"""
Skill Base Module - Provides the abstract base class for all skills
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """
    Abstract base class for all skills.
    
    All skill implementations must inherit from this class and implement
    the required abstract properties and methods.
    """
    
    # Class-level registry to track all skill implementations
    _registry: Set[type] = set()
    
    def __init_subclass__(cls, **kwargs):
        """Automatically register skill subclasses when they are defined"""
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith('_'):
            BaseSkill._registry.add(cls)
            logger.debug(f"Registered skill class: {cls.__name__}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique name identifier for the skill.
        
        Returns:
            str: The unique skill name (lowercase, underscores recommended)
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what the skill does.
        
        Returns:
            str: Description of the skill's functionality
        """
        pass
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """
        Parameter schema definition for the skill.
        
        Returns:
            Dict[str, Any]: Dictionary describing the expected parameters
        """
        return {}
    
    @property
    def required_config_keys(self) -> List[str]:
        """
        List of required configuration keys for this skill.
        
        Override this property to specify which config keys are required.
        
        Returns:
            List[str]: List of required configuration key names
        """
        return []
    
    @property
    def skill_dir(self) -> Path:
        """
        Get the directory path for this skill's resources.
        
        Returns:
            Path: Path to the skill's dedicated directory
        """
        base_dir = Path(__file__).parent.parent.parent.parent
        skill_dir = base_dir / "skills" / self.name
        return skill_dir
    
    def __init__(self):
        """Initialize the skill and load configuration"""
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._validate_config()
    
    def _load_config(self) -> None:
        """
        Load configuration from various sources with priority (highest to lowest):
        1. Environment variables (SKILL_{NAME}_{KEY})
        2. config.json (main configuration file)
        3. skills_config.yaml (legacy, for backward compatibility)
        """
        import os
        from app.core.config import load_config

        # Load from legacy config.json (main config file in root directory)
        try:
            cfg = load_config()
            skills_cfg = cfg.get("skills", {}).get(self.name, {})
            self._config.update(skills_cfg)
        except Exception as e:
            logger.debug(f"Could not load from config.json: {e}")

        # Load from skills_config.yaml if exists (legacy, for backward compatibility)
        # Note: config.json values take precedence over skills_config.yaml values
        try:
            yaml_config = self._load_yaml_config()
            if yaml_config:
                skill_yaml_cfg = yaml_config.get(self.name, {})
                for key, value in skill_yaml_cfg.items():
                    if key not in self._config:
                        self._config[key] = value
        except Exception as e:
            logger.debug(f"Could not load from YAML config: {e}")

        # Load from environment variables (highest priority)
        env_prefix = f"SKILL_{self.name.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                self._config[config_key] = value
    
    def _load_yaml_config(self) -> Optional[Dict[str, Any]]:
        """
        Load configuration from skills_config.yaml
        
        Returns:
            Optional[Dict[str, Any]]: Configuration dict or None
        """
        try:
            import yaml
            base_dir = Path(__file__).parent.parent.parent.parent
            config_path = base_dir / "skills_config.yaml"
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except ImportError:
            logger.debug("PyYAML not available, skipping YAML config")
        except Exception as e:
            logger.error(f"Error loading YAML config: {e}")
        
        return None
    
    def _validate_config(self) -> None:
        """
        Validate that all required configuration keys are present.
        
        Raises:
            ValueError: If any required config key is missing
        """
        missing_keys = []
        for key in self.required_config_keys:
            if key not in self._config:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(
                f"Skill '{self.name}' missing required configuration: "
                f"{', '.join(missing_keys)}"
            )
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key name
            default: Default value if key not found
            
        Returns:
            Any: Configuration value or default
        """
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value at runtime.
        
        Args:
            key: Configuration key name
            value: Value to set
        """
        self._config[key] = value
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get Level 1 metadata for the skill (name and description only).
        
        This is used for system prompts to let the LLM know what skills are available.
        
        Returns:
            Dict[str, Any]: Skill metadata
        """
        return {
            "name": self.name,
            "description": self.description
        }
    
    def get_full_instructions(self) -> Optional[str]:
        """
        Get Level 2 full instructions from SKILL.md.
        
        Returns:
            Optional[str]: Contents of SKILL.md or None if not found
        """
        skill_md_path = self.skill_dir / "SKILL.md"
        if skill_md_path.exists():
            try:
                with open(skill_md_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading SKILL.md: {e}")
        return None
    
    def get_resource(self, resource_path: str) -> Optional[bytes]:
        """
        Get Level 3 bundled resource from the skill's directory.
        
        Args:
            resource_path: Path to the resource relative to skill directory
            
        Returns:
            Optional[bytes]: Resource content or None if not found/accessible
        """
        try:
            full_path = self.skill_dir / resource_path
            
            # Security: Ensure path is within skill directory
            full_path = full_path.resolve()
            skill_dir = self.skill_dir.resolve()
            
            if not str(full_path).startswith(str(skill_dir)):
                logger.warning(f"Attempt to access resource outside skill directory: {resource_path}")
                return None
            
            if full_path.exists() and full_path.is_file():
                with open(full_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error accessing resource {resource_path}: {e}")
        
        return None
    
    def list_resources(self) -> List[str]:
        """
        List all available resources in the skill's directory.
        
        Returns:
            List[str]: List of resource paths relative to skill directory
        """
        resources = []
        try:
            if self.skill_dir.exists():
                for item in self.skill_dir.rglob("*"):
                    if item.is_file() and item.name != "SKILL.md":
                        rel_path = item.relative_to(self.skill_dir)
                        resources.append(str(rel_path))
        except Exception as e:
            logger.error(f"Error listing resources: {e}")
        
        return sorted(resources)
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the skill with the given parameters.
        
        Args:
            **kwargs: Skill parameters as defined in the parameters property
            
        Returns:
            Dict[str, Any]: Execution result dictionary with at least:
                - success: bool indicating success/failure
                - error: str with error message if failed
                - Additional skill-specific results
        """
        pass
