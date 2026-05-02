"""
LLM Context — contextvars-based propagation of the current request's
provider/model selection, so all downstream LLM calls use the same model
without needing to thread parameters through every function signature.
"""
import contextvars

_current_provider: contextvars.ContextVar[str] = contextvars.ContextVar(
    "llm_provider", default="openai"
)
_current_model: contextvars.ContextVar[str] = contextvars.ContextVar(
    "llm_model", default=""
)


def set_llm_context(provider: str, model: str = "") -> None:
    """Set the LLM provider/model for the current request context.

    Call once at the request entry point (e.g. routes.py /qa endpoint).
    All downstream LLM calls will use these values as defaults.
    """
    _current_provider.set(provider)
    if model:
        _current_model.set(model)


def get_llm_provider() -> str:
    """Return the current request's LLM provider (default: 'openai')."""
    return _current_provider.get()


def get_llm_model() -> str:
    """Return the current request's LLM model override, or empty string."""
    return _current_model.get()
