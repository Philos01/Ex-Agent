"""
Skill Discovery Module - Provides automatic skill scanning and loading
"""
import importlib
import inspect
import pkgutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Type, Optional, Set
from app.skills.base import BaseSkill

logger = logging.getLogger(__name__)


# Decorator for explicit skill registration
_registered_skills: Set[Type[BaseSkill]] = set()


def skill(cls: Type[BaseSkill]) -> Type[BaseSkill]:
    """
    Decorator to explicitly register a skill class.
    
    Args:
        cls: The skill class to register
        
    Returns:
        The same class (for decorator chaining)
    """
    if issubclass(cls, BaseSkill):
        _registered_skills.add(cls)
        logger.info(f"Explicitly registered skill: {cls.__name__}")
    else:
        logger.warning(f"Cannot register {cls.__name__}: not a subclass of BaseSkill")
    return cls


class SkillDiscoverer:
    """
    Discovers and loads skill classes from Python modules.
    
    Supports:
    1. Classes decorated with @skill
    2. Classes inheriting from BaseSkill
    3. Recursive directory scanning
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the skill discoverer.
        
        Args:
            base_path: Base directory to scan for skills (defaults to skills directory)
        """
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = Path(base_path)
        self._discovered_skills: Dict[str, Type[BaseSkill]] = {}
    
    def discover_skills(self, recursive: bool = True) -> Dict[str, Type[BaseSkill]]:
        """
        Discover all skills in the skills directory.
        
        Args:
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            Dict mapping skill names to skill classes
        """
        logger.info(f"Starting skill discovery in: {self.base_path}")
        
        # Clear previous results
        self._discovered_skills.clear()
        
        # Add explicitly registered skills first
        for skill_cls in _registered_skills:
            try:
                self._register_skill_class(skill_cls)
            except Exception as e:
                logger.error(f"Failed to register explicit skill {skill_cls.__name__}: {e}")
        
        # Scan Python files
        if recursive:
            python_files = list(self.base_path.rglob("*.py"))
        else:
            python_files = list(self.base_path.glob("*.py"))
        
        # Filter out __init__.py and discovery.py
        python_files = [
            f for f in python_files 
            if f.name not in ("__init__.py", "discovery.py", "base.py")
        ]
        
        logger.debug(f"Found {len(python_files)} Python files to scan")
        
        for file_path in python_files:
            try:
                self._scan_file(file_path)
            except Exception as e:
                logger.error(f"Error scanning file {file_path}: {e}", exc_info=True)
        
        logger.info(f"Skill discovery complete. Found {len(self._discovered_skills)} skills")
        return self._discovered_skills
    
    def _scan_file(self, file_path: Path) -> None:
        """
        Scan a single Python file for skill classes.
        
        Args:
            file_path: Path to the Python file
        """
        try:
            # Convert file path to module name
            # Find backend/app/skills/xxx.py -> app.skills.xxx
            backend_dir = self.base_path.parent.parent
            rel_path = file_path.relative_to(backend_dir)
            module_name = rel_path.with_suffix("").as_posix().replace("/", ".")
            
            logger.debug(f"Scanning module: {module_name}")
            
            # Import the module
            module = importlib.import_module(module_name)
            
            # Inspect all classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a skill class
                if (
                    issubclass(obj, BaseSkill) and 
                    obj is not BaseSkill and 
                    not name.startswith("_")
                ):
                    try:
                        self._register_skill_class(obj)
                    except Exception as e:
                        logger.error(f"Failed to register skill {name} from {module_name}: {e}")
        
        except Exception as e:
            logger.error(f"Error importing module from {file_path}: {e}", exc_info=True)
    
    def _register_skill_class(self, skill_cls: Type[BaseSkill]) -> None:
        """
        Register a skill class.
        
        Args:
            skill_cls: The skill class to register
        """
        # Try to instantiate to get the name
        try:
            # We just need the name, don't fully initialize
            # Create a minimal instance to get the name property
            # Temporarily bypass __init__ to avoid config issues
            temp_instance = object.__new__(skill_cls)
            
            # Check if name is unique
            skill_name = temp_instance.name
            if skill_name in self._discovered_skills:
                existing = self._discovered_skills[skill_name]
                logger.warning(
                    f"Duplicate skill name '{skill_name}': "
                    f"replacing {existing.__name__} with {skill_cls.__name__}"
                )
            
            self._discovered_skills[skill_name] = skill_cls
            logger.debug(f"Registered skill class: {skill_cls.__name__} as '{skill_name}'")
        
        except Exception as e:
            logger.warning(
                f"Could not get name for skill class {skill_cls.__name__}: {e}"
            )
            # Fall back to class name
            skill_name = skill_cls.__name__.lower()
            if skill_name.endswith("skill"):
                skill_name = skill_name[:-5]
            
            if skill_name not in self._discovered_skills:
                self._discovered_skills[skill_name] = skill_cls
                logger.debug(f"Registered skill class (fallback): {skill_cls.__name__} as '{skill_name}'")
    
    def get_skill_classes(self) -> Dict[str, Type[BaseSkill]]:
        """
        Get all discovered skill classes.
        
        Returns:
            Dict mapping skill names to skill classes
        """
        if not self._discovered_skills:
            self.discover_skills()
        return self._discovered_skills.copy()
    
    def create_skill_instance(self, skill_name: str) -> Optional[BaseSkill]:
        """
        Create an instance of a discovered skill.
        
        Args:
            skill_name: Name of the skill to instantiate
            
        Returns:
            Skill instance or None if not found
        """
        skill_cls = self._discovered_skills.get(skill_name)
        if skill_cls:
            try:
                return skill_cls()
            except Exception as e:
                logger.error(f"Failed to instantiate skill '{skill_name}': {e}", exc_info=True)
        return None


# Global discoverer instance
_discoverer: Optional[SkillDiscoverer] = None


def get_skill_discoverer() -> SkillDiscoverer:
    """
    Get the global skill discoverer instance.
    
    Returns:
        SkillDiscoverer instance
    """
    global _discoverer
    if _discoverer is None:
        _discoverer = SkillDiscoverer()
        # Run discovery on first access
        _discoverer.discover_skills()
    return _discoverer


def discover_skills() -> Dict[str, Type[BaseSkill]]:
    """
    Convenience function to discover all skills.
    
    Returns:
        Dict mapping skill names to skill classes
    """
    return get_skill_discoverer().discover_skills()
