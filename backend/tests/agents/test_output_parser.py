"""
单元测试 - OutputParser
"""
import pytest
from app.agents.output_parser import OutputParser
from app.agents.exceptions import OutputParseError


class TestOutputParser:
    
    def test_parse_json_success(self):
        """测试成功解析 JSON"""
        parser = OutputParser(mode="json")
        text = '''```json
        {
            "thought": "我需要搜索",
            "action": "search",
            "action_input": {"query": "test"},
            "is_final_answer": false,
            "final_answer": null
        }
        ```'''
        result = parser.parse(text)
        assert result["thought"] == "我需要搜索"
        assert result["action"] == "search"
        assert result["action_input"] == {"query": "test"}
        assert result["is_final_answer"] is False
    
    def test_parse_json_final_answer(self):
        """测试解析最终答案"""
        parser = OutputParser(mode="json")
        text = '''```json
        {
            "thought": "我现在知道最终答案了。",
            "action": null,
            "action_input": null,
            "is_final_answer": true,
            "final_answer": "这是最终答案"
        }
        ```'''
        result = parser.parse(text)
        assert result["is_final_answer"] is True
        assert result["final_answer"] == "这是最终答案"
    
    def test_parse_invalid_json(self):
        """测试解析无效 JSON"""
        parser = OutputParser(mode="json")
        with pytest.raises(OutputParseError):
            parser.parse("invalid json")
    
    def test_parse_text_mode(self):
        """测试文本模式解析"""
        parser = OutputParser(mode="text")
        text = """Thought: 我需要搜索
Action: search
Action Input: {"query": "test"}
Observation: 结果"""
        result = parser.parse(text)
        assert result["thought"] == "我需要搜索"
        assert result["action"] == "search"
    
    def test_parse_text_final_answer(self):
        """测试文本模式最终答案"""
        parser = OutputParser(mode="text")
        text = """Thought: 我现在知道最终答案了。
Final Answer: 这是最终答案"""
        result = parser.parse(text)
        assert result["is_final_answer"] is True
        assert result["final_answer"] == "这是最终答案"
    
    def test_normalize_null_action(self):
        """测试标准化 null action"""
        parser = OutputParser(mode="json")
        text = '''{"thought": "test", "action": "null", "is_final_answer": false}'''
        result = parser.parse(text)
        assert result["action"] is None
