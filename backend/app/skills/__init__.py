"""
Skills Package - Extensible skill system for the AI assistant

This package provides:
- Skill management and execution
- Skill selection via LLM
- Skill registry with versioning and permissions
- Parameter validation
- Progressive disclosure system (3-tier information loading)
- Package-based skill system
"""

from app.skills.skill_manager import SkillManager, get_skill_manager
from app.skills.registry import SkillRegistry, SkillDefinition
from app.skills.validator import ParameterValidator, ValidationError
from app.skills.permission import PermissionControl, PermissionRule, Role
from app.skills.versioning import VersionManager, SemVer, MigrationStep

__all__ = [
    # Manager
    "SkillManager",
    "get_skill_manager",
    # Registry
    "SkillRegistry",
    "SkillDefinition",
    # Validation
    "ParameterValidator",
    "ValidationError",
    # Permissions
    "PermissionControl",
    "PermissionRule",
    "Role",
    # Versioning
    "VersionManager",
    "SemVer",
    "MigrationStep",
]

__version__ = "5.0.0"
