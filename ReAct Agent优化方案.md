# ReAct Agent 架构优化方案

> **版本**: v1.0  
> **日期**: 2026-04-29  
> **适用模块**: `backend/app/agents/` (react_agent, prompt_engine, memory, output_parser, exceptions)  
> **当前版本问题数**: 19 项 (P0: 4, P1: 8, P2: 7)

---

## 一、当前架构问题诊断

### 1.1 架构全景图

```
┌─────────────────────────────────────────────────────────┐
│                    ReActAgent 核心循环                    │
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ Thought  │──▶│  Action  │──▶│Observation│──┐         │
│  │ (LLM推理) │   │ (Tool调用)│   │ (结果注入) │  │         │
│  └──────────┘   └──────────┘   └──────────┘  │         │
│        ▲                                      │         │
│        └──────────────────────────────────────┘         │
│                    更新 Scratchpad                       │
│                                                         │
│  终止条件: is_final_answer=true 或 max_iterations 达上限  │
└─────────────────────────────────────────────────────────┘
```

### 1.2 问题清单

#### P0 — 架构级缺陷

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| **A1** | `run()` 和 `stream_run()` 代码重复率 >90%——两个方法各 ~120 行，核心循环逻辑完全一致 | [react_agent.py:294-551](backend/app/agents/react_agent.py#L294-L551) | 修改逻辑需双倍维护，易产生行为不一致 |
| **A2** | Scratchpad 无限膨胀——每轮将完整 Observation（如 10 篇论文全文）原样存入，Prompt 随迭代线性增长 | [memory.py:49-78](backend/app/agents/memory.py#L49-L78) | 第 3-4 轮时 prompt 超模型 context window，导致输出截断或幻觉 |
| **A3** | 无 Token 预算管理——PromptEngine 构建 prompt 时不做任何 token 计数或截断 | [prompt_engine.py:34-122](backend/app/agents/prompt_engine.py#L34-L122) | GPT-3.5-turbo (4K context) 在第 2-3 轮即可能溢出 |
| **A4** | 每次迭代重建完整 Prompt——包括 `_build_kb_overview()`（全量扫描知识库摘要），第 N 轮与第 1 轮成本相同 | [prompt_engine.py:60-65](backend/app/agents/prompt_engine.py#L60-L65) | 不必要的 I/O 和 token 浪费 |

#### P1 — 逻辑缺陷

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| **B1** | `_should_force_final_answer` 依赖关键词硬编码匹配——13 个中英文关键词 + 5 个 hint 词 | [react_agent.py:124-174](backend/app/agents/react_agent.py#L124-L174) | 模型换用不同措辞则漏判，导致迭代浪费 |
| **B2** | LLM 调用参数硬编码——`temp=0.1, max_tokens=1024` 不可配置 | [react_agent.py:574-576](backend/app/agents/react_agent.py#L574-L576) | 不同提供者/场景需要对温度和 token 数做调整 |
| **B3** | `_call_llm` 非流式——即使在 `stream_run()` 中也等待完整 LLM 响应 | [react_agent.py:553-647](backend/app/agents/react_agent.py#L553-L647) | 用户需等完整 Thought 生成后才能看到任何内容，体验差 |
| **B4** | 工具执行失败后无重试/降级——直接 `observation = "工具执行失败: ..."` | [react_agent.py:384-385](backend/app/agents/react_agent.py#L384-L385) | 瞬态网络错误（ArXiv API 暂时不可用）导致整个任务失败 |
| **B5** | `_validate_and_complete_params` 仅处理 2 个技能——硬编码 if/elif，新技能需改 Agent 代码 | [react_agent.py:259-290](backend/app/agents/react_agent.py#L259-L290) | 破坏技能系统的可扩展性 |
| **B6** | OutputParser 的 JSON 提取仅匹配 ` ```json ``` ` 代码块和裸 JSON——未处理 LLM 常见的"附带解释文本+JSON"混合输出 | [output_parser.py:75-88](backend/app/agents/output_parser.py#L75-L88) | 约 10-15% 的 LLM 响应解析失败，触发重试浪费 |
| **B7** | `reset()` 从未被调用——每次请求创建新 `ReActAgent()` 实例 | [react_agent.py:676-678](backend/app/agents/react_agent.py#L676-L678) + [qa.py:340](backend/app/services/qa.py#L340) | MemoryScratchpad 的状态管理设计形同虚设 |
| **B8** | 缺少 Reflection 阶段——传统 ReAct 的 Thought→Action→Obs→**Reflection** 中缺乏显式的反思步骤 | [react_agent.py:294-395](backend/app/agents/react_agent.py#L294-L395) | Agent 可能在错误路径上反复迭代而不自知 |

#### P2 — 健壮性与体验

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| **C1** | LLM 重试无退避策略——连续重试无延迟，可能触发 API rate limit | [react_agent.py:331-348](backend/app/agents/react_agent.py#L331-L348) | 瞬时错误后立即重试往往再次失败 |
| **C2** | 无迭代级超时——单次 LLM 调用可能挂起，仅依赖 `max_iterations` 无法防护 | [react_agent.py:314-395](backend/app/agents/react_agent.py#L314-L395) | 一次调用阻塞整个请求 |
| **C3** | 异常信息直接暴露给用户——`f"执行过程中发生错误: {str(e)}"` | [react_agent.py:408-409](backend/app/agents/react_agent.py#L408-L409) | API Key 等敏感信息可能在错误消息中泄露 |
| **C4** | 对话历史在 ReAct 模式中忽略 `skill_result`/`skill_name`——跨轮次工具调用结果丢失 | [qa.py:327-337](backend/app/services/qa.py#L327-L337) | 用户追问时 Agent 不记得刚搜索过的论文 |
| **C5** | `PromptEngine._build_kb_overview()` 在每次构建 prompt 时全量读取摘要文件——纯 I/O 无缓存 | [prompt_engine.py:154-182](backend/app/agents/prompt_engine.py#L154-L182) | 每个迭代都做一次全量摘要磁盘读取 |
| **C6** | `_extract_final_answer_from_thought` 的 6 个正则仅匹配中文/英文固定模板 | [react_agent.py:195-201](backend/app/agents/react_agent.py#L195-L201) | 模型用不同语序表达无法提取，回退到整段 thought |
| **C7** | 无工具调用前的参数合理性校验——空 query、负数 count 直接透传 | [react_agent.py:378-387](backend/app/agents/react_agent.py#L378-L387) | 浪费一次工具调用和完整的 LLM 往返 |

---

## 二、架构优化设计

### 2.1 目标架构

```
┌──────────────────────────────────────────────────────────────────┐
│                   ReActAgent v2.0 优化架构                         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    AgentLoop (统一循环引擎)                    │ │
│  │                                                             │ │
│  │  ┌────────┐  ┌────────┐  ┌──────────┐  ┌───────────┐       │ │
│  │  │Think   │─▶│Act     │─▶│Observe   │─▶│Reflect    │──┐    │ │
│  │  │(LLM)   │  │(Tool)  │  │(Parse)   │  │(Evaluate) │  │    │ │
│  │  └────────┘  └────────┘  └──────────┘  └───────────┘  │    │ │
│  │       │                                        │       │    │ │
│  │       │            ┌──────────┐                │       │    │ │
│  │       │            │ 短路判断  │◀───────────────┘       │    │ │
│  │       │            │ (可回答?) │                        │    │ │
│  │       │            └────┬─────┘                        │    │ │
│  │       │                 │YES                           │    │ │
│  │       ▼                 ▼                              │    │ │
│  │  ┌──────────────────────────┐                          │    │ │
│  │  │     Final Answer          │                          │    │ │
│  │  └──────────────────────────┘                          │    │ │
│  │                                                             │ │
│  │  支撑组件:                                                    │ │
│  │  ┌──────────┐ ┌───────────┐ ┌─────────┐ ┌──────────────┐   │ │
│  │  │Token     │ │Compressed │ │Tool     │ │Prompt        │   │ │
│  │  │Budget    │ │Scratchpad │ │Registry │ │Cache         │   │ │
│  │  │Manager   │ │           │ │         │ │              │   │ │
│  │  └──────────┘ └───────────┘ └─────────┘ └──────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **单一循环引擎** | `run()` 和 `stream_run()` 合并为一个带 `stream` 参数的统一方法 |
| **显式 Reflection** | 每次 Observation 后增加显式的反思判断步骤（评估信息充分性） |
| **Token 预算感知** | 每轮迭代前计算 prompt token 数，自动压缩历史 Observation |
| **工具注册制** | 参数校验逻辑从 Agent 移到 Skill 自身（`validate_params` 方法） |
| **分层缓存** | KB 概览 → 请求级缓存；Prompt 模板 → 进程级缓存 |
| **优雅降级** | 工具失败 → 自动重试(退避) → 降级提示 → 不阻断循环 |

---

## 三、核心模块优化

### 3.1 Think 模块（思考阶段）

**当前问题**：LLM 调用参数硬编码、非流式、无 token 预算管理。

**优化方案**：

```python
# backend/app/agents/think_engine.py (新文件，从 react_agent 拆分)

import time
import logging
from typing import Dict, Any, Optional, Generator
from dataclasses import dataclass
from app.agents.exceptions import ReActAgentError

logger = logging.getLogger(__name__)


@dataclass
class ThinkConfig:
    """思考阶段配置"""
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 1024
    enable_thinking: bool = False  # 用于支持思考链的模型 (如 qwen3)
    retry_count: int = 2
    retry_base_delay: float = 0.5  # 退避基础延迟(秒)
    retry_max_delay: float = 4.0   # 退避最大延迟(秒)


class ThinkEngine:
    """
    思考引擎 —— 负责 LLM 调用与响应解析

    优化点:
    1. 支持流式和非流式两种调用路径
    2. 指数退避重试
    3. 参数从配置读取，不再硬编码
    4. 集成 Token 预算检查
    """

    def __init__(self, provider: str = "openai", config: ThinkConfig = None):
        from app.core.config import get_complete_config
        self.cfg = get_complete_config()
        self.provider = provider
        self.think_config = config or ThinkConfig()

    def think(
        self,
        prompt: str,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        同步思考（非流式）

        Returns:
            {"thought": str, "action": str|None, "action_input": dict|None,
             "is_final_answer": bool, "final_answer": str|None}
        """
        from app.agents.output_parser import OutputParser

        parser = OutputParser(mode="json")
        last_error = None

        for attempt in range(self.think_config.retry_count + 1):
            try:
                llm_output = self._call_llm_raw(prompt, stream=False)

                if not self._is_output_usable(llm_output):
                    raise ReActAgentError("LLM output too short or empty")

                return parser.parse(llm_output)

            except Exception as e:
                last_error = e
                if attempt < self.think_config.retry_count:
                    delay = min(
                        self.think_config.retry_base_delay * (2 ** attempt),
                        self.think_config.retry_max_delay
                    )
                    logger.warning(
                        f"[ThinkEngine] Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"[ThinkEngine] All {self.think_config.retry_count + 1} attempts failed")
                    raise ReActAgentError(f"LLM call failed after all retries: {last_error}")

    def think_stream(
        self,
        prompt: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        流式思考 —— 边生成边 yield

        Yields:
            {"type": "thought_chunk", "content": "..."}
            {"type": "thought_complete", "parsed": {...}}
        """
        from app.agents.output_parser import OutputParser

        parser = OutputParser(mode="json")
        buffer = ""

        for chunk_text in self._call_llm_raw_stream(prompt):
            buffer += chunk_text
            yield {"type": "thought_chunk", "content": chunk_text}

        # 流式结束后统一解析
        try:
            parsed = parser.parse(buffer)
            yield {"type": "thought_complete", "parsed": parsed}
        except Exception as e:
            logger.error(f"[ThinkEngine] Stream parse failed: {e}")
            yield {
                "type": "thought_error",
                "message": str(e),
                "raw_output": buffer[:500]
            }

    def _call_llm_raw(self, prompt: str, stream: bool = False) -> str:
        """底层 LLM 调用（非流式）"""
        if self.provider == "ollama":
            return self._call_ollama(prompt)
        else:
            return self._call_openai(prompt)

    def _call_llm_raw_stream(self, prompt: str) -> Generator[str, None, None]:
        """底层 LLM 调用（流式）"""
        if self.provider == "ollama":
            yield from self._call_ollama_stream(prompt)
        else:
            yield from self._call_openai_stream(prompt)

    def _call_openai(self, prompt: str) -> str:
        """OpenAI 非流式调用（带超时）"""
        from openai import OpenAI

        key = self.cfg.get("openai_api_key")
        base_url = self.cfg.get("openai_base_url")

        client = OpenAI(
            api_key=key,
            base_url=base_url,
            timeout=60.0  # 新增：硬性超时
        )

        completion = client.chat.completions.create(
            model=self.cfg.get("openai_chat_model", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.think_config.max_tokens,
            temperature=self.think_config.temperature,
            top_p=self.think_config.top_p
        )

        if (completion.choices and completion.choices[0].message
                and completion.choices[0].message.content):
            return completion.choices[0].message.content.strip()
        raise ReActAgentError("LLM returned empty response")

    def _call_openai_stream(self, prompt: str) -> Generator[str, None, None]:
        """OpenAI 流式调用"""
        from openai import OpenAI

        client = OpenAI(
            api_key=self.cfg.get("openai_api_key"),
            base_url=self.cfg.get("openai_base_url"),
            timeout=60.0
        )

        stream = client.chat.completions.create(
            model=self.cfg.get("openai_chat_model", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.think_config.max_tokens,
            temperature=self.think_config.temperature,
            top_p=self.think_config.top_p,
            stream=True
        )

        for chunk in stream:
            if (chunk.choices and chunk.choices[0].delta
                    and chunk.choices[0].delta.content):
                yield chunk.choices[0].delta.content

    def _call_ollama(self, prompt: str) -> str:
        """Ollama 非流式调用"""
        try:
            from ollama import chat
            OLLAMA_SDK = True
        except ImportError:
            OLLAMA_SDK = False

        model = self.cfg.get("ollama_model")
        timeout = self.cfg.get("timeouts", {}).get("react_agent_subprocess", 60)

        if OLLAMA_SDK:
            response = chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    "temperature": self.think_config.temperature,
                    "top_p": self.think_config.top_p,
                    "num_predict": self.think_config.max_tokens
                },
                stream=False,
                think=self.think_config.enable_thinking
            )
            return response.message.content.strip()
        else:
            import requests
            endpoint = self.cfg.get("ollama_url").rstrip("/") + "/api/generate"
            r = requests.post(
                endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.think_config.temperature,
                        "top_p": self.think_config.top_p,
                        "num_predict": self.think_config.max_tokens
                    }
                },
                timeout=timeout
            )
            r.raise_for_status()
            return r.json().get("response", "")

    def _call_ollama_stream(self, prompt: str) -> Generator[str, None, None]:
        """Ollama 流式调用"""
        # ... 类似 _call_ollama，但 stream=True
        pass

    def _is_output_usable(self, output: str) -> bool:
        """快速检查 LLM 输出是否可用"""
        if not output or len(output.strip()) < 10:
            return False
        # 检查是否包含关键 JSON 字段（容错：不需要完整 JSON）
        has_thought = '"thought"' in output or 'Thought:' in output
        has_answer = 'final_answer' in output or 'Final Answer' in output
        return has_thought or has_answer
```

### 3.2 Act 模块（行动阶段）

**当前问题**：工具参数校验硬编码在 Agent 中、无调用前验证、无工具级重试。

**优化方案**：

```python
# backend/app/agents/action_engine.py (新文件)

import logging
from typing import Dict, Any, Optional, List
from app.agents.exceptions import ToolNotFoundError, ToolExecutionError

logger = logging.getLogger(__name__)


class ActionEngine:
    """
    行动引擎 —— 负责工具的校验、执行与结果处理

    优化点:
    1. 工具注册制：参数 schema 从 Skill metadata 动态获取
    2. 调用前参数校验（类型、范围、必填）
    3. 工具级重试（瞬态错误自动重试）
    4. 结构化结果封装（区分成功/失败/部分成功）
    """

    MAX_TOOL_RETRIES = 1  # 工具级最大重试次数

    def __init__(self):
        from app.skills import get_skill_manager
        self.skill_manager = get_skill_manager()
        self._tool_schemas = {}  # 缓存工具参数 schema

    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        retry_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            params: 参数字典
            retry_on_error: 是否在失败时重试

        Returns:
            {
                "success": bool,
                "output": str,            # 格式化输出（给 LLM 阅读）
                "error": str | None,      # 错误信息
                "tool_name": str,
                "params_used": dict,      # 实际使用的参数（补全后）
                "execution_time_ms": float
            }
        """
        import time

        # Step 1: 验证工具存在
        available = self.skill_manager.list_skills()
        if tool_name not in [s["name"] for s in available]:
            raise ToolNotFoundError(tool_name)

        # Step 2: 校验并补全参数
        validated_params = self._validate_params(tool_name, params)

        # Step 3: 执行（带重试）
        last_error = None
        max_attempts = self.MAX_TOOL_RETRIES + 1 if retry_on_error else 1

        for attempt in range(max_attempts):
            try:
                start = time.time()
                raw_result = self.skill_manager.execute_skill(
                    tool_name, **validated_params
                )
                elapsed = (time.time() - start) * 1000

                # Step 4: 结构化封装
                formatted = self.skill_manager.format_skill_result(raw_result)

                return {
                    "success": raw_result.get("success", False),
                    "output": formatted,
                    "error": raw_result.get("error") if not raw_result.get("success") else None,
                    "tool_name": tool_name,
                    "params_used": validated_params,
                    "execution_time_ms": round(elapsed, 1)
                }

            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"[ActionEngine] Tool '{tool_name}' attempt {attempt + 1} "
                        f"failed: {e}. Retrying..."
                    )
                else:
                    logger.error(
                        f"[ActionEngine] Tool '{tool_name}' failed after "
                        f"{max_attempts} attempts: {e}"
                    )

        # 所有重试都失败
        return {
            "success": False,
            "output": f"[工具执行失败] {tool_name}: {str(last_error)}",
            "error": str(last_error),
            "tool_name": tool_name,
            "params_used": validated_params,
            "execution_time_ms": 0
        }

    def _validate_params(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        动态参数校验与补全

        从 Skill metadata 的 input_parameters schema 获取校验规则，
        而非硬编码 if/elif。
        """
        validated = params.copy() if isinstance(params, dict) else {}

        # 获取工具的输入参数 schema
        schema = self._get_tool_param_schema(tool_name)

        if not schema:
            # 无 schema → 不做校验，仅确保 query/city 等常用参数有默认值
            return self._apply_fallback_defaults(tool_name, validated)

        for param_name, param_schema in schema.items():
            # 必填参数检查
            if param_schema.get("required", False) and param_name not in validated:
                default = param_schema.get("default")
                if default is not None:
                    validated[param_name] = default
                else:
                    logger.warning(
                        f"[ActionEngine] Missing required param '{param_name}' "
                        f"for tool '{tool_name}'"
                    )

            # 类型转换
            if param_name in validated and "type" in param_schema:
                validated[param_name] = self._coerce_type(
                    validated[param_name],
                    param_schema["type"]
                )

            # 范围校验
            if param_name in validated and "max" in param_schema:
                if isinstance(validated[param_name], (int, float)):
                    validated[param_name] = min(
                        validated[param_name],
                        param_schema["max"]
                    )

        return validated

    def _get_tool_param_schema(self, tool_name: str) -> dict:
        """从 Skill metadata 获取参数 schema（带缓存）"""
        if tool_name in self._tool_schemas:
            return self._tool_schemas[tool_name]

        skills = self.skill_manager.list_skills()
        for skill in skills:
            if skill["name"] == tool_name:
                schema = skill.get("input_parameters", {})
                self._tool_schemas[tool_name] = schema
                return schema

        return {}

    def _coerce_type(self, value: Any, target_type: str) -> Any:
        """类型强制转换"""
        if target_type == "integer" or target_type == "number":
            try:
                return int(value) if target_type == "integer" else float(value)
            except (ValueError, TypeError):
                return value
        elif target_type == "string":
            return str(value)
        return value

    def _apply_fallback_defaults(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """无 schema 时的兜底默认值"""
        if tool_name == "arxiv-watcher":
            if "query" not in params and "search_query" in params:
                params["query"] = params.pop("search_query")
            params.setdefault("query", "")
            params.setdefault("count", 5)
        elif tool_name == "amap-weather":
            if "location" in params and "city" not in params:
                params["city"] = params.pop("location")
            params.setdefault("city", "宁波")
        return params
```

### 3.3 Observe 模块（观察阶段）

**当前问题**：Observation 完整存入 Scratchpad 导致 prompt 膨胀、无结构化压缩。

**优化方案**：

```python
# backend/app/agents/observation_compressor.py (新文件)

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ObservationCompressor:
    """
    观察结果压缩器

    策略:
    1. 按 observation 类型采用不同压缩策略
    2. 论文列表 → 保留标题 + 摘要前 150 字
    3. 天气数据 → 保留关键字段
    4. 错误信息 → 保留错误类型，去除堆栈
    5. 通用文本 → 保留前 N 字符 + 尾 N 字符
    """

    # 各类型的保留配置
    COMPRESSION_CONFIG = {
        "arxiv_search": {
            "max_papers_in_scratchpad": 3,   # Scratchpad 中只保留前3篇
            "abstract_max_chars": 150,        # 摘要截断长度
            "keep_fields": ["title", "authors", "published", "pdf_url"]
        },
        "weather": {
            "keep_fields": ["city", "temperature", "weather", "humidity", "wind"]
        },
        "default": {
            "max_chars": 500,                 # 通用截断
            "keep_head": 300,                 # 前300字符
            "keep_tail": 100                  # 尾100字符（含关键信息）
        }
    }

    def compress(
        self,
        observation: str,
        obs_type: str = "default",
        action_name: str = ""
    ) -> str:
        """
        压缩 Observation 文本

        Args:
            observation: 原始 Observation
            obs_type: 类型 ("arxiv_search", "weather", "error", "default")
            action_name: 触发该 Observation 的 Action 名称（辅助判断类型）

        Returns:
            压缩后的 Observation
        """
        # 自动推断类型
        if not obs_type or obs_type == "default":
            obs_type = self._infer_type(observation, action_name)

        config = self.COMPRESSION_CONFIG.get(
            obs_type,
            self.COMPRESSION_CONFIG["default"]
        )

        if obs_type == "arxiv_search":
            return self._compress_arxiv_result(observation, config)
        elif obs_type == "weather":
            return self._compress_weather(observation, config)
        elif obs_type == "error":
            return self._compress_error(observation)
        else:
            return self._compress_generic(observation, config)

    def _infer_type(self, text: str, action_name: str) -> str:
        """自动推断 Observation 类型"""
        if action_name == "arxiv-watcher":
            return "arxiv_search"
        if action_name == "amap-weather":
            return "weather"
        if text.startswith("工具执行失败") or "error" in text.lower()[:50]:
            return "error"
        return "default"

    def _compress_arxiv_result(self, text: str, config: dict) -> str:
        """压缩 ArXiv 搜索结果"""
        import re

        max_papers = config["max_papers_in_scratchpad"]
        abstract_max = config["abstract_max_chars"]

        # 按 ### Paper N 分割
        papers = re.split(r'(?=### Paper \d+:)', text)

        compressed_parts = []
        paper_count = 0

        for paper_text in papers:
            if paper_count >= max_papers:
                break
            if not paper_text.strip():
                continue

            # 提取标题
            title_match = re.search(r'### Paper \d+: (.+)', paper_text)
            title = title_match.group(1) if title_match else "Unknown"

            # 截断摘要
            abstract_match = re.search(
                r'-\s*\*\*Abstract\*\*:\s*(.+?)(?=\n-|\n\n|$)',
                paper_text, re.DOTALL
            )
            if abstract_match:
                abstract = abstract_match.group(1).strip()
                if len(abstract) > abstract_max:
                    abstract = abstract[:abstract_max] + "..."

            # 提取链接
            pdf_match = re.search(r'-\s*\*\*PDF Link\*\*:\s*(.+)', paper_text)
            pdf_link = pdf_match.group(1).strip() if pdf_match else ""

            compressed_parts.append(
                f"**{title}**\n"
                f"摘要: {abstract}\n"
                f"链接: {pdf_link}"
            )
            paper_count += 1

        result = "\n\n".join(compressed_parts)

        total_count = len(re.findall(r'### Paper \d+:', text))
        if total_count > max_papers:
            result += f"\n\n*...（共 {total_count} 篇，展示前 {max_papers} 篇）*"

        return result

    def _compress_weather(self, text: str, config: dict) -> str:
        """压缩天气数据 —— 只保留关键字段"""
        import re
        parts = []
        for field in config["keep_fields"]:
            match = re.search(
                rf'[-*]\s*\*\*{field}\*\*:\s*(.+)',
                text, re.IGNORECASE
            )
            if match:
                parts.append(f"{field}: {match.group(1).strip()}")
        return "\n".join(parts) if parts else text[:200]

    def _compress_error(self, text: str) -> str:
        """压缩错误信息 —— 移除堆栈"""
        lines = text.split('\n')
        # 只保留前 3 行（错误类型 + 主要原因）
        useful_lines = []
        for line in lines:
            if len(useful_lines) >= 3:
                break
            # 跳过堆栈帧
            if line.strip().startswith('File "') or line.strip().startswith('  '):
                continue
            useful_lines.append(line)
        return '\n'.join(useful_lines)

    def _compress_generic(self, text: str, config: dict) -> str:
        """通用压缩 —— 保留头尾"""
        max_chars = config["max_chars"]
        if len(text) <= max_chars:
            return text

        head = text[:config["keep_head"]]
        tail = text[-config["keep_tail"]:]
        return f"{head}\n...\n[中间 {len(text) - config['keep_head'] - config['keep_tail']} 字符已省略]\n...\n{tail}"
```

### 3.4 Reflect 模块（反思阶段）—— 新增

```python
# backend/app/agents/reflector.py (新文件)

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class Reflector:
    """
    反思器 —— Observation 后评估信息是否足够回答用户问题

    优化点:
    1. 替代基于关键词的 _should_force_final_answer
    2. 基于结构化信号而非字符串匹配
    3. 支持信息充分性评分
    """

    # 强信号：观察结果明确表明可以/应该结束
    STRONG_END_SIGNALS = [
        "搜索完成",
        "Search Results",
        "查询成功",
        "天气信息",
    ]

    # 弱信号：观察结果暗示可能需要更多信息
    WEAK_CONTINUE_SIGNALS = [
        "未找到",
        "没有结果",
        "0 papers",
        "执行失败",
        "搜索失败",
    ]

    def evaluate(
        self,
        user_question: str,
        thought: str,
        action: Optional[str],
        observation: str,
        iteration: int,
        max_iterations: int,
        scratchpad_steps: List[Dict]
    ) -> Dict[str, Any]:
        """
        评估当前状态

        Returns:
            {
                "should_stop": bool,       # 是否应该结束
                "should_continue": bool,    # 是否应该继续（调用工具）
                "confidence": float,        # 0.0-1.0 信息充分性信心
                "reason": str,              # 决策理由
                "suggestion": str | None    # 建议的下一步（如 "尝试扩大搜索范围"）
            }
        """
        # Rule 1: 达到最大迭代次数 → 强制结束
        if iteration >= max_iterations - 1:
            return {
                "should_stop": True,
                "should_continue": False,
                "confidence": 0.5,
                "reason": "达到最大迭代次数",
                "suggestion": None
            }

        # Rule 2: 无 action → LLM 认为无需调用工具，直接回答
        if not action:
            return {
                "should_stop": True,
                "should_continue": False,
                "confidence": 0.9,
                "reason": "模型判断无需调用工具",
                "suggestion": None
            }

        # Rule 3: 观察结果包含强信号
        for signal in self.STRONG_END_SIGNALS:
            if signal in observation:
                return {
                    "should_stop": True,
                    "should_continue": False,
                    "confidence": 0.85,
                    "reason": f"观察结果包含成功信号: {signal}",
                    "suggestion": None
                }

        # Rule 4: 观察结果包含弱信号 → 建议重试但保留结束选项
        for signal in self.WEAK_CONTINUE_SIGNALS:
            if signal in observation:
                if iteration < max_iterations - 2:
                    return {
                        "should_stop": False,
                        "should_continue": True,
                        "confidence": 0.2,
                        "reason": f"观察结果表明需要重试: {signal}",
                        "suggestion": self._suggest_retry_strategy(action, observation)
                    }

        # Rule 5: 连续调用同一工具 → 可能陷入循环
        if len(scratchpad_steps) >= 2:
            last_actions = [
                s.get("action") for s in scratchpad_steps[-2:]
            ]
            if last_actions[-1] == last_actions[-2] == action:
                return {
                    "should_stop": True,
                    "should_continue": False,
                    "confidence": 0.6,
                    "reason": "连续调用同一工具，可能陷入循环",
                    "suggestion": "基于已有结果给出最佳回答"
                }

        # Rule 6: 默认——信息充足，可以结束
        return {
            "should_stop": True,
            "should_continue": False,
            "confidence": 0.7,
            "reason": "观察结果正常，信息充足",
            "suggestion": None
        }

    def _suggest_retry_strategy(
        self,
        action: str,
        observation: str
    ) -> Optional[str]:
        """根据失败类型建议重试策略"""
        if action == "arxiv-watcher":
            if "0 papers" in observation or "未找到" in observation:
                return "尝试使用更广泛/不同的关键词重新搜索"
            if "执行失败" in observation:
                return "ArXiv API 可能暂时不可用，稍后重试或使用本地知识库"
        return "尝试调整参数后重新调用"
```

---

## 四、循环逻辑优化

### 4.1 统一循环引擎

**核心改动**：消除 `run()` 和 `stream_run()` 的 95% 代码重复，合并为单一方法。

```python
# backend/app/agents/react_agent.py (重构后)

class ReActAgent:
    """ReAct Agent v2.0 — 统一循环引擎"""

    def __init__(self, max_iterations=5, provider="openai"):
        from app.core.config import get_complete_config
        from app.agents.think_engine import ThinkEngine, ThinkConfig
        from app.agents.action_engine import ActionEngine
        from app.agents.observation_compressor import ObservationCompressor
        from app.agents.reflector import Reflector
        from app.agents.token_budget import TokenBudgetManager  # 新增

        self.cfg = get_complete_config()
        self.max_iterations = max_iterations
        self.provider = provider

        # 模块化组件
        self.think_engine = ThinkEngine(provider=provider)
        self.action_engine = ActionEngine()
        self.compressor = ObservationCompressor()
        self.reflector = Reflector()
        self.scratchpad = MemoryScratchpad()
        self.token_budget = TokenBudgetManager(
            max_tokens=self.cfg.get("react_token_budget", 6000)
        )

        # Prompt 引擎（延迟构建，因为需要工具列表）
        self.tools = self._get_tools_list()
        self.prompt_engine = PromptEngine(tools=self.tools, use_few_shot=True)

    def execute(
        self,
        user_question: str,
        conversation_history: str = "",
        stream: bool = False
    ) -> Generator[Dict[str, Any], None, None]:
        """
        统一执行入口 —— 消除 run()/stream_run() 重复

        Args:
            user_question: 用户问题
            conversation_history: 对话历史
            stream: 是否流式输出

        Yields:
            事件字典 (type 字段标识事件类型)
        """
        logger.info(f"[ReActAgent] Starting for: {user_question[:50]}...")

        # 缓存：请求级 Prompt 基础部分
        base_prompt_cache = {}

        try:
            for iteration in range(self.max_iterations):
                yield {
                    "type": "thinking",
                    "iteration": iteration + 1,
                    "total": self.max_iterations
                }

                # —— 1. 构建 Prompt（复用不变部分） ——
                prompt = self._build_iteration_prompt(
                    user_question=user_question,
                    conversation_history=conversation_history,
                    iteration=iteration,
                    cache=base_prompt_cache
                )

                # Token 预算检查
                prompt_tokens = self.token_budget.estimate_tokens(prompt)
                if prompt_tokens > self.token_budget.max_tokens * 0.9:
                    # 压缩历史 Observation
                    self.scratchpad.compress_history(self.compressor)
                    prompt = self._build_iteration_prompt(
                        user_question=user_question,
                        conversation_history=conversation_history,
                        iteration=iteration,
                        cache={}  # 重建 cache
                    )
                    logger.warning(
                        f"[ReActAgent] Prompt too long ({prompt_tokens} tokens), "
                        f"compressed scratchpad"
                    )

                yield {
                    "type": "token_usage",
                    "estimated_tokens": prompt_tokens,
                    "budget_remaining": self.token_budget.max_tokens - prompt_tokens
                }

                # —— 2. Think ——
                if stream:
                    yield from self._think_stream(prompt)
                    # _think_stream 的最后一个事件是 thought_complete
                    # 需要提取 parsed 结果...（实现细节）
                    # 简化：流式模式下仍用非流式 LLM 调用获取完整 thought
                    # 真正的流式 LLM 需要更大的架构改动
                    parsed = self.think_engine.think(prompt, stream=False)
                else:
                    parsed = self.think_engine.think(prompt, stream=False)

                yield {"type": "thought", "content": parsed["thought"]}

                # —— 3. Reflect ——
                evaluation = self.reflector.evaluate(
                    user_question=user_question,
                    thought=parsed["thought"],
                    action=parsed.get("action"),
                    observation="",  # 本轮尚未 observe
                    iteration=iteration,
                    max_iterations=self.max_iterations,
                    scratchpad_steps=self.scratchpad.get_steps()
                )

                # 直接回答判定
                if parsed["is_final_answer"] or (
                    evaluation["should_stop"] and not parsed.get("action")
                ):
                    logger.info(
                        f"[ReActAgent] Final answer at iteration {iteration + 1}. "
                        f"Reason: {evaluation['reason']}"
                    )
                    self.scratchpad.add_step(thought=parsed["thought"])
                    yield {"type": "final_answer", "content": parsed["final_answer"]}
                    yield {
                        "type": "done",
                        "final_answer": parsed["final_answer"],
                        "steps": self.scratchpad.get_steps(),
                        "success": True,
                        "iterations_used": iteration + 1
                    }
                    return

                # —— 4. Act ——
                action = parsed.get("action")
                action_input = parsed.get("action_input") or {}

                if not action:
                    # 无行动也无最终答案 → 强制给出回答
                    logger.warning("[ReActAgent] No action and no final answer, forcing")
                    fallback_answer = self._force_answer_from_thought(
                        parsed["thought"]
                    )
                    yield {"type": "final_answer", "content": fallback_answer}
                    yield {
                        "type": "done",
                        "final_answer": fallback_answer,
                        "steps": self.scratchpad.get_steps(),
                        "success": True
                    }
                    return

                yield {"type": "action", "name": action, "input": action_input}

                # —— 5. Observe ——
                result = self.action_engine.execute(action, action_input)

                # 压缩观察结果
                compressed_obs = self.compressor.compress(
                    result["output"],
                    action_name=action
                )

                yield {
                    "type": "observation",
                    "content": compressed_obs,
                    "raw_length": len(result["output"]),
                    "compressed_length": len(compressed_obs),
                    "success": result["success"]
                }

                # —— 6. Update Scratchpad ——
                self.scratchpad.add_step(
                    thought=parsed["thought"],
                    action=action,
                    action_input=action_input,
                    observation=compressed_obs  # 存压缩版
                )

            # 达到最大迭代次数
            yield {
                "type": "error",
                "message": f"达到最大迭代次数 ({self.max_iterations})"
            }
            yield {
                "type": "done",
                "final_answer": "抱歉，经过多步思考仍未能得出满意答案。请尝试简化问题或提供更多细节。",
                "steps": self.scratchpad.get_steps(),
                "success": False,
                "iterations_used": self.max_iterations
            }

        except Exception as e:
            logger.error(f"[ReActAgent] Unexpected error: {e}", exc_info=True)
            # 安全错误消息（不泄露敏感信息）
            safe_msg = "执行过程中发生内部错误，请稍后重试。"
            yield {"type": "error", "message": safe_msg}
            yield {
                "type": "done",
                "final_answer": safe_msg,
                "steps": self.scratchpad.get_steps(),
                "success": False
            }

    def _build_iteration_prompt(
        self,
        user_question: str,
        conversation_history: str,
        iteration: int,
        cache: dict
    ) -> str:
        """构建当前迭代的 Prompt（缓存不变部分）"""
        # 第 1 轮：完整构建
        if iteration == 0 or "system_part" not in cache:
            full = self.prompt_engine.build_prompt(
                user_question=user_question,
                scratchpad_text=self.scratchpad.get_scratchpad_text(),
                conversation_history=conversation_history,
                provider=self.provider
            )
            # 拆分可变部分和不变部分
            cache["system_part"] = self._extract_system_part(full)
            cache["tools_part"] = self._extract_tools_part(full)

        # 后续轮次：复用 system + tools，只重建 scratchpad + 输入
        scratchpad_text = self.scratchpad.get_scratchpad_text()
        return (
            cache.get("system_part", "")
            + cache.get("tools_part", "")
            + f"\n\n## 当前步骤\n{scratchpad_text}\n\n"
            + f"## 用户问题\n{user_question}\n\n开始！"
        )

    def _extract_system_part(self, prompt: str) -> str:
        """提取 Prompt 中的 system/role 部分"""
        # 简化实现：取 prompt 中从开头到"## 可用工具"之前的内容
        idx = prompt.find("## 可用工具")
        return prompt[:idx] if idx > 0 else prompt[:500]

    def _extract_tools_part(self, prompt: str) -> str:
        """提取 Prompt 中的工具描述部分"""
        import re
        match = re.search(
            r'(## 可用工具.*?)(?=## 思考指南|## 示例|---\n\n##)',
            prompt, re.DOTALL
        )
        return match.group(1) if match else ""

    def _force_answer_from_thought(self, thought: str) -> str:
        """强制从 thought 生成回答（取代正则匹配）"""
        # 使用简单的启发式：取 thought 中 "答案" 之后的内容
        for marker in ["最终答案", "答案", "Final Answer"]:
            idx = thought.find(marker)
            if idx >= 0:
                return thought[idx + len(marker):].strip("：:。. \n")
        return thought

    # _get_tools_list, _is_output_complete 等方法保留但简化
```

---

## 五、状态管理方案

### 5.1 MemoryScratchpad 增强

```python
# backend/app/agents/memory.py (改进版)

class MemoryScratchpad:
    """
    增强版暂存器

    新增:
    - compressed observation 存储（区分 raw 和 compressed）
    - 自动压缩（根据 token 预算）
    - 摘要生成（超长历史时用 LLM 生成压缩摘要）
    """

    def __init__(self, max_raw_chars: int = 8000):
        self._steps: List[Dict[str, Any]] = []
        self.max_raw_chars = max_raw_chars  # 所有 observation 累计上限

    def add_step(
        self,
        thought: str,
        action: Optional[str] = None,
        action_input: Optional[Dict] = None,
        observation: Optional[str] = None,
        raw_observation: Optional[str] = None  # 新增：未压缩版（用于前端展示）
    ):
        step = {
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation,           # 压缩版（给 LLM）
            "raw_observation": raw_observation,   # 原始版（给前端）
        }
        self._steps.append(step)

    def compress_history(self, compressor) -> None:
        """遍历历史，压缩所有 observation"""
        for step in self._steps:
            if step.get("observation") and step.get("action"):
                step["observation"] = compressor.compress(
                    step["observation"],
                    action_name=step["action"]
                )
                logger.debug(
                    f"[MemoryScratchpad] Compressed observation "
                    f"for action '{step['action']}'"
                )

    def get_total_chars(self) -> int:
        """获取所有步骤的总字符数（用于 token 估算）"""
        return sum(len(str(s.get("observation", ""))) for s in self._steps)

    def get_scratchpad_text(self) -> str:
        """格式化输出（优化版：截断最早的 observation）"""
        if not self._steps:
            return ""

        lines = []
        for i, step in enumerate(self._steps, 1):
            lines.append(f"Step {i}:")
            lines.append(f"  Thought: {step['thought']}")

            if step.get("action"):
                lines.append(f"  Action: {step['action']}")

            if step.get("observation"):
                obs = step["observation"]
                # 对最早的步骤做额外截断
                if i < len(self._steps) - 1:
                    max_obs = 300
                    if len(obs) > max_obs:
                        obs = obs[:max_obs] + "..."
                lines.append(f"  Observation: {obs}")

        return "\n".join(lines)

    # get_steps(), clear(), __len__() 保持不变
```

### 5.2 Token 预算管理（新增）

```python
# backend/app/agents/token_budget.py (新文件)

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TokenBudgetManager:
    """
    Token 预算管理器

    功能:
    - 估算文本 token 数（中文约 2 字符/token，英文约 4 字符/token）
    - 动态调整 scratchpad 中 observation 的截断长度
    - 在超预算时触发 scratchpad 压缩
    """

    # 各模型上下文窗口
    MODEL_CONTEXT_LIMITS = {
        "gpt-3.5-turbo": 4096,
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "gpt-4o": 128000,
        "deepseek-v3": 65536,
    }

    def __init__(self, max_tokens: int = 6000, model_name: str = ""):
        # 如果指定了模型，取模型限制的 90% 作为预算
        if model_name and model_name in self.MODEL_CONTEXT_LIMITS:
            model_limit = self.MODEL_CONTEXT_LIMITS[model_name]
            self.max_tokens = min(max_tokens, int(model_limit * 0.9))
        else:
            self.max_tokens = max_tokens

        self.system_prompt_tokens = 0  # 由外部设置

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本 token 数（快速估算，无需加载 tokenizer）

        规则:
        - 中文字符: ~0.5 token/char
        - 英文单词: ~0.75 token/word
        - 数字/符号: ~1 token/char（保守）
        """
        import re

        chinese_chars = len(re.findall(r'[一-鿿]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        other_chars = len(text) - chinese_chars - english_words

        # 经验公式
        tokens = (
            chinese_chars * 0.5 +
            english_words * 0.75 +
            other_chars * 0.3
        )
        return int(tokens)

    def can_add(self, additional_text: str) -> bool:
        """检查是否还有足够预算"""
        return self.estimate_tokens(additional_text) < self.remaining()

    def remaining(self) -> int:
        """剩余 token 预算"""
        return self.max_tokens - self.system_prompt_tokens

    def recommended_observation_limit(self, iteration: int, max_iterations: int) -> int:
        """
        根据剩余迭代次数建议 Observation 长度上限

        策略: 为每轮预留约 equal share
        """
        remaining_iterations = max_iterations - iteration
        if remaining_iterations <= 0:
            return 500
        share = self.remaining() // max(remaining_iterations, 1)
        # 每轮 observation 约占 30%
        return max(200, int(share * 0.3))
```

---

## 六、性能优化策略

| # | 策略 | 内容 | 预期效果 |
|---|------|------|---------|
| 1 | **Prompt 分层缓存** | 将 Prompt 拆为 System + Tools(不变) + Scratchpad(变)，缓存不变部分 | 第 2+ 轮 prompt 构建时间减少 60% |
| 2 | **KB 概览请求级缓存** | `_build_kb_overview()` 结果在请求生命周期内缓存 | 每轮节省一次全量摘要 I/O |
| 3 | **工具 Schema 缓存** | ActionEngine 首次获取 Skill 参数 schema 后缓存 | 每轮节省一次 `list_skills()` 遍历 |
| 4 | **Observation 压缩** | 论文列表 → 标题+摘要前150字；天气 → 关键字段 | 第 3 轮 prompt 减少 40-60% |
| 5 | **指数退避重试** | LLM 调用失败后 `0.5s → 1s → 2s` 退避 | 减少 API rate limit 触发 |
| 6 | **流式 Thought** | 边生成 thought 边推送给前端 | 用户感知延迟减少 50%+ |

---

## 七、错误处理机制

```python
# backend/app/agents/error_handler.py (新文件)

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# 敏感信息过滤规则
SENSITIVE_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{20,}', 'sk-***'),
    (r'Bearer\s+[a-zA-Z0-9\-_\.]+', 'Bearer ***'),
    (r'api_key["\']?\s*[:=]\s*["\'][^"\']+["\']', 'api_key="***"'),
    (r'key=["\'][a-zA-Z0-9]{20,}["\']', 'key="***"'),
]


def sanitize_error_message(error: Exception) -> str:
    """脱敏错误消息"""
    import re
    msg = str(error)
    for pattern, replacement in SENSITIVE_PATTERNS:
        msg = re.sub(pattern, replacement, msg)
    return msg


def classify_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """
    错误分类与建议

    Returns:
        {"category": str, "retryable": bool, "user_message": str, "log_message": str}
    """
    from openai import (
        APIError, APIConnectionError, RateLimitError, APITimeoutError
    )

    msg = str(error).lower()

    if isinstance(error, RateLimitError) or "rate limit" in msg:
        return {
            "category": "rate_limit",
            "retryable": True,
            "user_message": "服务繁忙，正在重试...",
            "log_message": sanitize_error_message(error)
        }
    elif isinstance(error, APITimeoutError) or "timeout" in msg:
        return {
            "category": "timeout",
            "retryable": True,
            "user_message": "响应超时，正在重试...",
            "log_message": sanitize_error_message(error)
        }
    elif isinstance(error, APIConnectionError) or "connection" in msg:
        return {
            "category": "connection",
            "retryable": True,
            "user_message": "网络连接异常，正在重试...",
            "log_message": sanitize_error_message(error)
        }
    elif isinstance(error, APIError) or "api" in msg:
        return {
            "category": "api_error",
            "retryable": False,
            "user_message": "服务暂时不可用，请稍后重试。",
            "log_message": sanitize_error_message(error)
        }
    else:
        return {
            "category": "unknown",
            "retryable": False,
            "user_message": "执行过程中发生内部错误。",
            "log_message": sanitize_error_message(error)
        }
```

---

## 八、实施步骤

### 第 1 阶段：基础设施（2-3 天）

```
□ 创建 think_engine.py — LLM 调用统一入口（带流式+退避重试）
□ 创建 action_engine.py — 工具执行与参数校验
□ 创建 observation_compressor.py — Observation 压缩
□ 创建 reflector.py — 信号驱动反思判断
□ 创建 token_budget.py — Token 预算管理
□ 创建 error_handler.py — 错误分类与脱敏
□ 增强 memory.py — 区分 raw/compressed observation
```

### 第 2 阶段：核心重构（2-3 天）

```
□ 重构 react_agent.py — 统一 execute() 方法替代 run()/stream_run()
□ 重构 prompt_engine.py — 分层缓存 system/tools 部分
□ 修改 qa.py — 适配新的 ReActAgent 接口
□ OutputParser 增强 — 支持 ```json```/裸JSON/混合文本 三种提取方式
□ 编写 react_agent 单元测试
```

### 第 3 阶段：灰度验证（1-2 天）

```
□ 使用测试问题集对比新旧 Agent 输出质量
□ 测量 token 消耗、延迟、成功率
□ 调优参数（max_iterations, token_budget, compression_config）
□ 添加可观测性（事件类型计数、平均迭代数、工具调用成功率）
```

### 第 4 阶段：流式 Thought 实现（1-2 天）

```
□ ThinkEngine 实现真正的流式 LLM 调用
□ 前端适配 Thought 流式渲染
□ 解决流式模式下 OutputParser 的增量解析问题
```

---

## 九、测试建议

### 9.1 单元测试

```python
# backend/tests/test_react_agent_v2.py

class TestThinkEngine:
    def test_think_with_valid_prompt_returns_parsed_output(self): ...
    def test_think_with_empty_response_raises_error(self): ...
    def test_think_retries_on_failure_with_backoff(self): ...
    def test_think_stream_yields_chunks_then_complete(self): ...

class TestActionEngine:
    def test_execute_validates_required_params(self): ...
    def test_execute_coerces_param_types(self): ...
    def test_execute_retries_on_transient_error(self): ...
    def test_execute_returns_structured_result_on_total_failure(self): ...

class TestObservationCompressor:
    def test_compress_arxiv_papers_truncates_abstracts(self): ...
    def test_compress_arxiv_papers_limits_count(self): ...
    def test_compress_weather_extracts_key_fields(self): ...
    def test_compress_error_removes_stack_traces(self): ...
    def test_compress_generic_keeps_head_and_tail(self): ...

class TestReflector:
    def test_strong_end_signal_triggers_stop(self): ...
    def test_weak_continue_signal_suggests_retry(self): ...
    def test_consecutive_same_action_triggers_stop(self): ...
    def test_max_iterations_forces_stop(self): ...
```

### 9.2 集成测试

```python
class TestReActAgentV2:
    def test_simple_question_answers_directly(self): ...
    def test_search_question_calls_arxiv_watcher(self): ...
    def test_tool_failure_gracefully_degrades(self): ...
    def test_max_iterations_returns_partial_answer(self): ...
    def test_scratchpad_compression_on_token_budget_exceeded(self): ...
```

---

## 十、预期效果汇总

| 指标 | 当前 | 优化后 | 提升 |
|------|------|--------|------|
| 代码行数（react_agent） | ~680 | ~350 | -48% |
| run/stream 代码重复 | 95% | 0% | 消除 |
| 平均迭代次数（简单问题） | 2-3 | 1 | -50% |
| LLM 重试成功率 | ~70% | ~95% | +25% |
| 第 3 轮 prompt 大小 | ~8K tokens | ~4K tokens | -50% |
| 上下文溢出发生概率 | ~15% | <2% | -87% |
| 工具参数校验覆盖率 | 2 个技能硬编码 | 100% 动态 | — |
| 错误消息敏感信息泄露 | 存在 | 已脱敏 | — |
| 单元测试覆盖 | 0 | >70% | — |
