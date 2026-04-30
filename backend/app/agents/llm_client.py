"""
Shared LLM Client Factory — single source of truth for OpenAI/Ollama calls.
"""
import logging
from typing import Generator, Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 4096
    timeout: float = 60.0
    enable_thinking: bool = False


class LLMClient:
    """Unified LLM client with cached connections."""

    def __init__(self, provider: str = "openai", config: Optional[LLMConfig] = None):
        from app.core.config import get_complete_config
        self.cfg = get_complete_config()
        self.provider = provider
        self.config = config or LLMConfig()
        self._openai_client: Any = None

    # ── Public API ──────────────────────────────────────

    def complete(self, prompt: str, system_prompt: str = "") -> str:
        if self.provider == "ollama":
            return self._complete_ollama(prompt, system_prompt)
        return self._complete_openai(prompt, system_prompt)

    def complete_stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        if self.provider == "ollama":
            yield from self._stream_ollama(prompt, system_prompt)
        else:
            yield from self._stream_openai(prompt, system_prompt)

    # ── OpenAI ──────────────────────────────────────────

    def _ensure_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            kwargs: Dict[str, Any] = {"timeout": self.config.timeout}
            if self.provider == "deepseek":
                kwargs["base_url"] = self.cfg.get("deepseek_base_url", "https://api.deepseek.com/v1")
                key = self.cfg.get("deepseek_api_key")
            else:
                key = self.cfg.get("openai_api_key")
                base_url = self.cfg.get("openai_base_url")
                if base_url:
                    kwargs["base_url"] = base_url
            if key:
                kwargs["api_key"] = key
            self._openai_client = OpenAI(**kwargs)
        return self._openai_client

    def _build_openai_messages(self, prompt: str, system_prompt: str) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _openai_chat_kwargs(self, messages: List[Dict], **extra) -> Dict[str, Any]:
        if self.provider == "deepseek":
            model = (self.cfg.get("deepseek_reasoner_model", "deepseek-reasoner")
                     if self.config.enable_thinking
                     else self.cfg.get("deepseek_chat_model", "deepseek-chat"))
        else:
            model = self.cfg.get("openai_chat_model", "gpt-3.5-turbo")
        kwargs: Dict[str, Any] = dict(
            model=model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            **extra,
        )
        # deepseek-reasoner does not support temperature/top_p
        if not (self.provider == "deepseek" and self.config.enable_thinking):
            kwargs["temperature"] = self.config.temperature
            kwargs["top_p"] = self.config.top_p
        return kwargs

    def _complete_openai(self, prompt: str, system_prompt: str = "") -> str:
        client = self._ensure_openai_client()
        messages = self._build_openai_messages(prompt, system_prompt)
        completion = client.chat.completions.create(**self._openai_chat_kwargs(messages))
        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
            return completion.choices[0].message.content.strip()
        return ""

    def _stream_openai(self, prompt: str, system_prompt: str = "") -> Generator[Dict[str, str], None, None]:
        client = self._ensure_openai_client()
        messages = self._build_openai_messages(prompt, system_prompt)
        stream = client.chat.completions.create(**self._openai_chat_kwargs(messages, stream=True))
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, 'reasoning_content', None)
                if reasoning:
                    yield {"type": "reasoning_chunk", "content": reasoning}
                if delta.content:
                    yield {"type": "content", "content": delta.content}

    # ── Ollama ──────────────────────────────────────────

    def _build_ollama_messages(self, prompt: str, system_prompt: str) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _ollama_options(self) -> Dict[str, Any]:
        return {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "num_predict": self.config.max_tokens,
        }

    def _complete_ollama(self, prompt: str, system_prompt: str = "") -> str:
        try:
            from ollama import chat
            response = chat(
                model=self.cfg.get("ollama_model"),
                messages=self._build_ollama_messages(prompt, system_prompt),
                options=self._ollama_options(),
                stream=False,
            )
            return response.message.content.strip()
        except ImportError:
            return self._complete_ollama_http(prompt, system_prompt)

    def _stream_ollama(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        try:
            from ollama import chat
            stream = chat(
                model=self.cfg.get("ollama_model"),
                messages=self._build_ollama_messages(prompt, system_prompt),
                options=self._ollama_options(),
                stream=True,
            )
            for chunk in stream:
                content = getattr(chunk.message, "content", None)
                if content:
                    yield content
        except ImportError:
            yield from self._stream_ollama_http(prompt, system_prompt)

    # ── Ollama HTTP fallback ────────────────────────────

    def _ollama_full_prompt(self, prompt: str, system_prompt: str) -> str:
        return f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

    def _ollama_http_endpoint(self) -> str:
        return self.cfg.get("ollama_url").rstrip("/") + "/api/generate"

    def _complete_ollama_http(self, prompt: str, system_prompt: str = "") -> str:
        import requests
        r = requests.post(
            self._ollama_http_endpoint(),
            json={
                "model": self.cfg.get("ollama_model"),
                "prompt": self._ollama_full_prompt(prompt, system_prompt),
                "stream": False,
                "options": self._ollama_options(),
            },
            timeout=self.cfg.get("timeouts", {}).get("react_agent_subprocess", 60),
        )
        r.raise_for_status()
        return r.json().get("response", "")

    def _stream_ollama_http(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        import requests
        import json
        r = requests.post(
            self._ollama_http_endpoint(),
            json={
                "model": self.cfg.get("ollama_model"),
                "prompt": self._ollama_full_prompt(prompt, system_prompt),
                "stream": True,
                "options": self._ollama_options(),
            },
            stream=True,
            timeout=self.cfg.get("timeouts", {}).get("requests_stream", 60),
        )
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if data.get("response"):
                        yield data["response"]
                    if data.get("done", False):
                        break
                except Exception:
                    pass


def create_llm_client(provider: str = "openai", **kwargs) -> LLMClient:
    config_keys = ("temperature", "top_p", "max_tokens", "timeout", "enable_thinking")
    config_kwargs = {k: kwargs.pop(k) for k in config_keys if k in kwargs}
    config = LLMConfig(**config_kwargs) if config_kwargs else LLMConfig()
    return LLMClient(provider=provider, config=config)
