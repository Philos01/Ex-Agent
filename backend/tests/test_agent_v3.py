"""
Unit tests for ReAct Agent v3.0 modules.

Covers: LLMClient, Types, Thinker, Actor, Observer, Reflector, AgentLoop
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Types Tests ────────────────────────────────────────

class TestAgentTypes:
    def test_semver_parse(self):
        from app.agents.types import AgentStep, AgentState, ParsedOutput, AgentEvent, EventType

        step = AgentStep(thought="test", action="arxiv-watcher", action_input={"q": "x"})
        assert step.thought == "test"
        assert step.action == "arxiv-watcher"
        d = step.to_dict()
        assert d["thought"] == "test"

    def test_parsed_output_defaults(self):
        from app.agents.types import ParsedOutput
        p = ParsedOutput()
        assert p.thought == ""
        assert p.action is None
        assert not p.is_final_answer

    def test_agent_state_immutability(self):
        from app.agents.types import AgentState, AgentStep
        s1 = AgentState(iteration=0)
        step = AgentStep(thought="hello")
        s2 = s1.add_step(step)
        assert len(s1.steps) == 0
        assert len(s2.steps) == 1
        assert s2.steps[0].thought == "hello"

    def test_agent_event_to_dict(self):
        from app.agents.types import AgentEvent, EventType
        e = AgentEvent(type=EventType.THOUGHT, content="thinking...", iteration=1, total_iterations=5)
        d = e.to_dict()
        assert d["type"] == "thought"
        assert d["content"] == "thinking..."
        assert d["iteration"] == 1
        assert d["total"] == 5

    def test_event_types_enum(self):
        from app.agents.types import EventType
        assert EventType.THOUGHT.value == "thought"
        assert EventType.ACTION.value == "action"
        assert EventType.OBSERVATION.value == "observation"
        assert EventType.FINAL_ANSWER.value == "final_answer"
        assert EventType.DONE.value == "done"

    def test_step_types_enum(self):
        from app.agents.types import StepType
        assert StepType.THOUGHT.value == "thought"
        assert StepType.ACTION.value == "action"
        assert StepType.OBSERVATION.value == "observation"
        assert StepType.REFLECTION.value == "reflection"

    def test_reflection_result(self):
        from app.agents.types import ReflectionResult
        r = ReflectionResult(should_stop=True, should_continue=False, reason="done")
        assert r.should_stop
        assert not r.should_continue

    def test_action_result(self):
        from app.agents.types import ActionResult
        r = ActionResult(success=True, output="ok", tool_name="test")
        assert r.success
        assert r.output == "ok"


# ── Observer Tests ──────────────────────────────────────

class TestObserver:
    def test_infer_type_arxiv(self):
        from app.agents.observer import Observer
        from app.agents.types import ActionResult
        obs = Observer()
        result = ActionResult(tool_name="arxiv-watcher", output="papers")
        assert obs._infer_type(result) == "arxiv_search"

    def test_infer_type_weather(self):
        from app.agents.observer import Observer
        from app.agents.types import ActionResult
        obs = Observer()
        result = ActionResult(tool_name="amap-weather", output="weather")
        assert obs._infer_type(result) == "weather"

    def test_infer_type_error(self):
        from app.agents.observer import Observer
        from app.agents.types import ActionResult
        obs = Observer()
        result = ActionResult(success=False, tool_name="test", output="error occurred")
        assert obs._infer_type(result) == "error"

    def test_compress_empty(self):
        from app.agents.observer import Observer
        obs = Observer()
        assert obs.compress("") == ""

    def test_compress_generic_short(self):
        from app.agents.observer import Observer
        obs = Observer()
        text = "short result"
        assert obs.compress(text, "default") == text

    def test_compress_generic_long(self):
        from app.agents.observer import Observer
        obs = Observer()
        text = "x" * 600
        result = obs.compress(text, "default")
        assert len(result) < len(text)
        assert "[中间" in result

    def test_compress_error(self):
        from app.agents.observer import Observer
        obs = Observer()
        text = 'Error message\n  File "test.py", line 1\nReal error'
        result = obs.compress(text, "error")
        assert "Real error" in result

    def test_process_success(self):
        from app.agents.observer import Observer
        from app.agents.types import ActionResult
        obs = Observer()
        result = ActionResult(success=True, output="OK", tool_name="test")
        processed = obs.process(result)
        assert processed["success"]
        assert "compressed" in processed
        assert "raw" in processed

    def test_compress_arxiv_format(self):
        from app.agents.observer import Observer
        obs = Observer()
        text = "### Paper 1: Test Paper\n- **Abstract**: Some abstract here\n- **Authors**: John\n- **PDF Link**: http://example.com"
        result = obs.compress(text, "arxiv_search")
        assert "Test Paper" in result
        assert "Some abstract" in result


# ── Reflector Tests ─────────────────────────────────────

class TestReflector:
    def test_stop_at_max_iterations(self):
        from app.agents.reflector import Reflector
        from app.agents.types import ReflectionResult
        r = Reflector()
        result = r.evaluate(
            user_question="test", thought="thinking", action="tool",
            observation="result", iteration=4, max_iterations=5, steps=[],
        )
        assert result.should_stop
        assert "最大迭代" in result.reason

    def test_stop_when_no_action(self):
        from app.agents.reflector import Reflector
        r = Reflector()
        result = r.evaluate(
            user_question="test", thought="done", action=None,
            observation="", iteration=0, max_iterations=5, steps=[],
        )
        assert result.should_stop

    def test_strong_end_signal(self):
        from app.agents.reflector import Reflector
        r = Reflector()
        result = r.evaluate(
            user_question="test", thought="search done", action="arxiv-watcher",
            observation="搜索完成，找到3篇论文", iteration=0, max_iterations=5, steps=[],
        )
        assert result.should_stop

    def test_weak_signal_retry(self):
        from app.agents.reflector import Reflector
        r = Reflector()
        result = r.evaluate(
            user_question="test", thought="need retry", action="arxiv-watcher",
            observation="未找到结果", iteration=0, max_iterations=5, steps=[],
        )
        assert not result.should_stop
        assert result.should_continue
        assert result.suggestion is not None

    def test_repetitive_action_detection(self):
        from app.agents.reflector import Reflector
        from app.agents.types import AgentStep
        r = Reflector()
        steps = [
            AgentStep(thought="t1", action="arxiv-watcher"),
            AgentStep(thought="t2", action="arxiv-watcher"),
        ]
        result = r.evaluate(
            user_question="test", thought="t3", action="arxiv-watcher",
            observation="results", iteration=1, max_iterations=5, steps=steps,
        )
        assert result.should_stop
        assert "循环" in result.reason


# ── Token Budget Tests ──────────────────────────────────

class TestTokenBudget:
    def test_estimate_chinese(self):
        from app.agents.token_budget import TokenBudgetManager
        tb = TokenBudgetManager(max_tokens=6000)
        tokens = tb.estimate_tokens("你好世界")
        assert tokens > 0

    def test_estimate_english(self):
        from app.agents.token_budget import TokenBudgetManager
        tb = TokenBudgetManager(max_tokens=6000)
        tokens = tb.estimate_tokens("hello world this is a test")
        assert tokens > 0

    def test_can_add(self):
        from app.agents.token_budget import TokenBudgetManager
        tb = TokenBudgetManager(max_tokens=6000)
        assert tb.can_add("short text")
        # Very long string should exceed budget
        long_text = "hello world " * 10000
        assert not tb.can_add(long_text)

    def test_remaining(self):
        from app.agents.token_budget import TokenBudgetManager
        tb = TokenBudgetManager(max_tokens=1000)
        assert tb.remaining() == 1000

    def test_model_context_limit(self):
        from app.agents.token_budget import TokenBudgetManager
        tb = TokenBudgetManager(max_tokens=10000, model_name="gpt-3.5-turbo")
        assert tb.max_tokens <= 4096 * 0.9


# ── Error Handler Tests ─────────────────────────────────

class TestErrorHandler:
    def test_sanitize_api_key(self):
        from app.agents.error_handler import sanitize_error_message
        msg = "Error with key sk-12345678901234567890"
        sanitized = sanitize_error_message(Exception(msg))
        assert "sk-***" in sanitized

    def test_classify_rate_limit(self):
        from app.agents.error_handler import classify_error
        result = classify_error(Exception("rate limit exceeded"))
        assert result["category"] == "rate_limit"
        assert result["retryable"]

    def test_classify_timeout(self):
        from app.agents.error_handler import classify_error
        result = classify_error(Exception("connection timeout"))
        assert result["retryable"]

    def test_classify_unknown(self):
        from app.agents.error_handler import classify_error
        result = classify_error(Exception("something weird"))
        assert result["category"] == "unknown"
        assert not result["retryable"]


# ── Skill Registry Tests ────────────────────────────────

class TestSkillRegistry:
    def test_register_and_get(self):
        from app.skills.registry import SkillRegistry, SkillDefinition
        reg = SkillRegistry(skills_dir=None)
        sd = SkillDefinition(name="test-skill", description="A test skill")
        reg.register(sd)
        assert reg.get("test-skill") is sd
        assert len(reg) == 1

    def test_disable_and_enable(self):
        from app.skills.registry import SkillRegistry, SkillDefinition
        reg = SkillRegistry(skills_dir=None)
        sd = SkillDefinition(name="test", description="desc")
        reg.register(sd)
        assert reg.list()[0].enabled
        reg.disable("test")
        assert not reg.list(enabled_only=False)[0].enabled
        assert len(reg.list(enabled_only=True)) == 0
        reg.enable("test")
        assert len(reg.list(enabled_only=True)) == 1

    def test_unregister(self):
        from app.skills.registry import SkillRegistry, SkillDefinition
        reg = SkillRegistry(skills_dir=None)
        sd = SkillDefinition(name="test", description="desc")
        reg.register(sd)
        reg.unregister("test")
        assert reg.get("test") is None
        assert len(reg) == 0

    def test_permission_check_no_restrictions(self):
        from app.skills.registry import SkillRegistry, SkillDefinition
        reg = SkillRegistry(skills_dir=None)
        sd = SkillDefinition(name="test", description="desc")
        reg.register(sd)
        assert reg.check_permission("test")

    def test_admin_permission(self):
        from app.skills.registry import SkillRegistry, SkillDefinition
        reg = SkillRegistry(skills_dir=None)
        sd = SkillDefinition(name="test", description="desc", permissions=["admin"])
        reg.register(sd)
        assert not reg.check_permission("test", {"user_role": "user"})
        assert reg.check_permission("test", {"user_role": "admin"})

    def test_contains(self):
        from app.skills.registry import SkillRegistry, SkillDefinition
        reg = SkillRegistry(skills_dir=None)
        sd = SkillDefinition(name="test", description="desc")
        reg.register(sd)
        assert "test" in reg
        assert "other" not in reg

    def test_list_metadata(self):
        from app.skills.registry import SkillRegistry, SkillDefinition
        reg = SkillRegistry(skills_dir=None)
        sd = SkillDefinition(name="test", description="desc", version="2.0.0")
        reg.register(sd)
        meta = reg.list_metadata()
        assert len(meta) == 1
        assert meta[0]["name"] == "test"
        assert meta[0]["version"] == "2.0.0"


# ── Parameter Validator Tests ───────────────────────────

class TestParameterValidator:
    def test_required_param_missing(self):
        from app.skills.validator import ParameterValidator, ValidationError
        v = ParameterValidator({"city": {"type": "string", "required": True}})
        with pytest.raises(ValidationError):
            v.validate({})

    def test_default_value(self):
        from app.skills.validator import ParameterValidator
        v = ParameterValidator({"count": {"type": "integer", "default": 5}})
        result = v.validate({})
        assert result["count"] == 5

    def test_type_coercion_string_to_int(self):
        from app.skills.validator import ParameterValidator
        v = ParameterValidator({"count": {"type": "integer"}})
        result = v.validate({"count": "10"})
        assert result["count"] == 10
        assert isinstance(result["count"], int)

    def test_min_bound(self):
        from app.skills.validator import ParameterValidator
        v = ParameterValidator({"count": {"type": "integer", "min": 1}})
        result = v.validate({"count": -5})
        assert result["count"] == 1

    def test_max_bound(self):
        from app.skills.validator import ParameterValidator
        v = ParameterValidator({"count": {"type": "integer", "max": 100}})
        result = v.validate({"count": 999})
        assert result["count"] == 100

    def test_extra_params_passthrough(self):
        from app.skills.validator import ParameterValidator
        v = ParameterValidator({"city": {"type": "string"}})
        result = v.validate({"city": "NB", "extra": "value"})
        assert result["city"] == "NB"
        assert result["extra"] == "value"


# ── Version Manager Tests ───────────────────────────────

class TestVersionManager:
    def test_parse_semver(self):
        from app.skills.versioning import SemVer
        v = SemVer.parse("2.1.3")
        assert v.major == 2
        assert v.minor == 1
        assert v.patch == 3
        assert str(v) == "2.1.3"

    def test_semver_comparison(self):
        from app.skills.versioning import SemVer
        assert SemVer(1, 0, 0) < SemVer(2, 0, 0)
        assert SemVer(1, 2, 0) < SemVer(1, 3, 0)
        assert SemVer(1, 0, 1) < SemVer(1, 0, 2)
        assert SemVer(1, 0, 0) == SemVer(1, 0, 0)

    def test_needs_migration(self):
        from app.skills.versioning import VersionManager
        vm = VersionManager()
        vm.set_version("test", "2.0.0")
        assert vm.needs_migration("test", "1.0.0")

    def test_no_migration_needed(self):
        from app.skills.versioning import VersionManager
        vm = VersionManager()
        vm.set_version("test", "1.0.0")
        assert not vm.needs_migration("test", "1.0.0")

    def test_check_compatibility(self):
        from app.skills.versioning import VersionManager
        vm = VersionManager()
        vm.set_version("test", "2.0.0")
        # Same major, current >= required → compatible
        ok, msg = vm.check_compatibility("test", "2.0.0")
        assert ok
        # Major version mismatch → incompatible
        ok2, msg2 = vm.check_compatibility("test", "3.0.0")
        assert not ok2
        # Current newer than required, same major → compatible
        vm2 = VersionManager()
        vm2.set_version("test2", "1.5.0")
        ok3, msg3 = vm2.check_compatibility("test2", "1.0.0")
        assert ok3

    def test_version_history(self):
        from app.skills.versioning import VersionManager
        vm = VersionManager()
        vm.set_version("test", "1.0.0")
        vm.set_version("test", "1.1.0")
        vm.set_version("test", "2.0.0")
        history = vm.get_history("test")
        assert len(history) == 3


# ── Memory Scratchpad Tests ─────────────────────────────

class TestMemoryScratchpad:
    def test_add_and_get(self):
        from app.agents.memory import MemoryScratchpad
        ms = MemoryScratchpad()
        ms.add_step(thought="hello", action="test", observation="result")
        assert len(ms) == 1
        steps = ms.get_steps()
        assert steps[0]["thought"] == "hello"

    def test_clear(self):
        from app.agents.memory import MemoryScratchpad
        ms = MemoryScratchpad()
        ms.add_step(thought="hello")
        ms.clear()
        assert len(ms) == 0

    def test_scratchpad_text(self):
        from app.agents.memory import MemoryScratchpad
        ms = MemoryScratchpad()
        ms.add_step(thought="thinking", action="tool", observation="result")
        text = ms.get_scratchpad_text()
        assert "thinking" in text
        assert "tool" in text

    def test_raw_observation_storage(self):
        from app.agents.memory import MemoryScratchpad
        ms = MemoryScratchpad()
        ms.add_step(thought="t", observation="compressed", raw_observation="full raw data")
        steps = ms.get_steps()
        assert steps[0]["observation"] == "compressed"
        assert steps[0]["raw_observation"] == "full raw data"


# ── Exceptions Tests ────────────────────────────────────

class TestExceptions:
    def test_base_error(self):
        from app.agents.exceptions import ReActAgentError
        with pytest.raises(ReActAgentError):
            raise ReActAgentError("test error")

    def test_output_parse_error(self):
        from app.agents.exceptions import OutputParseError
        e = OutputParseError("bad json", raw_output="{invalid")
        assert e.raw_output == "{invalid"

    def test_tool_not_found(self):
        from app.agents.exceptions import ToolNotFoundError
        e = ToolNotFoundError("nonexistent")
        assert e.tool_name == "nonexistent"


# ── Integration: AgentLoop ──────────────────────────────

class TestAgentLoop:
    def test_init(self):
        from app.agents.agent_loop import AgentLoop
        agent = AgentLoop(max_iterations=3, provider="openai")
        assert agent.max_iterations == 3
        assert agent.provider == "openai"

    def test_reset(self):
        from app.agents.agent_loop import AgentLoop
        agent = AgentLoop()
        agent.scratchpad.add_step(thought="test")
        agent.reset()
        assert len(agent.scratchpad) == 0

    def test_validate_parsed_null_final_answer(self):
        from app.agents.agent_loop import AgentLoop
        from app.agents.types import ParsedOutput
        agent = AgentLoop()
        p = ParsedOutput(
            thought="answer",
            is_final_answer=True,
            final_answer=None,
        )
        result = agent._validate_parsed(p)
        assert not result.is_final_answer  # Should be downgraded

    def test_validate_parsed_short_final_answer(self):
        from app.agents.agent_loop import AgentLoop
        from app.agents.types import ParsedOutput
        agent = AgentLoop()
        p = ParsedOutput(
            thought="A long and detailed thought process that provides the answer",
            is_final_answer=True,
            final_answer="OK",
        )
        result = agent._validate_parsed(p)
        # Should use thought as the answer since final_answer is too short
        assert "detailed thought" in str(result.final_answer)

    def test_force_answer_fallback(self):
        from app.agents.agent_loop import AgentLoop
        from app.agents.types import ParsedOutput
        agent = AgentLoop()
        result = agent._force_answer("", ParsedOutput())
        assert "抱歉" in result  # Should return fallback message
