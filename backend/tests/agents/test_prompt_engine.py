"""
单元测试 - PromptEngine
"""
from app.agents.prompt_engine import PromptEngine


class TestPromptEngine:
    
    def test_initialization(self):
        """测试初始化"""
        tools = [{"name": "test", "description": "test tool"}]
        engine = PromptEngine(tools=tools, use_few_shot=True)
        assert len(engine.tools) == 1
    
    def test_build_prompt(self):
        """测试构建提示词"""
        tools = [{"name": "search", "description": "搜索工具"}]
        engine = PromptEngine(tools=tools)
        
        prompt = engine.build_prompt(
            user_question="测试问题",
            scratchpad_text="",
            conversation_history="",
            provider="openai"
        )
        
        assert "测试问题" in prompt
        assert "search" in prompt
        assert "可用工具" in prompt
    
    def test_build_tools_description(self):
        """测试构建工具描述"""
        tools = [
            {"name": "tool1", "description": "第一个工具"},
            {"name": "tool2", "description": "第二个工具"}
        ]
        engine = PromptEngine(tools=tools)
        desc = engine._build_tools_description()
        
        assert "tool1" in desc
        assert "tool2" in desc
        assert "第一个工具" in desc
    
    def test_build_prompt_with_scratchpad(self):
        """测试带暂存器的提示词构建"""
        engine = PromptEngine(tools=[])
        prompt = engine.build_prompt(
            user_question="test",
            scratchpad_text="Thought: 之前的思考",
            conversation_history=""
        )
        assert "之前的思考" in prompt
    
    def test_build_prompt_without_tools(self):
        """测试没有工具的情况"""
        engine = PromptEngine(tools=[])
        prompt = engine.build_prompt(user_question="test", scratchpad_text="", conversation_history="")
        assert "当前没有可用工具" in prompt
