
"""
Skill Manager - Unified skill manager
Combines legacy and new skill package systems
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from app.skills.base import BaseSkill
from app.skills.discovery import get_skill_discoverer
from app.skills.skill_selector import SkillSelector
from app.skills.skill_executor import SkillExecutor
from app.core.config import load_config

logger = logging.getLogger(__name__)


class SkillManager:
    """
    Unified Skill Manager - combines both legacy and new package systems
    
    Features:
    - Automatic skill discovery (both legacy and package)
    - LLM-based skill matching with configurable provider
    - Support executing .sh and .py skill files
    - Backward compatible with old BaseSkill system
    - Configuration management
    - Skill execution and result formatting
    """
    
    def __init__(self, auto_discover=True):
        self.cfg = load_config()
        
        # Set skills directory
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.skills_dir = self.project_root / "skills"
        
        logger.info("[SkillManager] Skills directory: {}".format(self.skills_dir))
        
        # Initialize skill selector
        self.skill_selector = SkillSelector(self.skills_dir)
        
        # Legacy system initialization
        self._skills = {}
        self._skill_classes = {}
        skills_cfg = self.cfg.get("skills", {})
        self.enabled = skills_cfg.get("enabled", True)
        
        if auto_discover:
            self._discover_and_load_skills()
        
        logger.info("[SkillManager] Initialization complete")
    
    def _discover_and_load_skills(self):
        """Discover and load both legacy and new package skills"""
        logger.info("[SkillManager] Starting skill discovery and loading")
        
        # Load legacy skills
        try:
            discoverer = get_skill_discoverer()
            self._skill_classes = discoverer.get_skill_classes()
            for name, skill_cls in self._skill_classes.items():
                try:
                    self._load_legacy_skill(name, skill_cls)
                except Exception as e:
                    logger.error(f"[SkillManager] Failed to load legacy skill '{name}': {e}", exc_info=True)
            logger.info(f"[SkillManager] Loaded {len(self._skills)} legacy skills")
        except Exception as e:
            logger.warning(f"[SkillManager] Legacy skill discovery failed: {e}")
        
        # New package skills are loaded by skill_selector
        available_packages = self.skill_selector.get_available_skills()
        logger.info(f"[SkillManager] Found {len(available_packages)} package skills")
    
    def _load_legacy_skill(self, name, skill_cls):
        """Load a single legacy skill"""
        skill_enabled = True
        try:
            skills_config = self.cfg.get("skills", {})
            skill_config = skills_config.get(name, {})
            skill_enabled = skill_config.get("enabled", True)
        except Exception:
            pass
        
        if not skill_enabled:
            logger.info(f"[SkillManager] Skipping disabled legacy skill: {name}")
            return
        
        skill = skill_cls()
        self._skills[name] = skill
        logger.info(f"[SkillManager] Loaded legacy skill: {name}")
    
    def register_skill(self, skill):
        """Manually register a legacy skill"""
        self._skills[skill.name] = skill
        logger.info(f"[SkillManager] Manually registered skill: {skill.name}")
    
    def get_skill(self, name):
        """Get a legacy skill by name"""
        return self._skills.get(name)
    
    def list_skills(self):
        """
        List all available skills (both systems combined)
        
        Returns:
            List of skill metadata dictionaries
        """
        skills = []
        
        # Add package skills first
        for metadata in self.skill_selector.get_available_skills():
            skills.append({
                "name": metadata["name"],
                "description": metadata["description"],
                "type": "package"
            })
        
        # Add legacy skills
        for skill in self._skills.values():
            skill_meta = skill.get_metadata()
            # Skip if already listed as package skill
            if skill_meta["name"] not in [s["name"] for s in skills]:
                skills.append({
                    **skill_meta,
                    "type": "legacy"
                })
        
        return skills
    
    def get_skill_metadata(self, name):
        """Get skill metadata"""
        # Check package skills first
        skill_dir = self.skill_selector.get_skill_dir(name)
        if skill_dir:
            from app.skills.metadata_parser import get_skill_metadata
            return get_skill_metadata(skill_dir)
        
        # Check legacy skills
        skill = self.get_skill(name)
        if skill:
            return skill.get_metadata()
        return None
    
    def get_skill_instructions(self, name):
        """Get skill instructions (legacy only)"""
        skill = self.get_skill(name)
        if skill:
            return skill.get_full_instructions()
        return None
    
    def get_skill_resources(self, name):
        """Get skill resources (legacy only)"""
        skill = self.get_skill(name)
        if skill:
            return skill.list_resources()
        return []
    
    def get_skill_resource(self, skill_name, resource_path):
        """Get skill resource (legacy only)"""
        skill = self.get_skill(skill_name)
        if skill:
            return skill.get_resource(resource_path)
        return None
    
    def should_use_skill(self, question, provider="openai"):
        """
        Determine if a skill should be used
        
        Args:
            question: User question
            provider: LLM provider ("openai" or "ollama")
            
        Returns:
            Tuple (should_use, skill_name, params)
        """
        if not self.enabled:
            return False, None, None
        
        # Try package system first with specified provider
        use_skill, skill_name, params = self.skill_selector.select_skill_with_llm(question, provider=provider)
        
        if use_skill and skill_name:
            return True, skill_name, params
        
        # Fallback to legacy system
        if self._skills:
            try:
                return self._should_use_legacy_skill(question, provider=provider)
            except Exception as e:
                logger.warning(f"[SkillManager] Legacy skill selection failed: {e}")
        
        return False, None, None
    
    def _should_use_legacy_skill(self, question, provider="openai"):
        """Legacy skill selection (for backward compatibility)"""
        if not self._skills:
            return False, None, None
        
        should_use, skill_name, params = self.skill_selector.select_skill_with_llm(question, provider=provider)
        
        if should_use and skill_name and skill_name not in self._skills:
            logger.warning(f"[SkillManager] Selected skill '{skill_name}' not loaded, skipping")
            return False, None, None
        
        return should_use, skill_name, params
    
    def execute_skill(self, skill_name, **kwargs):
        """
        Execute a skill (package or legacy)
        
        Args:
            skill_name: Skill name
            **kwargs: Skill parameters
            
        Returns:
            Execution result dictionary
        """
        logger.info("[SkillManager] Executing skill: {}, params: {}".format(skill_name, kwargs))
        
        # Try package skill first
        skill_dir = self.skill_selector.get_skill_dir(skill_name)
        if skill_dir:
            logger.info("[SkillManager] Using package skill: {}".format(skill_name))
            executor = SkillExecutor(skill_dir)
            result = executor.execute(kwargs)
            logger.info("[SkillManager] Package skill result: {}".format(result))
            return result
        
        # Try legacy skill
        skill = self.get_skill(skill_name)
        if skill:
            logger.info("[SkillManager] Using legacy skill: {}".format(skill_name))
            try:
                logger.info(f"[SKILL DEBUG] Executing legacy skill: {skill_name}, params: {kwargs}")
                print(f"[SKILL DEBUG] Executing legacy skill: {skill_name}, params: {kwargs}")
                result = skill.execute(**kwargs)
                print(f"[SKILL DEBUG] Legacy skill execution result: {result['success']}")
                return result
            except Exception as e:
                logger.error(f"[SkillManager] Legacy skill execution failed: {skill_name}, error: {str(e)}", exc_info=True)
                return {"success": False, "error": f"Skill execution failed: {str(e)}"}
        
        return {
            "success": False,
            "error": "Skill not found: {}".format(skill_name)
        }
    
    def format_skill_result(self, result):
        """
        Format skill result
        
        Args:
            result: Skill execution result
            
        Returns:
            Formatted string
        """
        print(f"[SKILL DEBUG] Formatting skill result: {result.get('success', False)}")
        
        if not result.get("success"):
            return "Skill execution failed: {}".format(result.get("error", "Unknown error"))
        
        # Handle package system output
        if "output" in result:
            return result["output"]
        
        # Extract data - check both result and result['data']
        data = result.get("data", result)
        
        # Handle papers output
        papers = data.get("papers", []) if isinstance(data, dict) else []
        if papers:
            formatted = f"## Search Results ({len(papers)} papers)\n\n"
            for i, paper in enumerate(papers, 1):
                formatted += f"### Paper {i}: {paper['title']}\n"
                formatted += f"- **Authors**: {', '.join(paper['authors'])}\n"
                formatted += f"- **Published**: {paper['published']}\n"
                formatted += f"- **Categories**: {', '.join(paper['categories'])}\n"
                formatted += f"- **Abstract**: {paper['summary'][:300]}...\n"
                formatted += f"- **PDF Link**: {paper['pdf_url']}\n"
                formatted += f"- **Details Link**: {paper['abs_url']}\n\n"
            return formatted
        
        if "data" in result:
            return str(result["data"])
        
        return str(result)


# Global instance
_skill_manager = None


def get_skill_manager():
    """Get unified skill manager instance"""
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager

