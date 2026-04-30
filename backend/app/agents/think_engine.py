"""
Think Engine - 思考引擎
负责 LLM 调用与响应解析，支持流式和非流式两种调用路径、指数退避重试
"""
import time
import logging
from typing import Dict, Any, Optional, Generator
from dataclasses import dataclass, field
from app.agents.exceptions import ReActAgentError
from app.agents.error_handler import sanitize_error_message

logger = logging.getLogger(__name__)


@dataclass
class ThinkConfig:
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 4096
    enable_thinking: bool = False
    retry_count: int = 2
    retry_base_delay: float = 0.5
    retry_max_delay: float = 4.0


class ThinkEngine:

    def __init__(self, provider: str = "openai", config: ThinkConfig = None):
        from app.core.config import get_complete_config
        self.cfg = get_complete_config()
        self.provider = provider
        self.think_config = config or ThinkConfig()

    def think(
        self,
        prompt: str,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        同步思考（非流式）

        Returns:
            {"thought": str, "action": str|None, "action_input": dict|None,
             "is_final_answer": bool, "final_answer": str|None}
        """
        from app.agents.output_parser import OutputParser

        parser = OutputParser(mode="json")
        last_error = None

        for attempt in range(self.think_config.retry_count + 1):
            try:
                llm_output = self._call_llm_raw(prompt, stream=False)

                if not self._is_output_usable(llm_output):
                    raise ReActAgentError("LLM output too short or empty")

                return parser.parse(llm_output)

            except Exception as e:
                last_error = e
                if attempt < self.think_config.retry_count:
                    delay = min(
                        self.think_config.retry_base_delay * (2 ** attempt),
                        self.think_config.retry_max_delay
                    )
                    logger.warning(
                        f"[ThinkEngine] Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

        # 所有重试耗尽 → 返回结构化降级结果而非抛异常
        logger.error(
            f"[ThinkEngine] All {self.think_config.retry_count + 1} attempts exhausted. "
            f"Last error: {last_error}"
        )
        error_msg = sanitize_error_message(last_error) if last_error else "未知错误"
        return {
            "thought": f"LLM调用在{self.think_config.retry_count + 1}次重试后仍然失败。",
            "action": None,
            "action_input": None,
            "is_final_answer": True,
            "final_answer": f"抱歉，AI 推理服务暂时不可用（已重试{self.think_config.retry_count + 1}次）。请稍后再试或检查 LLM 服务配置。错误信息: {error_msg}"
        }

    def think_stream(
        self,
        prompt: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        流式思考 —— 边生成边 yield

        Yields:
            {"type": "thought_chunk", "content": "..."}
            {"type": "thought_complete", "parsed": {...}}
        """
        from app.agents.output_parser import OutputParser

        parser = OutputParser(mode="json")
        buffer = ""

        for chunk_text in self._call_llm_raw_stream(prompt):
            buffer += chunk_text
            yield {"type": "thought_chunk", "content": chunk_text}

        try:
            parsed = parser.parse(buffer)
            yield {"type": "thought_complete", "parsed": parsed}
        except Exception as e:
            logger.error(f"[ThinkEngine] Stream parse failed: {e}")
            yield {
                "type": "thought_error",
                "message": str(e),
                "raw_output": buffer[:500]
            }

    def _call_llm_raw(self, prompt: str, stream: bool = False) -> str:
        if self.provider == "ollama":
            return self._call_ollama(prompt)
        else:
            return self._call_openai(prompt)

    def _call_llm_raw_stream(self, prompt: str) -> Generator[str, None, None]:
        if self.provider == "ollama":
            yield from self._call_ollama_stream(prompt)
        else:
            yield from self._call_openai_stream(prompt)

    def _call_openai(self, prompt: str) -> str:
        from openai import OpenAI

        key = self.cfg.get("openai_api_key")
        base_url = self.cfg.get("openai_base_url")

        client_kwargs = {}
        if key:
            client_kwargs["api_key"] = key
        if base_url:
            client_kwargs["base_url"] = base_url
        client_kwargs["timeout"] = 60.0

        client = OpenAI(**client_kwargs)

        completion = client.chat.completions.create(
            model=self.cfg.get("openai_chat_model", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.think_config.max_tokens,
            temperature=self.think_config.temperature,
            top_p=self.think_config.top_p
        )

        if (completion.choices and completion.choices[0].message
                and completion.choices[0].message.content):
            return completion.choices[0].message.content.strip()
        raise ReActAgentError("LLM returned empty response")

    def _call_openai_stream(self, prompt: str) -> Generator[str, None, None]:
        from openai import OpenAI

        key = self.cfg.get("openai_api_key")
        base_url = self.cfg.get("openai_base_url")

        client_kwargs = {}
        if key:
            client_kwargs["api_key"] = key
        if base_url:
            client_kwargs["base_url"] = base_url
        client_kwargs["timeout"] = 60.0

        client = OpenAI(**client_kwargs)

        stream = client.chat.completions.create(
            model=self.cfg.get("openai_chat_model", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.think_config.max_tokens,
            temperature=self.think_config.temperature,
            top_p=self.think_config.top_p,
            stream=True
        )

        for chunk in stream:
            if (chunk.choices and chunk.choices[0].delta
                    and chunk.choices[0].delta.content):
                yield chunk.choices[0].delta.content

    def _call_ollama(self, prompt: str) -> str:
        try:
            from ollama import chat
            OLLAMA_SDK = True
        except ImportError:
            OLLAMA_SDK = False

        model = self.cfg.get("ollama_model")
        timeout = self.cfg.get("timeouts", {}).get("react_agent_subprocess", 60)

        if OLLAMA_SDK:
            response = chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    "temperature": self.think_config.temperature,
                    "top_p": self.think_config.top_p,
                    "num_predict": self.think_config.max_tokens
                },
                stream=False,
                think=self.think_config.enable_thinking
            )
            return response.message.content.strip()
        else:
            import requests
            endpoint = self.cfg.get("ollama_url").rstrip("/") + "/api/generate"
            r = requests.post(
                endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.think_config.temperature,
                        "top_p": self.think_config.top_p,
                        "num_predict": self.think_config.max_tokens
                    }
                },
                timeout=timeout
            )
            r.raise_for_status()
            return r.json().get("response", "")

    def _call_ollama_stream(self, prompt: str) -> Generator[str, None, None]:
        try:
            from ollama import chat
            OLLAMA_SDK = True
        except ImportError:
            OLLAMA_SDK = False

        model = self.cfg.get("ollama_model")

        if OLLAMA_SDK:
            stream = chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    "temperature": self.think_config.temperature,
                    "top_p": self.think_config.top_p,
                    "num_predict": self.think_config.max_tokens
                },
                stream=True,
                think=self.think_config.enable_thinking
            )
            for chunk in stream:
                content = getattr(chunk.message, 'content', None)
                if content:
                    yield content
        else:
            import requests
            import json
            endpoint = self.cfg.get("ollama_url").rstrip("/") + "/api/generate"
            timeout = self.cfg.get("timeouts", {}).get("requests_stream", 60)
            r = requests.post(
                endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": self.think_config.temperature,
                        "top_p": self.think_config.top_p,
                        "num_predict": self.think_config.max_tokens
                    }
                },
                stream=True,
                timeout=timeout
            )
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if data.get("response"):
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except Exception:
                        pass

    def _is_output_usable(self, output: str) -> bool:
        if not output or len(output.strip()) < 10:
            return False
        has_thought = '"thought"' in output or 'Thought:' in output
        has_answer = 'final_answer' in output or 'Final Answer' in output
        return has_thought or has_answer
