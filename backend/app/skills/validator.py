"""
Parameter Validator — Schema-based parameter validation and type coercion.

Features:
- JSON Schema-compatible validation
- Type coercion (string → int/float)
- Min/max bounds checking
- Required field checking
- Default value application
"""
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Parameter validation error."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field


class ParameterValidator:
    """
    Validate and coerce parameters against a JSON Schema-compatible schema.

    Schema format (subset of JSON Schema):
    {
        "param_name": {
            "type": "string" | "integer" | "number" | "boolean",
            "required": true/false,
            "default": <value>,
            "min": <number>,
            "max": <number>,
            "description": "..."
        }
    }
    """

    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema

    def validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and coerce parameters.

        Returns:
            Validated and coerced parameter dict.

        Raises:
            ValidationError on invalid params.
        """
        validated: Dict[str, Any] = {}

        for param_name, param_schema in self.schema.items():
            value = params.get(param_name)

            # Apply default
            if value is None and "default" in param_schema:
                value = param_schema["default"]

            # Check required
            if param_schema.get("required", False) and value is None:
                raise ValidationError(
                    f"Missing required parameter: {param_name}",
                    field=param_name,
                )

            if value is None:
                continue

            # Type coercion
            target_type = param_schema.get("type", "string")
            try:
                value = self._coerce(value, target_type)
            except (ValueError, TypeError) as e:
                raise ValidationError(
                    f"Type mismatch for '{param_name}': expected {target_type}, got {type(value).__name__}",
                    field=param_name,
                )

            # Bounds checking
            if target_type in ("integer", "number") and isinstance(value, (int, float)):
                if "min" in param_schema and value < param_schema["min"]:
                    value = param_schema["min"]
                    logger.debug(f"[Validator] Clamped '{param_name}' to min={value}")
                if "max" in param_schema and value > param_schema["max"]:
                    value = param_schema["max"]
                    logger.debug(f"[Validator] Clamped '{param_name}' to max={value}")

            validated[param_name] = value

        # Pass through any extra params not in schema
        for key, value in params.items():
            if key not in validated and value is not None:
                validated[key] = value

        return validated

    def _coerce(self, value: Any, target_type: str) -> Any:
        """Coerce a value to the target type."""
        if target_type == "string":
            return str(value)
        elif target_type == "integer":
            if isinstance(value, bool):
                return 1 if value else 0
            return int(float(value))
        elif target_type == "number":
            if isinstance(value, bool):
                return 1.0 if value else 0.0
            return float(value)
        elif target_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        return value

    def get_schema(self) -> Dict[str, Any]:
        """Return the schema as a dict."""
        return self.schema
