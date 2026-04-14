
"""
New Skill Manager - Refactored skill manager
Based on YAML frontmatter and skill package execution
"""
import logging
from pathlib import Path
from app.core.config import load_config
from app.skills.metadata_parser import get_skill_metadata
from app.skills.skill_selector import SkillSelector
from app.skills.skill_executor import SkillExecutor

logger = logging.getLogger(__name__)


class NewSkillManager:
    """
    New Skill Manager
    
    Features:
    - YAML frontmatter based skill discovery
    - LLM-driven skill selection
    - Support executing .sh and .py skill files
    - Backward compatible with old BaseSkill system
    """
    
    def __init__(self):
        self.cfg = load_config()
        
        # Set skills directory
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.skills_dir = self.project_root / "skills"
        
        logger.info("[NewSkillManager] Skills directory: {}".format(self.skills_dir))
        
        # Initialize components
        self.skill_selector = SkillSelector(self.skills_dir)
        
        # Compatibility with old system
        self._legacy_skills = {}
        self._init_legacy_compatibility()
    
    def _init_legacy_compatibility(self):
        """Initialize old system compatibility"""
        try:
            from app.skills.skill_manager import get_skill_manager
            self._legacy_manager = get_skill_manager()
            self._legacy_skills = {
                s["name"]: s for s in self._legacy_manager.list_skills()
            }
            logger.info("[NewSkillManager] Loaded {} legacy skills".format(len(self._legacy_skills)))
        except Exception as e:
            logger.warning("[NewSkillManager] Legacy system not available: {}".format(e))
            self._legacy_manager = None
    
    def list_skills(self):
        """List all available skills (new and old systems combined)"""
        skills = []
        
        # Add new system skills
        for metadata in self.skill_selector.get_available_skills():
            skills.append({
                "name": metadata["name"],
                "description": metadata["description"],
                "type": "package"
            })
        
        # Add old system skills
        for name, metadata in self._legacy_skills.items():
            if name not in [s["name"] for s in skills]:
                skills.append({
                    **metadata,
                    "type": "legacy"
                })
        
        return skills
    
    def should_use_skill(self, question):
        """
        Determine if a skill should be used (prioritize new system)
        
        Args:
            question: User question
            
        Returns:
            (should_use, skill_name, params)
        """
        # Try new system's LLM selection first
        use_skill, skill_name, params = self.skill_selector.select_skill_with_llm(question)
        
        if use_skill and skill_name:
            return True, skill_name, params
        
        # Fallback to old system
        if self._legacy_manager:
            return self._legacy_manager.should_use_skill(question)
        
        return False, None, None
    
    def execute_skill(self, skill_name, **kwargs):
        """
        Execute a skill
        
        Args:
            skill_name: Skill name
            **kwargs: Skill parameters
            
        Returns:
            Execution result
        """
        logger.info("[NewSkillManager] Executing skill: {}, params: {}".format(skill_name, kwargs))
        
        # Check if it's a new system skill package first
        skill_dir = self.skill_selector.get_skill_dir(skill_name)
        
        if skill_dir:
            logger.info("[NewSkillManager] Using package skill: {}".format(skill_name))
            executor = SkillExecutor(skill_dir)
            result = executor.execute(kwargs)
            logger.info("[NewSkillManager] Package skill result: {}".format(result))
            return result
        
        # Fallback to old system
        if self._legacy_manager:
            logger.info("[NewSkillManager] Using legacy skill: {}".format(skill_name))
            return self._legacy_manager.execute_skill(skill_name, **kwargs)
        
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
        if not result.get("success"):
            return "Skill execution failed: {}".format(result.get("error", "Unknown error"))
        
        # Handle new system output
        if "output" in result:
            return result["output"]
        
        if "data" in result:
            return str(result["data"])
        
        # Fallback to old system formatting
        if self._legacy_manager:
            return self._legacy_manager.format_skill_result(result)
        
        return str(result)


# Global instance
_new_skill_manager = None


def get_new_skill_manager():
    """Get new skill manager instance"""
    global _new_skill_manager
    if _new_skill_manager is None:
        _new_skill_manager = NewSkillManager()
    return _new_skill_manager

