"""
Token Budget Manager - Token 预算管理器
估算文本 token 数，动态调整 scratchpad 中 observation 的截断长度
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class TokenBudgetManager:

    MODEL_CONTEXT_LIMITS = {
        "gpt-3.5-turbo": 4096,
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000,
        "deepseek-v3": 65536,
        "deepseek-chat": 65536,
        "deepseek-reasoner": 65536,
        "qwen2.5": 131072,
        "qwen3": 131072,
    }

    def __init__(self, max_tokens: int = 6000, model_name: str = ""):
        if model_name and model_name in self.MODEL_CONTEXT_LIMITS:
            model_limit = self.MODEL_CONTEXT_LIMITS[model_name]
            self.max_tokens = min(max_tokens, int(model_limit * 0.9))
        else:
            self.max_tokens = max_tokens

        self.system_prompt_tokens = 0

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本 token 数（快速估算，无需加载 tokenizer）

        规则:
        - 中文字符: ~0.5 token/char
        - 英文单词: ~0.75 token/word
        - 数字/符号: ~0.3 token/char（保守）
        """
        chinese_chars = len(re.findall(r'[一-鿿]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        other_chars = len(text) - chinese_chars - sum(len(w) for w in re.findall(r'[a-zA-Z]+', text))

        tokens = (
            chinese_chars * 0.5
            + english_words * 0.75
            + other_chars * 0.3
        )
        return int(tokens)

    def can_add(self, additional_text: str) -> bool:
        return self.estimate_tokens(additional_text) < self.remaining()

    def remaining(self) -> int:
        return self.max_tokens - self.system_prompt_tokens

    def recommended_observation_limit(self, iteration: int, max_iterations: int) -> int:
        remaining_iterations = max_iterations - iteration
        if remaining_iterations <= 0:
            return 500
        share = self.remaining() // max(remaining_iterations, 1)
        return max(200, int(share * 0.3))

    def set_system_prompt_tokens(self, text: str):
        self.system_prompt_tokens = self.estimate_tokens(text)
