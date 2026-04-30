"""
Memory & Scratchpad - 记忆与暂存器管理
增强版：区分 raw/compressed observation，支持自动压缩
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MemoryScratchpad:
    """
    Agent 暂存器 - 存储当前任务的"思考-行动-观察"链

    增强功能:
    - 区分 raw_observation（原始，给前端展示）和 observation（压缩，给 LLM）
    - 支持自动压缩（根据 token 预算）
    - 最早的步骤做额外截断
    """

    def __init__(self, max_raw_chars: int = 8000):
        self._steps: List[Dict[str, Any]] = []
        self.max_raw_chars = max_raw_chars
        logger.debug("[MemoryScratchpad] Initialized")

    def add_step(
        self,
        thought: str,
        action: Optional[str] = None,
        action_input: Optional[Dict[str, Any]] = None,
        observation: Optional[str] = None,
        raw_observation: Optional[str] = None
    ) -> None:
        step = {
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation,
            "raw_observation": raw_observation if raw_observation is not None else observation,
        }
        self._steps.append(step)
        logger.debug(f"[MemoryScratchpad] Added step: thought={thought[:50]}...")

    def compress_history(self, compressor) -> None:
        for step in self._steps:
            if step.get("observation") and step.get("action"):
                step["observation"] = compressor(
                    step["observation"],
                    tool_name=step["action"]
                )
                logger.debug(
                    f"[MemoryScratchpad] Compressed observation "
                    f"for action '{step['action']}'"
                )

    def get_total_chars(self) -> int:
        return sum(len(str(s.get("observation", ""))) for s in self._steps)

    def get_scratchpad_text(self) -> str:
        if not self._steps:
            return ""

        lines = []
        for i, step in enumerate(self._steps, 1):
            lines.append(f"Thought: {step['thought']}")

            if step.get("action"):
                lines.append(f"Action: {step['action']}")

            if step.get("action_input"):
                import json
                lines.append(f"Action Input: {json.dumps(step['action_input'], ensure_ascii=False)}")

            if step.get("observation"):
                obs = step["observation"]
                if i < len(self._steps):
                    max_obs = 300
                    if len(obs) > max_obs:
                        obs = obs[:max_obs] + "..."
                lines.append(f"Observation: {obs}")

            if i < len(self._steps):
                lines.append("---")

        scratchpad_text = "\n".join(lines)
        logger.debug(f"[MemoryScratchpad] Scratchpad text generated ({len(scratchpad_text)} chars)")
        return scratchpad_text

    def get_steps(self) -> List[Dict[str, Any]]:
        return self._steps.copy()

    def clear(self) -> None:
        self._steps = []
        logger.debug("[MemoryScratchpad] Cleared")

    def __len__(self) -> int:
        return len(self._steps)

    def __str__(self) -> str:
        return self.get_scratchpad_text()
