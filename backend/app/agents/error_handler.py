"""
Error Handler - 错误分类与脱敏
对异常进行分类（可重试/不可重试），并过滤敏感信息
"""
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

SENSITIVE_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{20,}', 'sk-***'),
    (r'Bearer\s+[a-zA-Z0-9\-_\.]+', 'Bearer ***'),
    (r'api_key["\']?\s*[:=]\s*["\'][^"\']+["\']', 'api_key="***"'),
    (r'key=["\'][a-zA-Z0-9]{20,}["\']', 'key="***"'),
    (r'password["\']?\s*[:=]\s*["\'][^"\']+["\']', 'password="***"'),
    (r'token["\']?\s*[:=]\s*["\'][^"\']+["\']', 'token="***"'),
]


def sanitize_error_message(error: Exception) -> str:
    msg = str(error)
    for pattern, replacement in SENSITIVE_PATTERNS:
        msg = re.sub(pattern, replacement, msg)
    return msg


def classify_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """
    错误分类与建议

    Returns:
        {"category": str, "retryable": bool, "user_message": str, "log_message": str}
    """
    msg = str(error).lower()

    try:
        from openai import (
            APIError, APIConnectionError, RateLimitError, APITimeoutError
        )

        if isinstance(error, RateLimitError) or "rate limit" in msg:
            return {
                "category": "rate_limit",
                "retryable": True,
                "user_message": "服务繁忙，正在重试...",
                "log_message": sanitize_error_message(error)
            }
        elif isinstance(error, APITimeoutError) or "timeout" in msg:
            return {
                "category": "timeout",
                "retryable": True,
                "user_message": "响应超时，正在重试...",
                "log_message": sanitize_error_message(error)
            }
        elif isinstance(error, APIConnectionError) or "connection" in msg:
            return {
                "category": "connection",
                "retryable": True,
                "user_message": "网络连接异常，正在重试...",
                "log_message": sanitize_error_message(error)
            }
        elif isinstance(error, APIError):
            return {
                "category": "api_error",
                "retryable": False,
                "user_message": "服务暂时不可用，请稍后重试。",
                "log_message": sanitize_error_message(error)
            }
    except ImportError:
        pass

    if "rate limit" in msg:
        return {
            "category": "rate_limit",
            "retryable": True,
            "user_message": "服务繁忙，正在重试...",
            "log_message": sanitize_error_message(error)
        }
    elif "timeout" in msg:
        return {
            "category": "timeout",
            "retryable": True,
            "user_message": "响应超时，正在重试...",
            "log_message": sanitize_error_message(error)
        }
    elif "connection" in msg:
        return {
            "category": "connection",
            "retryable": True,
            "user_message": "网络连接异常，正在重试...",
            "log_message": sanitize_error_message(error)
        }
    elif "json" in msg or "parse" in msg:
        return {
            "category": "parse_error",
            "retryable": True,
            "user_message": "输出解析异常，正在重试...",
            "log_message": sanitize_error_message(error)
        }

    return {
        "category": "unknown",
        "retryable": False,
        "user_message": "执行过程中发生内部错误。",
        "log_message": sanitize_error_message(error)
    }
