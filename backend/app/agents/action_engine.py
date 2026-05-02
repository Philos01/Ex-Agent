"""
Action Engine - 行动引擎
负责工具的校验、执行与结果处理，支持工具注册制、调用前参数校验、工具级重试
"""
import time
import logging
from typing import Dict, Any, Optional, List
from app.agents.exceptions import ToolNotFoundError, ToolExecutionError

logger = logging.getLogger(__name__)


class ActionEngine:

    MAX_TOOL_RETRIES = 1

    def __init__(self):
        from app.skills import get_skill_manager
        self.skill_manager = get_skill_manager()
        self._tool_schemas = {}

    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        retry_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        执行工具调用

        Returns:
            {
                "success": bool,
                "output": str,
                "error": str | None,
                "tool_name": str,
                "params_used": dict,
                "execution_time_ms": float
            }
        """
        available = self.skill_manager.list_skills()
        if tool_name not in [s["name"] for s in available]:
            raise ToolNotFoundError(tool_name)

        validated_params = self._validate_params(tool_name, params)

        last_error = None
        max_attempts = self.MAX_TOOL_RETRIES + 1 if retry_on_error else 1

        for attempt in range(max_attempts):
            try:
                start = time.time()
                raw_result = self.skill_manager.execute_skill(
                    tool_name, **validated_params
                )
                elapsed = (time.time() - start) * 1000

                formatted = self.skill_manager.format_skill_result(raw_result)

                return {
                    "success": raw_result.get("success", False),
                    "output": formatted,
                    "error": raw_result.get("error") if not raw_result.get("success") else None,
                    "tool_name": tool_name,
                    "params_used": validated_params,
                    "execution_time_ms": round(elapsed, 1)
                }

            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"[ActionEngine] Tool '{tool_name}' attempt {attempt + 1} "
                        f"failed: {e}. Retrying..."
                    )
                    time.sleep(0.5 * (2 ** attempt))
                else:
                    logger.error(
                        f"[ActionEngine] Tool '{tool_name}' failed after "
                        f"{max_attempts} attempts: {e}"
                    )

        return {
            "success": False,
            "output": f"[工具执行失败] {tool_name}: {str(last_error)}",
            "error": str(last_error),
            "tool_name": tool_name,
            "params_used": validated_params,
            "execution_time_ms": 0
        }

    def _validate_params(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and coerce parameters against the skill's declared input_parameters schema.
        No per-skill hardcoded defaults — defaults come from the schema only.
        """
        validated = params.copy() if isinstance(params, dict) else {}

        schema = self._get_tool_param_schema(tool_name)

        if not schema:
            return validated

        for param_name, param_schema in schema.items():
            if param_schema.get("required", False) and param_name not in validated:
                default = param_schema.get("default")
                if default is not None:
                    validated[param_name] = default
                else:
                    logger.warning(
                        f"[ActionEngine] Missing required param '{param_name}' "
                        f"for tool '{tool_name}'"
                    )

            if param_name in validated and "type" in param_schema:
                validated[param_name] = self._coerce_type(
                    validated[param_name],
                    param_schema["type"]
                )

            if param_name in validated and "max" in param_schema:
                if isinstance(validated[param_name], (int, float)):
                    validated[param_name] = min(
                        validated[param_name],
                        param_schema["max"]
                    )

            if param_name in validated and "min" in param_schema:
                if isinstance(validated[param_name], (int, float)):
                    validated[param_name] = max(
                        validated[param_name],
                        param_schema["min"]
                    )

        return validated

    def _get_tool_param_schema(self, tool_name: str) -> dict:
        if tool_name in self._tool_schemas:
            return self._tool_schemas[tool_name]

        try:
            metadata = self.skill_manager.get_skill_metadata(tool_name)
            if metadata and "input_parameters" in metadata:
                schema = metadata["input_parameters"]
                self._tool_schemas[tool_name] = schema
                return schema
        except Exception as e:
            logger.debug(f"[ActionEngine] Failed to get schema for {tool_name}: {e}")

        self._tool_schemas[tool_name] = {}
        return {}

    def _coerce_type(self, value: Any, target_type: str) -> Any:
        if target_type in ("integer", "number"):
            try:
                return int(value) if target_type == "integer" else float(value)
            except (ValueError, TypeError):
                return value
        elif target_type == "string":
            return str(value)
        return value

    def list_available_tools(self) -> List[str]:
        available = self.skill_manager.list_skills()
        return [s["name"] for s in available]
