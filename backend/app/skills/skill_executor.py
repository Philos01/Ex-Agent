
"""
Skill Executor - Execute .sh or .py files from skill packages
Enhanced with soft-coded parameter passing and configuration support
"""
import subprocess
import sys
import json
import os
from pathlib import Path
import logging
from app.core.config import get_complete_config

logger = logging.getLogger(__name__)


class SkillExecutor:
    """
    Skill Executor - Support executing .sh and .py files
    with flexible parameter passing configuration
    """
    
    def __init__(self, skill_dir):
        self.skill_dir = Path(skill_dir)
        self.scripts_dir = self.skill_dir / "scripts"
        self.config = self._load_skill_config()
        self.cfg = get_complete_config()
    
    def _load_skill_config(self):
        """
        Load skill execution configuration from various sources
        
        Configuration sources (highest priority first):
        1. skill_config.json in skill package
        2. _meta.json in skill package
        3. Default configuration
        
        Returns:
            dict: Skill execution configuration
        """
        config = {
            "python_param_arg": "--params",
            "shell_pass_query_as_arg": True,
            "shell_query_param_name": "query",
            "env_var_prefix": "SKILL_PARAM_",
            "output_json": True
        }
        
        # Try skill_config.json
        skill_config_path = self.skill_dir / "skill_config.json"
        if skill_config_path.exists():
            try:
                with open(skill_config_path, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                    config.update(custom_config)
                logger.info(f"[SkillExecutor] Loaded custom config from {skill_config_path}")
            except Exception as e:
                logger.warning(f"[SkillExecutor] Failed to load skill_config.json: {e}")
        
        # Try _meta.json
        meta_path = self.skill_dir / "_meta.json"
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    if "skillConfig" in meta:
                        config.update(meta["skillConfig"])
                        logger.info(f"[SkillExecutor] Loaded config from _meta.json")
            except Exception as e:
                logger.warning(f"[SkillExecutor] Failed to load config from _meta.json: {e}")
        
        return config
    
    def find_executable(self):
        """
        Find executable file in skill package (prioritize .py for cross-platform)
        
        Returns:
            Found executable path, or None
        """
        # Check scripts directory first
        if self.scripts_dir.exists():
            # Look for .py files first (cross-platform)
            py_files = list(self.scripts_dir.glob("*.py"))
            if py_files:
                return py_files[0]
            
            # Look for .sh files (Unix only)
            sh_files = list(self.scripts_dir.glob("*.sh"))
            if sh_files:
                return sh_files[0]
        
        # Check skill package root
        py_files = list(self.skill_dir.glob("*.py"))
        if py_files:
            return py_files[0]
        
        sh_files = list(self.skill_dir.glob("*.sh"))
        if sh_files:
            return sh_files[0]
        
        return None
    
    def execute_python(self, script_path, params):
        """
        Execute Python script with flexible parameter passing
        
        Args:
            script_path: Python script path
            params: Parameter dictionary
            
        Returns:
            Execution result dictionary
        """
        try:
            import tempfile
            
            # Create temporary parameter file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(params, f)
                params_file = f.name
            
            try:
                # Build command with configurable param argument
                param_arg = self.config.get("python_param_arg", "--params")
                cmd = [
                    sys.executable,
                    str(script_path),
                    param_arg,
                    params_file
                ]
                
                logger.info("[SkillExecutor] Executing Python: {}".format(' '.join(cmd)))
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=min(
                        self.cfg.get("timeouts", {}).get("skill_executor_python", 60) or 60,
                        120
                    ),
                    cwd=str(self.skill_dir)
                )
                
                if result.returncode != 0:
                    logger.error("[SkillExecutor] Python script failed: {}".format(result.stderr))
                    return {
                        "success": False,
                        "error": result.stderr or "Script execution failed"
                    }
                
                # Try to parse JSON output
                try:
                    output = json.loads(result.stdout)
                    # 如果输出已经有 success 字段，直接返回（避免双重嵌套）
                    if "success" in output:
                        return output
                    # 否则包装一层
                    return {
                        "success": True,
                        "data": output
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "output": result.stdout
                    }
                    
            finally:
                # Cleanup temporary file
                try:
                    os.unlink(params_file)
                except Exception:
                    pass
                
        except Exception as e:
            logger.error("[SkillExecutor] Python execution error: {}".format(e), exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_shell(self, script_path, params):
        """
        Execute Shell script with flexible parameter passing
        
        Args:
            script_path: Shell script path
            params: Parameter dictionary
            
        Returns:
            Execution result dictionary
        """
        try:
            # Build command - pass params as environment variables
            env = os.environ.copy()
            
            # Add parameters as environment variables with configurable prefix
            env_prefix = self.config.get("env_var_prefix", "SKILL_PARAM_")
            for key, value in params.items():
                env_key = "{}{}".format(env_prefix, key.upper())
                env[env_key] = str(value)
            
            # Ensure script is executable
            if os.name != 'nt':
                try:
                    os.chmod(script_path, 0o755)
                except Exception:
                    pass
            
            # Build command - handle Windows compatibility
            if os.name == 'nt':
                # On Windows, use bash if available, or provide helpful error
                cmd = ["bash", str(script_path)]
            else:
                cmd = [str(script_path)]
            
            if self.config.get("shell_pass_query_as_arg", True):
                query_param_name = self.config.get("shell_query_param_name", "query")
                if query_param_name in params:
                    cmd.append(str(params[query_param_name]))
            
            all_params_arg = self.config.get("shell_pass_all_params_as_args", True)
            if all_params_arg:
                for key, value in params.items():
                    if key != query_param_name:
                        cmd.append(str(value))
            
            logger.info("[SkillExecutor] Executing Shell: {}".format(' '.join(cmd)))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=min(
                    self.cfg.get("timeouts", {}).get("skill_executor_shell", 60) or 60,
                    120
                ),
                cwd=str(self.skill_dir),
                env=env
            )
            
            if result.returncode != 0:
                logger.error("[SkillExecutor] Shell script failed: {}".format(result.stderr))
                return {
                    "success": False,
                    "error": result.stderr or "Script execution failed"
                }
            
            return {
                "success": True,
                "output": result.stdout
            }
            
        except Exception as e:
            logger.error("[SkillExecutor] Shell execution error: {}".format(e), exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute(self, params):
        """
        Execute skill with flexible configuration
        
        Args:
            params: Parameter dictionary
            
        Returns:
            Execution result dictionary
        """
        executable = self.find_executable()
        
        if not executable:
            return {
                "success": False,
                "error": "No executable found (.py or .sh) in skill package"
            }
        
        logger.info("[SkillExecutor] Using executable: {}".format(executable))
        
        if executable.suffix == ".py":
            return self.execute_python(executable, params)
        elif executable.suffix == ".sh":
            return self.execute_shell(executable, params)
        else:
            return {
                "success": False,
                "error": "Unsupported file type: {}".format(executable.suffix)
            }

