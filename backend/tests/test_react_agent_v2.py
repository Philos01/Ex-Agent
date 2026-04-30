"""
ReAct Agent v2.0 单元测试
覆盖: TokenBudgetManager, ObservationCompressor, Reflector, OutputParser, MemoryScratchpad, ErrorHandler
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestTokenBudgetManager:
    def test_estimate_tokens_chinese(self):
        from app.agents.token_budget import TokenBudgetManager
        mgr = TokenBudgetManager(max_tokens=6000)
        tokens = mgr.estimate_tokens("这是一个中文测试文本")
        assert tokens > 0

    def test_estimate_tokens_english(self):
        from app.agents.token_budget import TokenBudgetManager
        mgr = TokenBudgetManager(max_tokens=6000)
        tokens = mgr.estimate_tokens("This is an English test text")
        assert tokens > 0

    def test_remaining(self):
        from app.agents.token_budget import TokenBudgetManager
        mgr = TokenBudgetManager(max_tokens=6000)
        mgr.system_prompt_tokens = 1000
        assert mgr.remaining() == 5000

    def test_can_add(self):
        from app.agents.token_budget import TokenBudgetManager
        mgr = TokenBudgetManager(max_tokens=6000)
        mgr.system_prompt_tokens = 5900
        assert not mgr.can_add("a very long text that exceeds budget" * 100)

    def test_recommended_observation_limit(self):
        from app.agents.token_budget import TokenBudgetManager
        mgr = TokenBudgetManager(max_tokens=6000)
        mgr.system_prompt_tokens = 1000
        limit = mgr.recommended_observation_limit(0, 5)
        assert limit >= 200

    def test_model_context_limit(self):
        from app.agents.token_budget import TokenBudgetManager
        mgr = TokenBudgetManager(max_tokens=100000, model_name="gpt-3.5-turbo")
        assert mgr.max_tokens <= 4096 * 0.9


class TestObservationCompressor:
    def test_compress_arxiv_papers_truncates_abstracts(self):
        from app.agents.observation_compressor import ObservationCompressor
        comp = ObservationCompressor()
        long_abstract = "A" * 500
        text = f"## Search Results\n\n### Paper 1: Test Paper\n- **Abstract**: {long_abstract}\n- **PDF Link**: https://example.com"
        result = comp.compress(text, obs_type="arxiv_search")
        assert len(result) < len(text)

    def test_compress_arxiv_papers_limits_count(self):
        from app.agents.observation_compressor import ObservationCompressor
        comp = ObservationCompressor()
        papers = ""
        for i in range(5):
            papers += f"### Paper {i+1}: Paper Title {i+1}\n- **Abstract**: Abstract {i+1}\n- **PDF Link**: url{i+1}\n\n"
        result = comp.compress(papers, obs_type="arxiv_search")
        assert "展示前 3 篇" in result

    def test_compress_weather_extracts_key_fields(self):
        from app.agents.observation_compressor import ObservationCompressor
        comp = ObservationCompressor()
        text = "- **city**: 宁波\n- **temperature**: 25°C\n- **weather**: 晴\n- **humidity**: 60%\n- **wind**: 东南风3级\n- **extra_field**: 不重要"
        result = comp.compress(text, obs_type="weather")
        assert "city" in result
        assert "temperature" in result

    def test_compress_error_removes_stack_traces(self):
        from app.agents.observation_compressor import ObservationCompressor
        comp = ObservationCompressor()
        text = "工具执行失败: ConnectionError\nFile \"test.py\", line 10\n  raise ConnectionError\n  more stack trace"
        result = comp.compress(text, obs_type="error")
        assert "File" not in result

    def test_compress_generic_keeps_head_and_tail(self):
        from app.agents.observation_compressor import ObservationCompressor
        comp = ObservationCompressor()
        text = "A" * 1000
        result = comp.compress(text, obs_type="default")
        assert "已省略" in result

    def test_infer_type_from_action_name(self):
        from app.agents.observation_compressor import ObservationCompressor
        comp = ObservationCompressor()
        assert comp._infer_type("some text", "arxiv-watcher") == "arxiv_search"
        assert comp._infer_type("some text", "amap-weather") == "weather"

    def test_compress_empty_string(self):
        from app.agents.observation_compressor import ObservationCompressor
        comp = ObservationCompressor()
        assert comp.compress("") == ""


class TestReflector:
    def test_max_iterations_forces_stop(self):
        from app.agents.reflector import Reflector
        ref = Reflector()
        result = ref.evaluate(
            user_question="test",
            thought="thinking",
            action="arxiv-watcher",
            observation="results",
            iteration=4,
            max_iterations=5,
            steps=[]
        )
        assert result.should_stop is True

    def test_no_action_triggers_stop(self):
        from app.agents.reflector import Reflector
        ref = Reflector()
        result = ref.evaluate(
            user_question="test",
            thought="I can answer directly",
            action=None,
            observation="",
            iteration=0,
            max_iterations=5,
            steps=[]
        )
        assert result.should_stop is True
        assert result.confidence >= 0.9

    def test_strong_end_signal_triggers_stop(self):
        from app.agents.reflector import Reflector
        ref = Reflector()
        result = ref.evaluate(
            user_question="test",
            thought="searching",
            action="arxiv-watcher",
            observation="搜索完成，找到3篇论文",
            iteration=0,
            max_iterations=5,
            steps=[]
        )
        assert result.should_stop is True

    def test_weak_continue_signal_suggests_retry(self):
        from app.agents.reflector import Reflector
        ref = Reflector()
        result = ref.evaluate(
            user_question="test",
            thought="searching",
            action="arxiv-watcher",
            observation="未找到相关论文",
            iteration=0,
            max_iterations=5,
            steps=[]
        )
        assert result.should_continue is True
        assert result.suggestion is not None

    def test_consecutive_same_action_triggers_stop(self):
        from app.agents.reflector import Reflector
        ref = Reflector()
        steps = [
            {"action": "arxiv-watcher"},
            {"action": "arxiv-watcher"}
        ]
        result = ref.evaluate(
            user_question="test",
            thought="searching again",
            action="arxiv-watcher",
            observation="more results",
            iteration=2,
            max_iterations=5,
            steps=steps
        )
        assert result.should_stop is True
        assert "循环" in result.reason


class TestOutputParser:
    def test_parse_json_code_block(self):
        from app.agents.output_parser import OutputParser
        parser = OutputParser(mode="json")
        text = '```json\n{"thought": "test", "action": null, "action_input": null, "is_final_answer": true, "final_answer": "42"}\n```'
        result = parser.parse(text)
        assert result["is_final_answer"] is True
        assert result["final_answer"] == "42"

    def test_parse_bare_json(self):
        from app.agents.output_parser import OutputParser
        parser = OutputParser(mode="json")
        text = '{"thought": "test", "action": "arxiv-watcher", "action_input": {"query": "test"}, "is_final_answer": false, "final_answer": null}'
        result = parser.parse(text)
        assert result["action"] == "arxiv-watcher"

    def test_parse_mixed_text_with_json(self):
        from app.agents.output_parser import OutputParser
        parser = OutputParser(mode="json")
        text = 'Here is my analysis:\n{"thought": "need to search", "action": "arxiv-watcher", "action_input": {"query": "remote sensing"}, "is_final_answer": false, "final_answer": null}\nThat is my response.'
        result = parser.parse(text)
        assert result["action"] == "arxiv-watcher"

    def test_parse_fallback_to_text(self):
        from app.agents.output_parser import OutputParser
        parser = OutputParser(mode="text")
        text = "Thought: I should search\nAction: arxiv-watcher\nAction Input: {\"query\": \"test\"}"
        result = parser.parse(text)
        assert result["thought"] == "I should search"
        assert result["action"] == "arxiv-watcher"

    def test_normalize_null_action(self):
        from app.agents.output_parser import OutputParser
        parser = OutputParser(mode="json")
        text = '{"thought": "I know the answer", "action": "null", "action_input": "null", "is_final_answer": true, "final_answer": "The answer"}'
        result = parser.parse(text)
        assert result["action"] is None

    def test_repair_incomplete_json(self):
        from app.agents.output_parser import OutputParser
        parser = OutputParser(mode="json")
        text = '{"thought": "test", "action": null, "is_final_answer": true'
        result = parser._try_repair_json(text)
        assert result is not None
        assert result.endswith("}")


class TestMemoryScratchpad:
    def test_add_step_with_raw_observation(self):
        from app.agents.memory import MemoryScratchpad
        pad = MemoryScratchpad()
        pad.add_step(
            thought="thinking",
            action="arxiv-watcher",
            observation="compressed",
            raw_observation="full raw output"
        )
        steps = pad.get_steps()
        assert len(steps) == 1
        assert steps[0]["observation"] == "compressed"
        assert steps[0]["raw_observation"] == "full raw output"

    def test_compress_history(self):
        from app.agents.memory import MemoryScratchpad
        from app.agents.observation_compressor import ObservationCompressor
        pad = MemoryScratchpad()
        comp = ObservationCompressor()
        long_obs = "A" * 1000
        pad.add_step(
            thought="searching",
            action="some-tool",
            observation=long_obs,
            raw_observation=long_obs
        )
        pad.compress_history(comp)
        steps = pad.get_steps()
        assert len(steps[0]["observation"]) < len(long_obs)

    def test_get_total_chars(self):
        from app.agents.memory import MemoryScratchpad
        pad = MemoryScratchpad()
        pad.add_step(thought="t1", observation="abc")
        pad.add_step(thought="t2", observation="defg")
        assert pad.get_total_chars() == 7

    def test_scratchpad_text_truncates_early_steps(self):
        from app.agents.memory import MemoryScratchpad
        pad = MemoryScratchpad()
        pad.add_step(thought="t1", action="a1", observation="A" * 500)
        pad.add_step(thought="t2", action="a2", observation="B" * 100)
        text = pad.get_scratchpad_text()
        assert "..." in text

    def test_clear(self):
        from app.agents.memory import MemoryScratchpad
        pad = MemoryScratchpad()
        pad.add_step(thought="test")
        pad.clear()
        assert len(pad) == 0


class TestErrorHandler:
    def test_sanitize_api_key(self):
        from app.agents.error_handler import sanitize_error_message
        error = Exception("API call failed with key sk-1234567890abcdef1234567890")
        msg = sanitize_error_message(error)
        assert "sk-***" in msg
        assert "1234567890abcdef" not in msg

    def test_classify_rate_limit(self):
        from app.agents.error_handler import classify_error
        error = Exception("Rate limit exceeded")
        result = classify_error(error)
        assert result["category"] == "rate_limit"
        assert result["retryable"] is True

    def test_classify_timeout(self):
        from app.agents.error_handler import classify_error
        error = Exception("Request timeout after 30s")
        result = classify_error(error)
        assert result["category"] == "timeout"
        assert result["retryable"] is True

    def test_classify_unknown(self):
        from app.agents.error_handler import classify_error
        error = Exception("Something unexpected happened")
        result = classify_error(error)
        assert result["category"] == "unknown"
        assert result["retryable"] is False

    def test_sanitize_bearer_token(self):
        from app.agents.error_handler import sanitize_error_message
        error = Exception("Auth failed: Bearer eyJhbGciOiJIUzI1NiJ9.test.sig")
        msg = sanitize_error_message(error)
        assert "Bearer ***" in msg
        assert "eyJhbGciOiJIUzI1NiJ9" not in msg


class TestReActAgentV2Integration:
    def test_run_returns_dict(self):
        from app.agents import AgentLoop
        with patch.object(AgentLoop, '__init__', lambda self, **kwargs: None):
            agent = AgentLoop.__new__(AgentLoop)
            agent.max_iterations = 1
            agent.provider = "openai"
            agent.scratchpad = MagicMock()
            agent.scratchpad.get_steps.return_value = []
            agent.scratchpad.get_scratchpad_text.return_value = ""
            agent.token_budget = MagicMock()
            agent.token_budget.estimate_tokens.return_value = 100
            agent.token_budget.max_tokens = 6000
            agent.prompt_engine = MagicMock()
            agent.prompt_engine.build_prompt.return_value = "test prompt"
            agent.thinker = MagicMock()
            agent.thinker.think.return_value = __import__('app.agents.types', fromlist=['ParsedOutput']).ParsedOutput(
                thought="I know the answer",
                action=None,
                action_input=None,
                is_final_answer=True,
                final_answer="42"
            )
            agent.reflector = MagicMock()
            agent.reflector.evaluate.return_value = __import__('app.agents.types', fromlist=['ReflectionResult']).ReflectionResult(
                should_stop=True,
                should_continue=False,
                confidence=0.9,
                reason="test",
            )
            agent.observer = MagicMock()
            agent._build_prompt = MagicMock(return_value="test prompt")
            agent._do_think = MagicMock(return_value=agent.thinker.think.return_value)
            agent._validate_parsed = MagicMock(side_effect=lambda x: x)

            result = agent.run("What is 6*7?")
            assert result["final_answer"] == "42"
            assert result["success"] is True
