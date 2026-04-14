
"""
Skill Manager - Manages skill discovery, registration, and execution
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from app.skills.base import BaseSkill
from app.skills.discovery import get_skill_discoverer
from app.skills.skill_selector import SkillSelector
from app.core.config import load_config

logger = logging.getLogger(__name__)


class SkillManager:
    """
    Enhanced Skill Manager with LLM-based skill selection.
    
    Features:
    - Automatic skill discovery
    - LLM-based skill matching using YAML frontmatter
    - Configuration management
    - Skill execution and result formatting
    """
    
    def __init__(self, auto_discover=True):
        self._skills = {}
        self._skill_classes = {}
        self.cfg = load_config()
        skills_cfg = self.cfg.get("skills", {})
        self.enabled = skills_cfg.get("enabled", True)
        project_root = Path(__file__).resolve().parents[3]
        skills_dir = project_root / "skills"
        self.skill_selector = SkillSelector(skills_dir)
        if auto_discover:
            self._discover_and_load_skills()
    
    def _discover_and_load_skills(self):
        logger.info("Starting skill discovery and loading")
        discoverer = get_skill_discoverer()
        self._skill_classes = discoverer.get_skill_classes()
        for name, skill_cls in self._skill_classes.items():
            try:
                self._load_skill(name, skill_cls)
            except Exception as e:
                logger.error(f"Failed to load skill '{name}': {e}", exc_info=True)
        logger.info(f"Loaded {len(self._skills)} skills")
    
    def _load_skill(self, name, skill_cls):
        skill_enabled = True
        try:
            skills_config = self.cfg.get("skills", {})
            skill_config = skills_config.get(name, {})
            skill_enabled = skill_config.get("enabled", True)
        except Exception:
            pass
        if not skill_enabled:
            logger.info(f"Skipping disabled skill: {name}")
            return
        skill = skill_cls()
        self._skills[name] = skill
        logger.info(f"Loaded skill: {name}")
    
    def register_skill(self, skill):
        self._skills[skill.name] = skill
        logger.info(f"Manually registered skill: {skill.name}")
    
    def get_skill(self, name):
        return self._skills.get(name)
    
    def list_skills(self):
        return [skill.get_metadata() for skill in self._skills.values()]
    
    def get_skill_metadata(self, name):
        skill = self.get_skill(name)
        if skill:
            return skill.get_metadata()
        return None
    
    def get_skill_instructions(self, name):
        skill = self.get_skill(name)
        if skill:
            return skill.get_full_instructions()
        return None
    
    def get_skill_resources(self, name):
        skill = self.get_skill(name)
        if skill:
            return skill.list_resources()
        return []
    
    def get_skill_resource(self, skill_name, resource_path):
        skill = self.get_skill(skill_name)
        if skill:
            return skill.get_resource(resource_path)
        return None
    
    def should_use_skill(self, question):
        if not self.enabled or not self._skills:
            return False, None, None
        logger.info("[SkillManager] Using LLM to select skill for question")
        should_use, skill_name, params = self.skill_selector.select_skill_with_llm(question)
        if should_use and skill_name and skill_name not in self._skills:
            logger.warning(f"[SkillManager] Selected skill '{skill_name}' not loaded, skipping")
            return False, None, None
        return should_use, skill_name, params
    
    def execute_skill(self, skill_name, **kwargs):
        skill = self.get_skill(skill_name)
        if not skill:
            return {"success": False, "error": f"Skill not found: {skill_name}"}
        try:
            logger.info(f"Executing skill: {skill_name}, params: {kwargs}")
            print(f"[SKILL DEBUG] Executing skill: {skill_name}, params: {kwargs}")
            result = skill.execute(**kwargs)
            print(f"[SKILL DEBUG] Skill execution result: {result}")
            return result
        except Exception as e:
            logger.error(f"Skill execution failed: {skill_name}, error: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Skill execution failed: {str(e)}"}
    
    def format_skill_result(self, result):
        print(f"[SKILL DEBUG] Formatting skill result: {result}")
        if not result.get("success"):
            return f"Search failed: {result.get('error', 'Unknown error')}"
        if "papers" in result:
            papers = result.get("papers", [])
            if not papers:
                return f"No papers found for: {result.get('query', '')}"
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
        return str(result)


_skill_manager = None


def get_skill_manager():
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager

