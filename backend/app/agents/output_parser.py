"""
Output Parser - 结构化输出解析器
支持 JSON 和文本两种模式，增强对混合文本+JSON输出的提取能力
"""
import logging
import json
import re
from typing import Dict, Any, Optional
from app.agents.exceptions import OutputParseError

logger = logging.getLogger(__name__)

_INVALID_LITERALS = frozenset({"None", "null", "none"})


def _is_invalid_final_answer(val) -> bool:
    """Check if a final_answer value should be treated as None."""
    if val is None:
        return True
    if isinstance(val, str):
        stripped = val.strip()
        return not stripped or stripped in _INVALID_LITERALS or stripped in ("[]", "{}")
    return False


class OutputParser:
    """
    LLM 输出解析器

    支持两种模式:
    - JSON 模式（推荐）: 解析 JSON 格式的输出
    - 文本模式: 使用正则表达式解析文本格式

    增强功能:
    - 支持 ```json``` 代码块
    - 支持裸 JSON
    - 支持混合文本+JSON（LLM 在 JSON 前后附带解释文本）
    - 支持不完整 JSON 的容错修复
    """

    def __init__(self, mode: str = "json"):
        self.mode = mode.lower()
        if self.mode not in ["json", "text"]:
            self.mode = "json"
        logger.debug(f"[OutputParser] Initialized with mode: {self.mode}")

    def parse(self, text: str) -> Dict[str, Any]:
        logger.debug(f"[OutputParser] Parsing output (mode={self.mode}): {text[:100]}...")

        if self.mode == "json":
            try:
                return self._parse_json(text)
            except OutputParseError:
                logger.warning("[OutputParser] JSON parse failed, falling back to text mode")
                return self._parse_text(text)
        else:
            return self._parse_text(text)

    def _parse_json(self, text: str) -> Dict[str, Any]:
        json_str = self._extract_json_string(text)

        if json_str:
            try:
                result = json.loads(json_str)
                return self._normalize_result(result)
            except json.JSONDecodeError as e:
                logger.warning(f"[OutputParser] JSON decode failed, attempting repair: {e}")
                repaired = self._try_repair_json(json_str)
                if repaired:
                    try:
                        result = json.loads(repaired)
                        return self._normalize_result(result)
                    except json.JSONDecodeError:
                        pass

        try:
            result = json.loads(text.strip())
            return self._normalize_result(result)
        except json.JSONDecodeError:
            pass

        raise OutputParseError(f"Failed to parse JSON from output", raw_output=text)

    def _extract_json_string(self, text: str) -> Optional[str]:
        """
        从文本中提取 JSON 字符串，支持多种格式:
        1. ```json ... ``` 代码块
        2. ``` ... ``` 代码块（无语言标记）
        3. 混合文本中嵌入的 { ... } JSON 对象
        """
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            return json_match.group(1).strip()

        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            return brace_match.group(0)

        return None

    def _try_repair_json(self, json_str: str) -> Optional[str]:
        repaired = json_str.strip()
        repaired = self._backtrack_unclosed_string(repaired)
        repaired = self._backtrack_incomplete_tail(repaired)
        repaired = self._close_unclosed_strings(repaired)
        repaired = self._close_brackets_in_order(repaired)
        repaired = re.sub(r',\s*([}\]])', r'\1', repaired)
        repaired = re.sub(r'(\w+)\s*:', r'"\1":', repaired)
        repaired = repaired.replace('""', '"')
        return repaired if repaired != json_str.strip() else None

    def _close_brackets_in_order(self, text: str) -> str:
        bracket_stack = []
        for ch in text:
            if ch == '{':
                bracket_stack.append('}')
            elif ch == '[':
                bracket_stack.append(']')
            elif ch == '}':
                if bracket_stack and bracket_stack[-1] == '}':
                    bracket_stack.pop()
            elif ch == ']':
                if bracket_stack and bracket_stack[-1] == ']':
                    bracket_stack.pop()
        return text + ''.join(reversed(bracket_stack))

    def _backtrack_unclosed_string(self, text: str) -> str:
        """如果 JSON 末尾截断在字符串中间，回退到上一个安全边界"""
        in_string = False
        escape_next = False
        last_safe = len(text)

        for i, ch in enumerate(text):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                if not in_string:
                    last_safe = i + 1

        if in_string:
            return text[:last_safe]
        return text

    def _backtrack_incomplete_tail(self, text: str) -> str:
        text = text.rstrip()
        changed = True
        while changed:
            changed = False
            if text.endswith(','):
                text = text[:-1].rstrip()
                changed = True
                continue

            m = re.search(r'"[^"]*"\s*:\s*$', text)
            if m:
                cut_pos = m.start()
                prev = text[:cut_pos].rstrip()
                if prev.endswith(','):
                    text = prev[:-1].rstrip()
                else:
                    last_boundary = max(prev.rfind(','), prev.rfind('{'), prev.rfind('['))
                    if last_boundary >= 0:
                        text = prev[:last_boundary + 1].rstrip() if prev[last_boundary] == ',' else prev[:last_boundary].rstrip()
                    else:
                        text = prev
                changed = True
                continue

            last_struct = max(text.rfind(','), text.rfind('{'), text.rfind('['))
            if last_struct >= 0:
                tail = text[last_struct + 1:].strip()
                if re.match(r'^"[^"]*"$', tail):
                    text = text[:last_struct + 1].rstrip() if text[last_struct] == ',' else text[:last_struct].rstrip()
                    changed = True
                    continue

        return text.rstrip()

    def _close_unclosed_strings(self, text: str) -> str:
        """关闭未闭合的 JSON 字符串"""
        in_string = False
        escape_next = False
        result = []
        for ch in text:
            if escape_next:
                result.append(ch)
                escape_next = False
                continue
            if ch == '\\':
                result.append(ch)
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
            result.append(ch)
        if in_string:
            result.append('"')
        return ''.join(result)

    def _parse_text(self, text: str) -> Dict[str, Any]:
        result = {
            "thought": "",
            "action": None,
            "action_input": None,
            "is_final_answer": False,
            "final_answer": None
        }

        thought_match = re.search(r'Thought:\s*(.*?)(?=\n\w+:|$)', text, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        final_answer_match = re.search(r'Final Answer:\s*(.*)', text, re.DOTALL)
        if final_answer_match:
            raw_fa = final_answer_match.group(1).strip()
            if raw_fa and raw_fa not in _INVALID_LITERALS:
                result["is_final_answer"] = True
                result["final_answer"] = raw_fa
            else:
                logger.warning(f"[OutputParser] Text mode captured invalid Final Answer: '{raw_fa}', ignoring")
                result["is_final_answer"] = False
                result["final_answer"] = None
            return result

        action_match = re.search(r'Action:\s*(.*?)(?=\n|$)', text)
        if action_match:
            action = action_match.group(1).strip()
            if action.lower() not in _INVALID_LITERALS:
                result["action"] = action

        action_input_match = re.search(r'Action Input:\s*(.*?)(?=\n\w+:|$)', text, re.DOTALL)
        if action_input_match:
            input_str = action_input_match.group(1).strip()
            try:
                result["action_input"] = json.loads(input_str)
            except json.JSONDecodeError:
                result["action_input"] = input_str

        if not result["thought"] and not result["is_final_answer"]:
            result["thought"] = text.strip()

        return result

    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        final_answer = result.get("final_answer")

        if _is_invalid_final_answer(final_answer):
            final_answer = None

        if final_answer is not None and not isinstance(final_answer, str):
            original_type = type(final_answer).__name__
            try:
                final_answer = json.dumps(final_answer, ensure_ascii=False, indent=2)
                if _is_invalid_final_answer(final_answer):
                    final_answer = None
                    logger.info(f"[OutputParser] Converted {original_type} final_answer to empty JSON string, treating as None")
                else:
                    logger.info(f"[OutputParser] Converted non-string final_answer (type={original_type}) to JSON string")
            except (TypeError, ValueError) as e:
                logger.warning(f"[OutputParser] Failed to convert final_answer to string: {e}")
                final_answer = str(final_answer)

        is_final_answer = bool(result.get("is_final_answer", False))

        if is_final_answer and final_answer is None:
            logger.warning("[OutputParser] is_final_answer=True but final_answer invalid, forcing is_final_answer=False")
            is_final_answer = False

        normalized = {
            "thought": result.get("thought", ""),
            "action": result.get("action"),
            "action_input": result.get("action_input"),
            "is_final_answer": is_final_answer,
            "final_answer": final_answer,
        }

        if normalized["action"] is None or str(normalized["action"]).lower() in ("null", "none"):
            normalized["action"] = None

        if normalized["action_input"] is not None and str(normalized["action_input"]).lower() in ("null", "none"):
            normalized["action_input"] = None

        if normalized["action_input"] and isinstance(normalized["action_input"], str):
            try:
                normalized["action_input"] = json.loads(normalized["action_input"])
            except (json.JSONDecodeError, TypeError):
                pass

        logger.debug(f"[OutputParser] Normalized: is_final={normalized['is_final_answer']}, "
                     f"action={normalized['action']}, fa_len={len(str(normalized['final_answer'])) if normalized['final_answer'] else 0}")
        return normalized
