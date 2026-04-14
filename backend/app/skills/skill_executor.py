
"""
Skill Executor - Execute .sh or .py files from skill packages
"""
import subprocess
import sys
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SkillExecutor:
    """
    Skill Executor - Support executing .sh and .py files
    """
    
    def __init__(self, skill_dir):
        self.skill_dir = skill_dir
        self.scripts_dir = skill_dir / "scripts"
        
    def find_executable(self):
        """
        Find executable file in skill package
        
        Returns:
            Found executable path, or None
        """
        # Check scripts directory first
        if self.scripts_dir.exists():
            # Look for .py files
            py_files = list(self.scripts_dir.glob("*.py"))
            if py_files:
                return py_files[0]
            
            # Look for .sh files
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
        Execute Python script
        
        Args:
            script_path: Python script path
            params: Parameter dictionary
            
        Returns:
            Execution result dictionary
        """
        try:
            # Method 1: Call via subprocess (isolated environment)
            import tempfile
            
            # Create temporary parameter file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(params, f)
                params_file = f.name
            
            try:
                # Build command
                cmd = [
                    sys.executable,
                    str(script_path),
                    "--params",
                    params_file
                ]
                
                logger.info("[SkillExecutor] Executing Python: {}".format(' '.join(cmd)))
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
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
                os.unlink(params_file)
                
        except Exception as e:
            logger.error("[SkillExecutor] Python execution error: {}".format(e), exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_shell(self, script_path, params):
        """
        Execute Shell script
        
        Args:
            script_path: Shell script path
            params: Parameter dictionary
            
        Returns:
            Execution result dictionary
        """
        try:
            # Build command - pass params as environment variables
            env = os.environ.copy()
            
            # Add parameters as environment variables
            for key, value in params.items():
                env_key = "SKILL_PARAM_{}".format(key.upper())
                env[env_key] = str(value)
            
            # Ensure script is executable
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            # Build command
            cmd = [str(script_path)]
            
            # If query parameter exists, pass as first argument
            if "query" in params:
                cmd.append(str(params["query"]))
            
            logger.info("[SkillExecutor] Executing Shell: {}".format(' '.join(cmd)))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
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
        Execute skill
        
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

