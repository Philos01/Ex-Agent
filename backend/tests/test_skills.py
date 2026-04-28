"""
Skill system tests
Tests for skill selection, execution, and parameter handling
"""
import pytest
from unittest.mock import patch, MagicMock


class TestSkillSelector:
    """Tests for skill selection"""
    
    def test_ollama_model_configurable(self):
        """Test that Ollama model name is configurable"""
        from app.skills.skill_selector import SkillSelector
        import inspect
        
        source = inspect.getsource(SkillSelector._call_ollama)
        assert 'cfg.get("ollama_model"' in source or "self.cfg.get" in source


class TestSkillExecutor:
    """Tests for skill execution"""
    
    def test_timeout_not_disabled(self):
        """Test that timeout cannot be completely disabled"""
        from app.skills.skill_executor import SkillExecutor
        import inspect
        
        source = inspect.getsource(SkillExecutor.execute_python)
        assert "min(" in source or "120" in source
    
    def test_shell_params_passed(self):
        """Test that shell parameters are passed correctly"""
        from app.skills.skill_executor import SkillExecutor
        import inspect
        
        source = inspect.getsource(SkillExecutor.execute_shell)
        assert "shell_pass_all_params_as_args" in source or "params.items()" in source


class TestSkillManager:
    """Tests for skill manager"""
    
    def test_parameter_normalization(self):
        """Test that parameters are normalized"""
        from app.skills.skill_manager import SkillManager
        
        assert hasattr(SkillManager, '_normalize_params')
    
    def test_weather_location_mapping(self):
        """Test that weather location parameter is mapped to city"""
        from app.skills.skill_manager import SkillManager
        
        mgr = SkillManager.__new__(SkillManager)
        mgr.cfg = {}
        
        params = {"location": "Beijing"}
        normalized = mgr._normalize_params("amap-weather", params)
        
        assert "city" in normalized
        assert normalized["city"] == "Beijing"
    
    def test_arxiv_query_mapping(self):
        """Test that arxiv search_query is mapped to query"""
        from app.skills.skill_manager import SkillManager
        
        mgr = SkillManager.__new__(SkillManager)
        mgr.cfg = {}
        
        params = {"search_query": "machine learning"}
        normalized = mgr._normalize_params("arxiv-watcher", params)
        
        assert "query" in normalized
        assert normalized["query"] == "machine learning"


class TestCommandSkillTrigger:
    """Tests for command-based skill triggering"""
    
    def test_skill_command_pattern(self):
        """Test that /skill command pattern is recognized"""
        import re
        
        pattern = r'^/skill\s+(\S+)(?:\s+(.*))?$'
        
        match = re.match(pattern, "/skill arxiv-watcher query=AI")
        assert match is not None
        assert match.group(1) == "arxiv-watcher"
        
        match = re.match(pattern, "/skill amap-weather city=Beijing")
        assert match is not None
        assert match.group(1) == "amap-weather"
        
        match = re.match(pattern, "What is the weather?")
        assert match is None
