"""
Skill Registry — Central skill registration and discovery.

Features:
- Skill registration with metadata
- Version tracking (semver)
- Enable/disable toggling
- Permission checking
- Package discovery from skills/ directory
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SkillDefinition:
    """Full skill definition."""
    name: str
    description: str
    version: str = "1.0.0"
    enabled: bool = True
    type: str = "package"
    permissions: List[str] = field(default_factory=list)
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "type": self.type,
            "permissions": self.permissions,
            "input_parameters": self.input_parameters,
        }


class SkillRegistry:
    """
    Central registry for all skills.

    Provides register, discover, enable/disable, and permission checking.
    """

    def __init__(self, skills_dir: Optional[Path] = None):
        self._skills: Dict[str, SkillDefinition] = {}
        self.skills_dir = skills_dir or self._default_skills_dir()
        logger.info(f"[SkillRegistry] Initialized with skills_dir={self.skills_dir}")

    @staticmethod
    def _default_skills_dir() -> Path:
        return Path(__file__).parent.parent.parent.parent / "skills"

    # ── Registration ────────────────────────────────────

    def register(self, skill_def: SkillDefinition) -> None:
        """Register a skill definition."""
        if skill_def.name in self._skills:
            logger.warning(f"[SkillRegistry] Overwriting existing skill: {skill_def.name}")
        self._skills[skill_def.name] = skill_def
        logger.info(f"[SkillRegistry] Registered: {skill_def.name} v{skill_def.version}")

    def unregister(self, name: str) -> None:
        """Remove a skill from the registry."""
        if name in self._skills:
            del self._skills[name]
            logger.info(f"[SkillRegistry] Unregistered: {name}")

    # ── Discovery ───────────────────────────────────────

    def discover(self) -> List[SkillDefinition]:
        """
        Discover skills from the skills/ directory.

        Each subdirectory is a skill package with:
        - _meta.json: owner, slug, version
        - SKILL.md: YAML frontmatter with name, description
        - skill_config.json: execution configuration
        """
        discovered = []
        if not self.skills_dir.exists():
            logger.warning(f"[SkillRegistry] Skills dir not found: {self.skills_dir}")
            return discovered

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            try:
                skill_def = self._load_skill_package(skill_dir)
                if skill_def:
                    self.register(skill_def)
                    discovered.append(skill_def)
            except Exception as e:
                logger.error(f"[SkillRegistry] Failed to load skill from {skill_dir}: {e}")

        logger.info(f"[SkillRegistry] Discovered {len(discovered)} skills")
        return discovered

    def _load_skill_package(self, skill_dir: Path) -> Optional[SkillDefinition]:
        """Load a single skill package from directory."""
        import json
        import yaml

        # Load _meta.json
        meta_path = skill_dir / "_meta.json"
        meta = {}
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))

        # Load SKILL.md frontmatter
        skill_md_path = skill_dir / "SKILL.md"
        name = skill_dir.name
        description = ""
        input_params = {}

        if skill_md_path.exists():
            content = skill_md_path.read_text(encoding="utf-8")
            fm = self._parse_yaml_frontmatter(content)
            name = fm.get("name", name)
            description = fm.get("description", "")
            input_params = fm.get("input_parameters", {})

        # Load skill_config.json
        config_path = skill_dir / "skill_config.json"
        config = {}
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))

        version = meta.get("version", "1.0.0")

        return SkillDefinition(
            name=name,
            description=description,
            version=version,
            enabled=True,
            type="package",
            permissions=meta.get("permissions", []),
            input_parameters=input_params,
            path=skill_dir,
        )

    @staticmethod
    def _parse_yaml_frontmatter(content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown content."""
        import yaml
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    return yaml.safe_load(parts[1]) or {}
                except Exception:
                    pass
        return {}

    # ── Query ───────────────────────────────────────────

    def get(self, name: str) -> Optional[SkillDefinition]:
        """Get a skill by name."""
        return self._skills.get(name)

    def list(self, enabled_only: bool = True) -> List[SkillDefinition]:
        """List all registered skills."""
        skills = list(self._skills.values())
        if enabled_only:
            skills = [s for s in skills if s.enabled]
        return skills

    def list_metadata(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """List skill metadata as dicts."""
        return [s.to_dict() for s in self.list(enabled_only=enabled_only)]

    # ── Lifecycle ───────────────────────────────────────

    def enable(self, name: str) -> bool:
        """Enable a skill."""
        skill = self._skills.get(name)
        if skill:
            skill.enabled = True
            logger.info(f"[SkillRegistry] Enabled: {name}")
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a skill."""
        skill = self._skills.get(name)
        if skill:
            skill.enabled = False
            logger.info(f"[SkillRegistry] Disabled: {name}")
            return True
        return False

    # ── Permissions ─────────────────────────────────────

    def check_permission(self, name: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if a skill can be executed in the given context.

        Args:
            name: Skill name
            context: Optional context dict (user role, etc.)

        Returns:
            True if the skill can be executed
        """
        skill = self._skills.get(name)
        if not skill:
            return False
        if not skill.enabled:
            return False
        if not skill.permissions:
            return True  # No restrictions

        ctx = context or {}
        user_role = ctx.get("user_role", "user")

        if "admin" in skill.permissions and user_role != "admin":
            logger.warning(f"[SkillRegistry] Permission denied for {name}: requires admin")
            return False

        return True

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills
