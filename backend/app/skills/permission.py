"""
Permission Control — Role-based access control for skill execution.

Features:
- Role-based permission checking (user, admin)
- Resource-level permissions
- Rate limiting per skill
- Execution context validation
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"


@dataclass
class PermissionRule:
    """A single permission rule."""
    role: Role = Role.USER
    requires_auth: bool = False
    rate_limit_per_minute: int = 0  # 0 = unlimited
    allowed_params: List[str] = field(default_factory=list)  # empty = all allowed


class PermissionControl:
    """
    Role-based permission control for skill execution.

    Checks permissions before allowing skill execution.
    """

    def __init__(self):
        self._rules: Dict[str, List[PermissionRule]] = {}
        self._rate_counters: Dict[str, Dict[str, int]] = {}  # skill_name -> {timestamp_key -> count}

    def set_rules(self, skill_name: str, rules: List[PermissionRule]) -> None:
        """Set permission rules for a skill."""
        self._rules[skill_name] = rules

    def add_rule(self, skill_name: str, rule: PermissionRule) -> None:
        """Add a permission rule for a skill."""
        if skill_name not in self._rules:
            self._rules[skill_name] = []
        self._rules[skill_name].append(rule)

    def check(
        self,
        skill_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check if skill execution is allowed.

        Args:
            skill_name: Name of the skill to check
            context: Execution context with user info

        Returns:
            True if execution is allowed
        """
        ctx = context or {}
        rules = self._rules.get(skill_name, [])

        if not rules:
            return True  # No rules = no restrictions

        user_role = Role(ctx.get("user_role", "user"))
        is_authenticated = ctx.get("is_authenticated", False)

        for rule in rules:
            # Check role
            if rule.role == Role.ADMIN and user_role != Role.ADMIN:
                logger.warning(
                    f"[Permission] Skill '{skill_name}' requires admin role, got {user_role}"
                )
                return False

            # Check auth
            if rule.requires_auth and not is_authenticated:
                logger.warning(
                    f"[Permission] Skill '{skill_name}' requires authentication"
                )
                return False

            # Check rate limit
            if rule.rate_limit_per_minute > 0:
                if not self._check_rate_limit(skill_name, rule.rate_limit_per_minute):
                    logger.warning(
                        f"[Permission] Skill '{skill_name}' rate limit exceeded"
                    )
                    return False

        return True

    def _check_rate_limit(self, skill_name: str, limit: int) -> bool:
        """Simple minute-based rate limiting."""
        import time
        minute_key = str(int(time.time() / 60))

        if skill_name not in self._rate_counters:
            self._rate_counters[skill_name] = {}

        counters = self._rate_counters[skill_name]

        # Clean old keys
        for old_key in list(counters.keys()):
            if old_key != minute_key:
                del counters[old_key]

        current = counters.get(minute_key, 0)
        if current >= limit:
            return False

        counters[minute_key] = current + 1
        return True

    def reset_limits(self, skill_name: Optional[str] = None) -> None:
        """Reset rate limit counters."""
        if skill_name:
            self._rate_counters.pop(skill_name, None)
        else:
            self._rate_counters.clear()
