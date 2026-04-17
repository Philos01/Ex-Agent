"""
单元测试 - MemoryScratchpad
"""
import pytest
from app.agents.memory import MemoryScratchpad


class TestMemoryScratchpad:
    
    def test_initialization(self):
        """测试初始化"""
        scratchpad = MemoryScratchpad()
        assert len(scratchpad) == 0
        assert scratchpad.get_scratchpad_text() == ""
    
    def test_add_step(self):
        """测试添加步骤"""
        scratchpad = MemoryScratchpad()
        scratchpad.add_step(
            thought="我需要搜索",
            action="search",
            action_input={"query": "test"},
            observation="搜索结果"
        )
        assert len(scratchpad) == 1
        
        steps = scratchpad.get_steps()
        assert steps[0]["thought"] == "我需要搜索"
        assert steps[0]["action"] == "search"
        assert steps[0]["action_input"] == {"query": "test"}
        assert steps[0]["observation"] == "搜索结果"
    
    def test_get_scratchpad_text(self):
        """测试获取暂存器文本"""
        scratchpad = MemoryScratchpad()
        scratchpad.add_step(thought="第一步思考")
        scratchpad.add_step(thought="第二步思考", action="test")
        
        text = scratchpad.get_scratchpad_text()
        assert "第一步思考" in text
        assert "第二步思考" in text
        assert "Action: test" in text
    
    def test_clear(self):
        """测试清空"""
        scratchpad = MemoryScratchpad()
        scratchpad.add_step(thought="测试")
        assert len(scratchpad) == 1
        
        scratchpad.clear()
        assert len(scratchpad) == 0
    
    def test_multiple_steps_with_separator(self):
        """测试多步骤分隔符"""
        scratchpad = MemoryScratchpad()
        scratchpad.add_step(thought="思考1")
        scratchpad.add_step(thought="思考2")
        
        text = scratchpad.get_scratchpad_text()
        assert "---" in text
