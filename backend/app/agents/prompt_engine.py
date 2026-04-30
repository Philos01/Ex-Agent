"""
Prompt Engine - 提示词构建器
增强版：分层缓存 system/tools 部分，KB 概览请求级缓存
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    ReAct 提示词构建器

    增强功能:
    - 分层缓存：System + Tools 部分在请求生命周期内缓存
    - KB 概览请求级缓存：避免每轮迭代重复 I/O
    - Prompt 拆分为可变/不变部分
    """

    def __init__(self, tools: List[Dict[str, Any]] = None, use_few_shot: bool = True):
        self.tools = tools or []
        self.use_few_shot = use_few_shot

        self._system_prompt_cache = None
        self._tools_desc_cache = None
        self._kb_overview_cache = None
        self._few_shot_cache = None

        logger.debug(f"[PromptEngine] Initialized with {len(self.tools)} tools")

    def build_prompt(
        self,
        user_question: str,
        scratchpad_text: str = "",
        conversation_history: str = "",
        retrieved_context: str = "",
        provider: str = "openai"
    ) -> str:
        system_part = self.get_system_part()
        tools_part = self.get_tools_part()
        return self.build_prompt_from_parts(
            system_part=system_part,
            tools_part=tools_part,
            user_question=user_question,
            scratchpad_text=scratchpad_text,
            conversation_history=conversation_history,
            retrieved_context=retrieved_context,
            provider=provider,
        )

    def _get_system_prompt(self) -> str:
        if self._system_prompt_cache is not None:
            return self._system_prompt_cache
        self._system_prompt_cache = self._build_system_prompt()
        return self._system_prompt_cache

    def _get_tools_description(self) -> str:
        if self._tools_desc_cache is not None:
            return self._tools_desc_cache
        self._tools_desc_cache = self._build_tools_description()
        return self._tools_desc_cache

    def _get_few_shot_examples(self) -> str:
        if not self.use_few_shot:
            return ""
        if self._few_shot_cache is not None:
            return self._few_shot_cache
        self._few_shot_cache = self._build_few_shot_examples()
        return self._few_shot_cache

    def get_system_part(self) -> str:
        if self._system_prompt_cache is None:
            self._system_prompt_cache = self._build_system_prompt()
        return self._system_prompt_cache

    def get_tools_part(self) -> str:
        if self._tools_desc_cache is None:
            self._tools_desc_cache = self._build_tools_description()
        tools_desc = self._tools_desc_cache
        return f"\n## 可用工具\n{tools_desc}\n"

    def clear_request_cache(self) -> None:
        self._kb_overview_cache = None

    def build_prompt_from_parts(
        self,
        system_part: str,
        tools_part: str,
        user_question: str,
        scratchpad_text: str,
        conversation_history: str = "",
        retrieved_context: str = "",
        provider: str = "openai"
    ) -> str:
        beijing_tz = ZoneInfo('Asia/Shanghai')
        current_datetime = datetime.now(beijing_tz)
        current_date_str = current_datetime.strftime('%Y年%m月%d日')
        current_year = current_datetime.year

        few_shot = self._get_few_shot_examples()

        context_section = ""
        if retrieved_context:
            context_section = f"""
<retrieved_context>
{retrieved_context}
</retrieved_context>
"""

        return f"""{system_part}
{tools_part}
## 输出格式要求
请严格按照以下 JSON 格式输出：
```json
{{
  "thought": "你的思考过程",
  "action": "工具名称（或 null）",
  "action_input": "工具参数（JSON 对象）",
  "is_final_answer": false,
  "final_answer": null
}}
```

当你认为可以给出最终答案时：
```json
{{
  "thought": "我现在知道最终答案了。",
  "action": null,
  "action_input": null,
  "is_final_answer": true,
  "final_answer": "最终答案内容"
}}
```

## 思考指南
1. 先分析问题，决定是否需要调用工具
2. 每次只调用一个工具
3. 工具执行结果会作为 Observation 返回给你
4. 基于 Observation 继续思考下一步
5. 当信息足够时，给出最终答案

{few_shot}

---

## ⏰ 重要时间信息
- **当前日期**：{current_date_str}
- **当前年份**：{current_year}年

## 📥 输入数据区
<conversation_history>
{conversation_history}
</conversation_history>
{context_section}
<user_question>
{user_question}
</user_question>

{scratchpad_text}

开始！
"""

    def _build_system_prompt(self) -> str:
        kb_overview = self._build_kb_overview()
        return f"""# Role: 宁波大学 RS-NBU 课题组专属学术助理 (ReAct Agent)

## 👤 Profile
你是专门为**宁波大学 RS-NBU（Remote Sensing - Ningbo University）课题组**深度定制的 AI 学术助理，具备多步推理和工具调用能力。

你的核心职责：
1. **自主思考**：分析问题，制定解决计划
2. **工具调用**：根据需要调用合适的工具获取信息
3. **多步决策**：基于工具返回结果继续推理，直到得出最终答案
4. **严谨输出**：严格按照要求的格式输出

{kb_overview}
"""

    def _build_tools_description(self) -> str:
        if not self.tools:
            return "当前没有可用工具，请直接回答问题。"

        lines = []
        for i, tool in enumerate(self.tools, 1):
            name = tool.get("name", "unknown")
            desc = tool.get("description", "")
            lines.append(f"{i}. **{name}**: {desc}")

        return "\n".join(lines)

    def _build_kb_overview(self) -> str:
        if self._kb_overview_cache is not None:
            return self._kb_overview_cache

        try:
            from app.services.summary_store import get_summary_store
            from app.services.vector_store import get_collection_info

            store = get_summary_store()
            all_summaries = store.get_all_summaries()
            collection_info = get_collection_info()
            doc_count = collection_info.get("count", 0)

            parts = []
            parts.append(f"## 📊 知识库实际数据（实时统计）")
            parts.append(f"- 知识库中文档总数: {len(all_summaries)} 篇")
            parts.append(f"- 向量库中文档片段总数: {doc_count} 个")

            if all_summaries:
                parts.append("### 知识库中的完整文献列表：")
                for i, summary in enumerate(all_summaries, 1):
                    topics_str = "、".join(summary.key_topics[:3]) if summary.key_topics else "无"
                    parts.append(
                        f"{i}. **{summary.filename}** - 核心主题: {topics_str}"
                    )
                parts.append("⚠️ 严禁编造上述列表之外的任何文献或研究成果。")
            else:
                parts.append("⚠️ 当前知识库为空。")

            result = "\n".join(parts)
            self._kb_overview_cache = result
            return result
        except Exception:
            result = "⚠️ 知识库概览不可用，请基于检索结果谨慎回答。"
            self._kb_overview_cache = result
            return result

    def _build_few_shot_examples(self) -> str:
        return """## 重要指南 - 结果验证与调整

### 关键原则
1. **关注用户的量化需求**：如果用户要求"20篇论文"、"5个城市天气"等，必须检查工具返回结果是否满足数量要求
2. **不满足时的处理**：如果工具返回结果数量不足，应该：
   - 先尝试调整参数再次调用（例如：增大 max_results/count，扩大搜索关键词）
   - 或者告知用户实际数量并基于现有结果回答
3. **Observation 后必须决策**：每次看到 Observation 后，必须决定：
   - 要么给出 Final Answer
   - 要么再次调用 Action 调整参数
   - 不能停留在思考阶段
4. **参数灵活性**：你可以自由传递任何参数给工具，系统会自动处理。对于 arxiv-watcher：
   - 可以使用 `query` 或 `search_query` 作为搜索查询
   - 可以使用 `count` 或 `max_results` 作为最大结果数
   - 所有你传递的参数都会被正确传递给工具
5. **必须输出有效的 final_answer**：
   - final_answer 不能为 null、None、空字符串
   - 如果确实无法回答（如缺少数据、工具不可用），final_answer 应如实说明"当前无法获取该信息，因为..."
   - 绝不输出 `"final_answer": null` 或 `"final_answer": "None"`

---

## 示例（必须严格使用 JSON 格式输出！）

### 示例 1: 使用搜索工具（结果满足）
```json
{"thought": "用户想了解最新的遥感图像融合论文，我需要使用 arxiv-watcher 工具进行搜索。", "action": "arxiv-watcher", "action_input": {"query": "remote sensing image fusion", "max_results": 3}, "is_final_answer": false, "final_answer": ""}
```

Observation: [搜索结果返回3篇论文...]

```json
{"thought": "我已经获取到了3篇最新的论文信息，可以给出最终答案了。", "action": null, "action_input": null, "is_final_answer": true, "final_answer": "根据搜索结果，最新的遥感图像融合论文包括：1. **论文A**... 2. **论文B**... 3. **论文C**..."}
```

### 示例 2: 结果不满足，调整参数重试
```json
{"thought": "用户要求10篇关于drone的论文，我先用基本关键词搜索。", "action": "arxiv-watcher", "action_input": {"query": "drone", "max_results": 10}, "is_final_answer": false, "final_answer": ""}
```

Observation: 只返回5篇

```json
{"thought": "只搜到5篇，我需要扩大搜索范围，用更多同义词重试。", "action": "arxiv-watcher", "action_input": {"query": "drone OR UAV OR unmanned aerial vehicle", "max_results": 10}, "is_final_answer": false, "final_answer": ""}
```

Observation: 返回7篇

```json
{"thought": "还是没到10篇，但已是全部结果，基于现有7篇回答并说明实际情况。", "action": null, "action_input": null, "is_final_answer": true, "final_answer": "根据当前检索结果，共找到7篇与drone相关的论文（未达到您要求的10篇）。以下是相关论文：1. ..."}
```

### 示例 3: 不需要工具，直接回答
```json
{"thought": "这是一个关于我身份的问题，不需要调用任何工具，可以直接回答。", "action": null, "action_input": null, "is_final_answer": true, "final_answer": "我是宁波大学 RS-NBU 课题组的专属 AI 学术助理，我可以帮助您搜索最新的学术论文、查询天气，以及回答遥感领域的专业问题。"}
```

### 示例 4: 工具无法回答问题，诚实告知
```json
{"thought": "用户询问组内学生就业情况，这属于内部人事信息。当前可用的工具（arxiv-watcher和amap-weather）都无法获取此类信息，我也无法访问内部数据库。我应该诚实告知用户我的能力边界。", "action": null, "action_input": null, "is_final_answer": true, "final_answer": "很抱歉，我目前无法查询组内学生的具体就业信息。这类人事数据不在我的知识库中，现有工具（ArXiv学术搜索和高德天气查询）也无法获取此类信息。建议您直接咨询课题组负责人或查看课题组内部的人事记录。"}
```"""
