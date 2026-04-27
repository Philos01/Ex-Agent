"""
Prompt Engine - 提示词构建器
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    ReAct 提示词构建器
    
    功能:
    - 构建 System Prompt（固定）
    - 构建 Few-Shot 示例（可选）
    - 构建动态上下文（用户问题、暂存器、对话历史）
    """
    
    def __init__(self, tools: List[Dict[str, Any]] = None, use_few_shot: bool = True):
        """
        初始化提示词引擎
        
        Args:
            tools: 工具列表，每个工具包含 name 和 description
            use_few_shot: 是否使用 Few-Shot 示例
        """
        self.tools = tools or []
        self.use_few_shot = use_few_shot
        logger.debug(f"[PromptEngine] Initialized with {len(self.tools)} tools")
    
    def build_prompt(
        self,
        user_question: str,
        scratchpad_text: str = "",
        conversation_history: str = "",
        provider: str = "openai"
    ) -> str:
        """
        构建完整的 Prompt
        
        Args:
            user_question: 用户问题
            scratchpad_text: 暂存器文本
            conversation_history: 对话历史
            provider: LLM 提供商
            
        Returns:
            完整的 Prompt 字符串
        """
        # 获取当前时间
        beijing_tz = ZoneInfo('Asia/Shanghai')
        current_datetime = datetime.now(beijing_tz)
        current_date_str = current_datetime.strftime('%Y年%m月%d日')
        current_year = current_datetime.year
        
        # 构建各部分
        system_prompt = self._build_system_prompt()
        tools_desc = self._build_tools_description()
        few_shot = self._build_few_shot_examples() if self.use_few_shot else ""
        
        # 组合所有部分
        prompt = f"""{system_prompt}

## 可用工具
{tools_desc}

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

<user_question>
{user_question}
</user_question>

{scratchpad_text}

开始！
"""
        logger.debug(f"[PromptEngine] Built prompt ({len(prompt)} chars)")
        return prompt
    
    def _build_system_prompt(self) -> str:
        """构建 System Prompt"""
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
        """构建工具描述"""
        if not self.tools:
            return "当前没有可用工具，请直接回答问题。"
        
        lines = []
        for i, tool in enumerate(self.tools, 1):
            name = tool.get("name", "unknown")
            desc = tool.get("description", "")
            lines.append(f"{i}. **{name}**: {desc}")
        
        return "\n".join(lines)
    
    def _build_kb_overview(self) -> str:
        """构建知识库实际数据概览"""
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
            
            return "\n".join(parts)
        except Exception:
            return "⚠️ 知识库概览不可用，请基于检索结果谨慎回答。"
    
    def _build_few_shot_examples(self) -> str:
        """构建 Few-Shot 示例"""
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

---

## 示例

### 示例 1: 使用搜索工具（结果满足）
Question: 最新的遥感图像融合论文有哪些？
Thought: 用户想了解最新的遥感图像融合论文，我需要使用 arxiv-watcher 工具进行搜索。
Action: arxiv-watcher
Action Input: {"query": "remote sensing image fusion", "max_results": 3}
Observation: [搜索结果：3篇论文...]
Thought: 我已经获取到了最新的论文信息，可以给出最终答案了。
Final Answer: 根据搜索结果，最新的遥感图像融合论文包括：...

### 示例 2: 结果不满足，调整参数重试
Question: 给我10篇关于drone的论文
Thought: 用户要求10篇关于drone的论文，我先调用arxiv-watcher工具搜索。
Action: arxiv-watcher
Action Input: {"query": "drone", "max_results": 10}
Observation: ## Search Results (5 papers) ... [只有5篇]
Thought: 用户要求10篇，但实际只返回了5篇。我需要再尝试一次，看看能否扩大搜索范围获取更多结果。
Action: arxiv-watcher
Action Input: {"query": "drone OR UAV OR unmanned aerial vehicle", "max_results": 10}
Observation: ## Search Results (7 papers) ... [现在有7篇]
Thought: 仍然没有达到10篇，但已经是能找到的最多数量了。我应该基于现有7篇论文给出回答，并说明实际数量。
Final Answer: 根据当前检索结果，共找到7篇与drone相关的论文（未达到您要求的10篇）。以下是相关论文：...

### 示例 3: 直接回答
Question: 你是谁？
Thought: 这是一个关于我身份的问题，不需要调用工具，可以直接回答。
Final Answer: 我是宁波大学 RS-NBU 课题组的专属 AI 学术助理。"""
