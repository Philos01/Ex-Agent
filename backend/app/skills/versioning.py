"""
Version Manager — Semantic version tracking for skills.

Features:
- Semantic version parsing (major.minor.patch)
- Version comparison
- Migration support tracking
- Version history
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SemVer:
    """Semantic version (major.minor.patch)."""
    major: int = 1
    minor: int = 0
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "SemVer") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __le__(self, other: "SemVer") -> bool:
        return self < other or self == other

    @classmethod
    def parse(cls, version_str: str) -> "SemVer":
        """Parse a version string like '1.2.3'."""
        try:
            parts = version_str.strip().split(".")
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return cls(major=major, minor=minor, patch=patch)
        except (ValueError, IndexError):
            logger.warning(f"[Versioning] Failed to parse version: {version_str}")
            return cls()


@dataclass
class MigrationStep:
    """A single migration step between versions."""
    from_version: SemVer
    to_version: SemVer
    description: str
    config_changes: Dict[str, Any] = None

    def __post_init__(self):
        if self.config_changes is None:
            self.config_changes = {}


class VersionManager:
    """
    Tracks skill versions and migrations.

    Each skill can have a version history and migration steps
    between versions.
    """

    def __init__(self):
        self._versions: Dict[str, SemVer] = {}
        self._history: Dict[str, List[SemVer]] = {}
        self._migrations: Dict[str, List[MigrationStep]] = {}

    def set_version(self, skill_name: str, version: str) -> SemVer:
        """Set the current version for a skill."""
        sv = SemVer.parse(version)
        old = self._versions.get(skill_name)

        if skill_name not in self._history:
            self._history[skill_name] = []
        self._history[skill_name].append(sv)

        self._versions[skill_name] = sv

        if old and old != sv:
            logger.info(
                f"[Versioning] {skill_name}: {old} → {sv}"
            )

        return sv

    def get_version(self, skill_name: str) -> SemVer:
        """Get the current version of a skill."""
        return self._versions.get(skill_name, SemVer())

    def get_history(self, skill_name: str) -> List[SemVer]:
        """Get version history for a skill."""
        return self._history.get(skill_name, [])

    def add_migration(
        self,
        skill_name: str,
        from_version: str,
        to_version: str,
        description: str,
        config_changes: Dict[str, Any] = None,
    ) -> None:
        """Register a migration step."""
        if skill_name not in self._migrations:
            self._migrations[skill_name] = []

        self._migrations[skill_name].append(
            MigrationStep(
                from_version=SemVer.parse(from_version),
                to_version=SemVer.parse(to_version),
                description=description,
                config_changes=config_changes or {},
            )
        )

    def get_migration_path(
        self, skill_name: str, from_version: str, to_version: str
    ) -> List[MigrationStep]:
        """Get the migration steps between two versions."""
        fv = SemVer.parse(from_version)
        tv = SemVer.parse(to_version)
        migrations = self._migrations.get(skill_name, [])

        return [
            m for m in migrations
            if m.from_version >= fv and m.to_version <= tv
        ]

    def needs_migration(self, skill_name: str, current_version: str) -> bool:
        """Check if a skill needs migration."""
        cv = SemVer.parse(current_version)
        latest = self._versions.get(skill_name)
        if latest is None:
            return False
        return cv < latest

    def check_compatibility(
        self, skill_name: str, required_version: str
    ) -> Tuple[bool, str]:
        """
        Check if the current version is compatible with a required version.

        Returns:
            (is_compatible, message)
        """
        current = self._versions.get(skill_name)
        required = SemVer.parse(required_version)

        if current is None:
            return False, f"Skill '{skill_name}' is not registered"

        if current.major != required.major:
            return False, (
                f"Major version mismatch for '{skill_name}': "
                f"required {required}, current {current}"
            )

        if current < required:
            return False, (
                f"Version too old for '{skill_name}': "
                f"required {required}, current {current}"
            )

        return True, f"Compatible: {current} >= {required}"
