"""
Shared LLM Client — single source of truth for all LLM calls.

Automatically reads provider/model from llm_context when available,
falling back to global config.  Supports OpenAI, DeepSeek, and Ollama.
"""
import json
import logging
from typing import Dict, Generator, List, Optional, Any

from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 4096
    timeout: float = 60.0
    enable_thinking: bool = False
    reasoning_effort: str = "high"


class LLMClient:
    """Unified LLM client.

    Provider and model resolution order:
    1. Explicit `provider` / `model` kwarg passed to the method
    2. Context-var set by set_llm_context() at request entry
    3. Global config (openai_chat_model, ollama_model, etc.)
    """

    def __init__(
        self,
        provider: str = "",
        model: str = "",
        config: Optional[LLMConfig] = None,
    ):
        from app.core.config import get_complete_config
        self.cfg = get_complete_config()
        self._provider = provider
        self._model = model
        self.config = config or LLMConfig()
        self._openai_client: Any = None

    # ── Provider / model resolution ─────────────────────

    def _resolve_provider(self, explicit: str = "") -> str:
        if explicit:
            return explicit
        if self._provider:
            return self._provider
        from app.core.llm_context import get_llm_provider
        return get_llm_provider()

    def _resolve_model(self, explicit: str = "", thinking: bool = False) -> str:
        if explicit:
            return explicit
        if self._model:
            return self._model
        from app.core.llm_context import get_llm_model
        ctx_model = get_llm_model()
        if ctx_model:
            return ctx_model
        provider = self._resolve_provider()
        if provider == "deepseek":
            return (
                self.cfg.get("deepseek_reasoner_model", "deepseek-reasoner")
                if thinking
                else self.cfg.get("deepseek_chat_model", "deepseek-chat")
            )
        if provider == "ollama":
            return self.cfg.get("ollama_model", "")
        return self.cfg.get("openai_chat_model", "gpt-3.5-turbo")

    # ── Public API ──────────────────────────────────────

    def complete(
        self, prompt: str, system_prompt: str = "",
        provider: str = "", model: str = "",
    ) -> str:
        prov = self._resolve_provider(provider)
        if prov == "ollama":
            return self._complete_ollama(prompt, system_prompt)
        return self._complete_openai(prompt, system_prompt, model=model)

    def complete_json(
        self, prompt: str, system_prompt: str = "",
        provider: str = "", model: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Complete and parse the response as JSON."""
        prov = self._resolve_provider(provider)
        if prov == "ollama":
            text = self._complete_ollama(prompt, system_prompt)
        else:
            text = self._complete_openai(prompt, system_prompt, model=model)
        return self._parse_json(text)

    def chat(
        self, messages: List[Dict[str, str]],
        provider: str = "", model: str = "",
        **kwargs,
    ) -> str:
        prov = self._resolve_provider(provider)
        if prov == "ollama":
            return self._chat_ollama(messages)
        return self._chat_openai(messages, model=model, **kwargs)

    def chat_stream(
        self, messages: List[Dict[str, str]],
        provider: str = "", model: str = "",
        **kwargs,
    ) -> Generator[Dict[str, str], None, None]:
        prov = self._resolve_provider(provider)
        if prov == "ollama":
            yield from self._chat_stream_ollama(messages)
        else:
            yield from self._chat_stream_openai(messages, model=model, **kwargs)

    def complete_stream(
        self, prompt: str, system_prompt: str = "",
        provider: str = "",
    ) -> Generator[str, None, None]:
        prov = self._resolve_provider(provider)
        if prov == "ollama":
            yield from self._stream_ollama(prompt, system_prompt)
        else:
            yield from self._stream_openai(prompt, system_prompt)

    # ── OpenAI helpers ───────────────────────────────────

    def _ensure_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            kwargs: Dict[str, Any] = {"timeout": self.config.timeout}
            prov = self._resolve_provider()
            if prov == "deepseek":
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

    def _openai_kwargs(self, messages, model="", stream=False, **extra):
        resolved_model = self._resolve_model(explicit=model, thinking=self.config.enable_thinking)
        kwargs: Dict[str, Any] = dict(
            model=resolved_model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            stream=stream,
            **extra,
        )
        prov = self._resolve_provider()
        if prov == "deepseek":
            if self.config.enable_thinking:
                effort = self.config.reasoning_effort
                kwargs["reasoning_effort"] = (
                    "max" if effort in ("xhigh",)
                    else "high" if effort in ("low", "medium")
                    else effort
                )
                kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
            else:
                kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        elif prov != "ollama":
            kwargs.setdefault("temperature", self.config.temperature)
            kwargs.setdefault("top_p", self.config.top_p)
        return kwargs

    # ── OpenAI non-streaming ─────────────────────────────

    def _complete_openai(self, prompt, system_prompt, model=""):
        client = self._ensure_openai_client()
        messages = self._build_messages(prompt, system_prompt)
        completion = client.chat.completions.create(**self._openai_kwargs(messages, model=model))
        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
            return completion.choices[0].message.content.strip()
        return ""

    def _chat_openai(self, messages, model="", **kwargs):
        client = self._ensure_openai_client()
        completion = client.chat.completions.create(**self._openai_kwargs(messages, model=model, **kwargs))
        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
            return completion.choices[0].message.content.strip()
        return ""

    # ── OpenAI streaming ─────────────────────────────────

    def _stream_openai(self, prompt, system_prompt):
        client = self._ensure_openai_client()
        messages = self._build_messages(prompt, system_prompt)
        stream = client.chat.completions.create(**self._openai_kwargs(messages, stream=True))
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    yield {"type": "reasoning_chunk", "content": reasoning}
                if delta.content:
                    yield delta.content

    def _chat_stream_openai(self, messages, model="", **kwargs):
        client = self._ensure_openai_client()
        stream = client.chat.completions.create(**self._openai_kwargs(messages, model=model, stream=True, **kwargs))
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    yield {"type": "reasoning_chunk", "content": reasoning}
                if delta.content:
                    yield {"type": "content", "content": delta.content}

    # ── Ollama ───────────────────────────────────────────

    def _ollama_model(self):
        return self._resolve_model()

    def _build_messages(self, prompt, system_prompt):
        msgs: List[Dict[str, str]] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def _ollama_options(self):
        return {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "num_predict": self.config.max_tokens,
        }

    def _complete_ollama(self, prompt, system_prompt):
        try:
            from ollama import chat
            response = chat(
                model=self._ollama_model(),
                messages=self._build_messages(prompt, system_prompt),
                options=self._ollama_options(),
                stream=False,
            )
            return response.message.content.strip()
        except ImportError:
            return self._complete_ollama_http(prompt, system_prompt)

    def _chat_ollama(self, messages):
        try:
            from ollama import chat
            response = chat(
                model=self._ollama_model(),
                messages=messages,
                options=self._ollama_options(),
                stream=False,
            )
            return response.message.content.strip()
        except ImportError:
            prompt = messages[-1]["content"] if messages else ""
            return self._complete_ollama_http(prompt)

    def _stream_ollama(self, prompt, system_prompt):
        try:
            from ollama import chat
            stream = chat(
                model=self._ollama_model(),
                messages=self._build_messages(prompt, system_prompt),
                options=self._ollama_options(),
                stream=True,
            )
            for chunk in stream:
                content = getattr(chunk.message, "content", None)
                if content:
                    yield content
        except ImportError:
            yield from self._stream_ollama_http(prompt, system_prompt)

    def _chat_stream_ollama(self, messages):
        try:
            from ollama import chat
            stream = chat(
                model=self._ollama_model(),
                messages=messages,
                options=self._ollama_options(),
                stream=True,
            )
            for chunk in stream:
                content = getattr(chunk.message, "content", None)
                if content:
                    yield {"type": "content", "content": content}
        except ImportError:
            prompt = messages[-1]["content"] if messages else ""
            for text in self._stream_ollama_http(prompt):
                yield {"type": "content", "content": text}

    # ── Ollama HTTP fallback ────────────────────────────

    def _ollama_endpoint(self):
        return self.cfg.get("ollama_url", "").rstrip("/") + "/api/generate"

    def _complete_ollama_http(self, prompt, system_prompt=""):
        import requests
        full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        r = requests.post(
            self._ollama_endpoint(),
            json={"model": self._ollama_model(), "prompt": full, "stream": False,
                  "options": self._ollama_options()},
            timeout=self.cfg.get("timeouts", {}).get("react_agent_subprocess", 60),
        )
        r.raise_for_status()
        return r.json().get("response", "")

    def _stream_ollama_http(self, prompt, system_prompt=""):
        import requests
        full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        r = requests.post(
            self._ollama_endpoint(),
            json={"model": self._ollama_model(), "prompt": full, "stream": True,
                  "options": self._ollama_options()},
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

    # ── JSON helper ──────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> Optional[Dict[str, Any]]:
        return parse_json_response(text)


def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from LLM response text. Reusable utility."""
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def create_llm_client(
    provider: str = "", model: str = "", **kwargs,
) -> LLMClient:
    """Create an LLMClient.

    If provider/model are omitted, the client resolves them from
    llm_context → global config automatically.
    """
    config_keys = (
        "temperature", "top_p", "max_tokens", "timeout",
        "enable_thinking", "reasoning_effort",
    )
    config_kwargs = {k: kwargs.pop(k) for k in config_keys if k in kwargs}
    config = LLMConfig(**config_kwargs) if config_kwargs else LLMConfig()
    return LLMClient(provider=provider, model=model, config=config)
