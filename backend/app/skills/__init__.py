
"""
Skills Package - Extensible skill system for the AI assistant

This package provides:
- BaseSkill: Abstract base class for all skills
- Skill discovery and auto-loading
- Skill management and execution
- Progressive disclosure system (3-tier information loading)
- Configuration management
- Unified SkillManager: Combines both legacy and package-based skill systems
"""

from app.skills.base import BaseSkill
from app.skills.discovery import skill, SkillDiscoverer, get_skill_discoverer, discover_skills
from app.skills.skill_manager import SkillManager, get_skill_manager

# Backward compatibility aliases
NewSkillManager = SkillManager
get_new_skill_manager = get_skill_manager

__all__ = [
    "BaseSkill",
    "skill",
    "SkillDiscoverer",
    "get_skill_discoverer",
    "discover_skills",
    "SkillManager",
    "get_skill_manager",
    "NewSkillManager",
    "get_new_skill_manager"
]

__version__ = "4.0.0"

