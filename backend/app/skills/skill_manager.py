
"""
Skill Manager - Package-based skill manager
Manages skill discovery, selection, execution, and result formatting
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from app.skills.skill_selector import SkillSelector
from app.skills.skill_executor import SkillExecutor
from app.core.config import load_config

logger = logging.getLogger(__name__)


class SkillManager:
    """
    Package-based Skill Manager

    Features:
    - Automatic skill discovery from packages
    - LLM-based skill matching with configurable provider
    - Support executing .sh and .py skill files
    - Configuration management
    - Skill execution and result formatting
    """

    def __init__(self, auto_discover: bool = True):
        self.cfg = load_config()

        self.project_root = Path(__file__).parent.parent.parent.parent
        self.skills_dir = self.project_root / "skills"

        logger.info("[SkillManager] Skills directory: {}".format(self.skills_dir))

        self.skill_selector = SkillSelector(self.skills_dir)

        skills_cfg = self.cfg.get("skills", {})
        self.enabled = skills_cfg.get("enabled", True)

        if auto_discover:
            available = self.skill_selector.get_available_skills()
            logger.info("[SkillManager] Found {} package skills".format(len(available)))

        logger.info("[SkillManager] Initialization complete")

    def list_skills(self) -> List[Dict[str, Any]]:
        """List all available skills"""
        skills = []
        for metadata in self.skill_selector.get_available_skills():
            skills.append({
                "name": metadata["name"],
                "description": metadata["description"],
                "type": "package"
            })
        return skills

    def get_skill_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get skill metadata"""
        skill_dir = self.skill_selector.get_skill_dir(name)
        if skill_dir:
            from app.skills.metadata_parser import get_skill_metadata
            return get_skill_metadata(skill_dir)
        return None

    def get_skill_instructions(self, name: str) -> Optional[str]:
        """Get skill instructions from SKILL.md"""
        skill_dir = self.skill_selector.get_skill_dir(name)
        if skill_dir:
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    return skill_md.read_text(encoding="utf-8")
                except Exception as e:
                    logger.warning(f"[SkillManager] Failed to read SKILL.md for {name}: {e}")
        return None

    def get_skill_resources(self, name: str) -> List[str]:
        """List skill resource files"""
        skill_dir = self.skill_selector.get_skill_dir(name)
        if skill_dir:
            resources = []
            refs_dir = skill_dir / "references"
            if refs_dir.exists():
                for f in refs_dir.iterdir():
                    if f.is_file():
                        resources.append(str(f.relative_to(skill_dir)))
            return resources
        return []

    def get_skill_resource(self, skill_name: str, resource_path: str) -> Optional[str]:
        """Read a specific skill resource file"""
        skill_dir = self.skill_selector.get_skill_dir(skill_name)
        if skill_dir:
            full_path = skill_dir / resource_path
            if full_path.exists() and full_path.is_file():
                try:
                    return full_path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.warning(f"[SkillManager] Failed to read resource {resource_path}: {e}")
        return None

    def should_use_skill(
        self,
        question: str,
        provider: str = "openai",
        conversation_history: str = "",
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Determine if a skill should be used for the given question.

        Args:
            question: User question
            provider: LLM provider
            conversation_history: Optional recent conversation context

        Returns:
            Tuple of (should_use, skill_name, params)
        """
        if not self.enabled:
            return False, None, None

        return self.skill_selector.select_skill_with_llm(
            question,
            provider=provider,
            conversation_history=conversation_history,
        )

    def execute_skill(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a skill. Parameters are passed through directly —
        the LLM extracts them according to the skill's input_parameters schema.

        Returns:
            Execution result dictionary
        """
        logger.info("[SkillManager] Executing skill: %s, params: %s", skill_name, kwargs)

        skill_dir = self.skill_selector.get_skill_dir(skill_name)
        if skill_dir:
            logger.info("[SkillManager] Executing package skill: %s", skill_name)
            executor = SkillExecutor(skill_dir)
            result = executor.execute(kwargs)
            logger.info("[SkillManager] Package skill result: success=%s", result.get("success", False))
            return result

        return {
            "success": False,
            "error": "Skill not found: {}".format(skill_name)
        }

    def format_skill_result(self, result: Dict[str, Any]) -> str:
        """
        Format skill result for LLM consumption.

        Returns:
            Formatted string
        """
        if not result.get("success"):
            return "Skill execution failed: {}".format(result.get("error", "Unknown error"))

        if "output" in result:
            return result["output"]

        data = result.get("data", result)

        papers = data.get("papers", []) if isinstance(data, dict) else []
        if papers:
            formatted = "## Search Results ({} papers)\n\n".format(len(papers))
            for i, paper in enumerate(papers, 1):
                formatted += "### Paper {}: {}\n".format(i, paper["title"])
                formatted += "- **Authors**: {}\n".format(", ".join(paper["authors"]))
                formatted += "- **Published**: {}\n".format(paper["published"])
                formatted += "- **Categories**: {}\n".format(", ".join(paper["categories"]))
                formatted += "- **Abstract**: {}...\n".format(paper["summary"][:300])
                formatted += "- **PDF Link**: {}\n".format(paper["pdf_url"])
                formatted += "- **Details Link**: {}\n\n".format(paper["abs_url"])
            return formatted

        if "data" in result:
            return str(result["data"])

        return str(result)


# Global singleton
_skill_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """Get the unified skill manager singleton"""
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager
