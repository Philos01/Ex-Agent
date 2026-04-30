"""
Question-answer logic: retrieve and call LLM
"""
import logging
from datetime import datetime
from app.services.vector_store import search
from app.services.hybrid_search import hybrid_search
from app.core.config import load_config, get_complete_config
from app.skills import get_skill_manager
from openai import OpenAI
import requests
import re
import json
from typing import Dict, Any, Tuple, List
try:
    from ollama import chat
    OLLAMA_SDK_AVAILABLE = True
except ImportError:
    OLLAMA_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


def _format_conversation_history(messages: list) -> str:
    if not messages:
        return ""
    result = "### 💬 对话历史：\n"
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            result += f"用户: {content}\n"
        elif role == "assistant":
            result += f"助手: {content}\n"
        skill_result = msg.get("skill_result")
        if skill_result:
            skill_name = msg.get("skill_name")
            prefix = f"[技能结果 - {skill_name}]" if skill_name else "[技能结果]"
            result += f"{prefix} {skill_result}\n"
    result += "\n"
    return result


def _build_knowledge_base_overview() -> str:
    """
    构建知识库实际元数据概览，注入到prompt中防止LLM幻觉
    
    Returns:
        知识库概览文本
    """
    overview_parts = []
    
    try:
        from app.services.summary_store import get_summary_store
        from app.services.vector_store import get_collection_info
        
        store = get_summary_store()
        all_summaries = store.get_all_summaries()
        
        collection_info = get_collection_info()
        doc_count = collection_info.get("count", 0)
        
        overview_parts.append(f"## 📊 知识库实际数据（实时统计，请严格依据此数据回答）")
        overview_parts.append(f"- 知识库中文档总数: {len(all_summaries)} 篇")
        overview_parts.append(f"- 向量库中文档片段总数: {doc_count} 个")
        overview_parts.append("")
        
        if all_summaries:
            overview_parts.append("### 知识库中的完整文献列表：")
            for i, summary in enumerate(all_summaries, 1):
                topics_str = "、".join(summary.key_topics[:3]) if summary.key_topics else "无"
                author_info = ""
                if hasattr(summary, 'authors') and summary.authors:
                    author_info = f"\n   - 作者: {', '.join(summary.authors[:5])}"
                pub_info = ""
                if hasattr(summary, 'publication_year') and summary.publication_year:
                    pub_info = f"\n   - 发表年份: {summary.publication_year}"
                if hasattr(summary, 'venue') and summary.venue:
                    pub_info += f"\n   - 期刊/会议: {summary.venue}"
                overview_parts.append(
                    f"{i}. **{summary.filename}**\n"
                    f"   - 摘要: {summary.summary[:150]}{'...' if len(summary.summary) > 150 else ''}\n"
                    f"   - 核心主题: {topics_str}"
                    f"{author_info}{pub_info}"
                )
            overview_parts.append("")
            overview_parts.append("⚠️ **严禁编造上述列表之外的任何文献、作者或研究成果。**")
            overview_parts.append("⚠️ **当用户询问组内文献数量时，必须回答「知识库中目前有 "
                                  f"{len(all_summaries)} 篇文献」，不得给出其他数字。**")
        else:
            overview_parts.append("⚠️ **当前知识库为空，没有任何文献。如用户询问组内文献，请明确告知知识库暂无数据。**")
        
    except Exception as e:
        logger.error(f"构建知识库概览失败: {e}")
        overview_parts.append("⚠️ 知识库概览生成失败，请基于检索到的上下文谨慎回答。")
    
    return "\n".join(overview_parts)


def regularize_output(text: str) -> str:
    """
    正则化处理LLM输出，提升可读性
    - 处理markdown标记（###、***等）
    - 优化文本结构
    - 保持学术严谨性
    - 确保信息完整
    """
    if not text:
        return text
    
    # 1. 处理markdown标题标记，保留标题结构
    # 将### 标题 转换为 <h3>标题</h3> 格式
    text = re.sub(r'^\s*###\s+(.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*##\s+(.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*#\s+(.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # 2. 处理强调标记，保留强调
    # 保留粗体和斜体
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # 3. 处理多余的空行，保持适当的段落间距
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 4. 处理行首空格
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    
    # 5. 优化列表格式
    lines = text.split('\n')
    optimized_lines = []
    in_list = False
    list_type = ''
    
    for line in lines:
        # 处理数字列表
        if re.match(r'^\s*\d+\s*[.,)]\s*', line):
            if not in_list or list_type != 'numbered':
                optimized_lines.append('<ol>')
                in_list = True
                list_type = 'numbered'
            item = re.sub(r'^\s*\d+\s*[.,)]\s*', '', line)
            optimized_lines.append(f'  <li>{item}</li>')
        # 处理项目符号列表
        elif re.match(r'^\s*[•●○▸▶►-\*]\s*', line):
            if not in_list or list_type != 'bulleted':
                optimized_lines.append('<ul>')
                in_list = True
                list_type = 'bulleted'
            item = re.sub(r'^\s*[•●○▸▶►-\*]\s*', '', line)
            optimized_lines.append(f'  <li>{item}</li>')
        else:
            if in_list:
                optimized_lines.append('</' + ('ol' if list_type == 'numbered' else 'ul') + '>')
                in_list = False
                list_type = ''
            optimized_lines.append(line)
    
    # 关闭未闭合的列表
    if in_list:
        optimized_lines.append('</' + ('ol' if list_type == 'numbered' else 'ul') + '>')
    
    text = '\n'.join(optimized_lines)
    
    # 6. 处理专业术语和论文标题
    # 处理期刊名称如TGRS
    text = re.sub(r'\b([A-Z]{2,})\b', r'<span class="font-bold">\1</span>', text)
    # 处理论文标题（驼峰命名）
    text = re.sub(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', r'<span class="font-italic">\1</span>', text)
    
    # 7. 再次处理多余空行，确保格式整洁
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 8. 确保段落间距，添加适当的段落标签
    # 将连续文本行包装在<p>标签中
    paragraphs = []
    current_paragraph = []
    
    for line in text.split('\n'):
        if line.strip() == '' or line.startswith('<h') or line.startswith('<ul') or line.startswith('<ol') or line.startswith('</'):
            if current_paragraph:
                paragraphs.append('<p>' + ' '.join(current_paragraph) + '</p>')
                current_paragraph = []
            paragraphs.append(line)
        else:
            current_paragraph.append(line)
    
    if current_paragraph:
        paragraphs.append('<p>' + ' '.join(current_paragraph) + '</p>')
    
    text = '\n'.join(paragraphs)
    
    # 9. 确保首尾没有多余空白
    text = text.strip()
    
    return text


def _get_client_for_provider(cfg: dict, provider: str, enable_thinking: bool = False):
    """
    Returns (client, model_name) for the given provider.
    DeepSeek uses the OpenAI SDK with deepseek base_url.
    Ollama returns (None, model_name) — caller must handle separately.
    """
    if provider == "ollama":
        return None, cfg.get("ollama_model", "")

    if provider == "deepseek":
        api_key = cfg.get("deepseek_api_key")
        base_url = cfg.get("deepseek_base_url", "https://api.deepseek.com/v1")
        model = (cfg.get("deepseek_reasoner_model", "deepseek-reasoner")
                 if enable_thinking
                 else cfg.get("deepseek_chat_model", "deepseek-chat"))
    else:
        api_key = cfg.get("openai_api_key")
        base_url = cfg.get("openai_base_url")
        model = cfg.get("openai_chat_model", "gpt-3.5-turbo")

    client_kwargs = {}
    if api_key:
        client_kwargs["api_key"] = api_key
    if base_url:
        client_kwargs["base_url"] = base_url
    client_kwargs["timeout"] = 60.0
    return OpenAI(**client_kwargs), model


def _get_openai_client(cfg):
    """获取OpenAI客户端实例（兼容旧调用）"""
    client, _ = _get_client_for_provider(cfg, cfg.get("provider", "openai"))
    return client


def answer_question(question: str, provider: str = "openai", top_k: int = 5, session_id: str = "default") -> Tuple[str, List[dict]]:
    logger.info("=== answer_question start ===")
    cfg = get_complete_config()
    
    # 获取当前时间（北京时间）
    from zoneinfo import ZoneInfo
    beijing_tz = ZoneInfo('Asia/Shanghai')
    current_datetime = datetime.now(beijing_tz)
    current_date_str = current_datetime.strftime('%Y年%m月%d日')
    current_year = current_datetime.year
    
    # 选择检索方式
    docs = _retrieve_documents(question, provider, top_k)
    
    # 获取过滤后的历史上下文
    history_messages = _get_filtered_history(session_id)

    conversation_history = _format_conversation_history(history_messages)
    context = "\n\n".join([d.get("text", "") for d in docs])
    
    kb_overview = _build_knowledge_base_overview()
    
    prompt = f"""
    # Role: 宁波大学 RS-NBU 课题组专属学术助理

    ## 👤 Profile
    你是专门为**宁波大学 RS-NBU（Remote Sensing - Ningbo University）课题组**深度定制的 AI 学术助理。你熟知遥感图像处理领域的前沿知识，并且你的知识库中包含了该课题组所有的内部文献、实验数据、代码库、会议记录和项目申请书。

    ## ⏰ 重要时间信息
    - **当前日期**：{current_date_str}
    - **当前年份**：{current_year}年
    请注意：这是真实的当前时间，你需要基于这个时间信息回答用户关于时间、年份的问题。

    ---

    {kb_overview}

    ---

    ## 📥 输入数据区
    <conversation_history>
    {conversation_history}
    </conversation_history>

    <retrieved_context>
    {context}
    </retrieved_context>

    <user_question>
    {question}
    </user_question>

    ---

    ## 🚫 约束
    1. **使用正确的时间**：必须基于上面提供的当前时间信息（{current_date_str}，{current_year}年）回答问题，不要使用你训练数据中的截止日期。
    2. **严格依据知识库实际数据**：关于组内文献数量、作者、研究成果等事实性问题，必须且只能依据上方「知识库实际数据」部分提供的信息回答，绝不可凭空编造或推测。

    ## 请根据上下文回答问题，并给出引用来源：
    """
    if provider == "ollama":
        # simple HTTP call to Ollama generation endpoint (用户需自行配置 Ollama)
        try:
            endpoint = cfg.get("ollama_url").rstrip("/") + "/api/generate"
            r = requests.post(endpoint, json={"model": cfg.get("ollama_model"), "prompt": prompt},
                             timeout=cfg.get("timeouts", {}).get("requests_post", 60) if cfg.get("timeouts", {}).get("enabled", True) else None)
            r.raise_for_status()
            text = r.json().get("response", "")
        except Exception as e:
            logger.error("Ollama call failed: %s", e)
            text = f"无法连接 Ollama 服务，请检查配置。错误: {str(e)}"
    else:
        try:
            client = _get_openai_client(cfg)
            logger.debug("Calling OpenAI with model: %s", cfg.get('openai_chat_model', 'gpt-3.5-turbo'))
            
            completion = client.chat.completions.create(
                model=cfg.get("openai_chat_model", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=cfg.get("temperature", 0.1),
            )
            
            # 安全地检查响应格式
            if (
                completion.choices 
                and len(completion.choices) > 0 
                and completion.choices[0].message 
                and completion.choices[0].message.content
            ):
                text = completion.choices[0].message.content.strip()
                # # 正则化处理输出
                # text = regularize_output(text)
            else:
                text = "API返回格式错误，请检查配置。"
        except Exception as e:
            logger.error("OpenAI call failed: %s", e)
            logger.exception("OpenAI call traceback")
            text = f"LLM 调用失败，请检查配置与网络。错误: {str(e)}"

    sources = [d.get("metadata", {}) for d in docs]
    return text, sources


def _stream_answer_react(question: str, provider: str = "openai", messages: List[dict] = None, max_tokens: int = None, enable_thinking: bool = False):
    """
    ReAct模式的流式回答（v3.0 AgentLoop适配）

    Args:
        question: 当前用户问题
        provider: LLM供应商
        messages: 对话历史
        max_tokens: 最大输出token数
        enable_thinking: 是否启用思考模式

    Yields:
        ReAct事件
    """
    from app.agents import AgentLoop

    logger.debug("[_stream_answer_react] Starting: question=%s, provider=%s, thinking=%s",
                 question[:50], provider, enable_thinking)

    conversation_history = _format_conversation_history(messages)

    docs = _retrieve_documents(question, provider, top_k=5)
    retrieved_context = "\n\n".join([d.get("text", "") for d in docs])
    logger.debug("[_stream_answer_react] Retrieved context length: %s", len(retrieved_context))

    agent = AgentLoop(provider=provider, max_tokens=max_tokens or 4096, enable_thinking=enable_thinking)

    event_count = 0
    for event_dict in agent.stream_run(question, conversation_history=conversation_history, retrieved_context=retrieved_context):
        event_count += 1
        event_type = event_dict.get("type")

        if event_type == "thought":
            yield {"type": "react_thought", "content": event_dict.get("content")}
        elif event_type == "thought_chunk":
            yield {"type": "react_thought_chunk", "content": event_dict.get("content")}
        elif event_type == "reasoning_chunk":
            yield {"type": "react_reasoning_chunk", "content": event_dict.get("content")}
        elif event_type == "action":
            action_data = event_dict.get("content", {})
            action_name = action_data.get("name") if isinstance(action_data, dict) else event_dict.get("name")
            action_input = action_data.get("input") if isinstance(action_data, dict) else event_dict.get("input")
            logger.debug("[_stream_answer_react] Action: %s, input: %s", action_name, action_input)
            yield {"type": "react_action", "name": action_name, "input": action_input}
        elif event_type == "observation":
            yield {"type": "react_observation", "content": event_dict.get("content")}
        elif event_type == "final_answer":
            final_content = event_dict.get("content")
            logger.debug("[_stream_answer_react] Final answer length: %s", len(str(final_content)))
            yield {"type": "react_final_answer", "content": final_content}
        elif event_type == "done":
            steps = event_dict.get("metadata", {}).get("steps", event_dict.get("steps", []))
            yield {"type": "react_steps", "steps": steps}
            yield {"type": "state", "phase": "done", "message": "生成完毕", "progress": 100}
        elif event_type == "error":
            error_msg = event_dict.get("content") or event_dict.get("message")
            yield {"type": "react_error", "message": error_msg}
        elif event_type == "thinking":
            iteration = event_dict.get("iteration", 1)
            total = event_dict.get("total", 5)
            yield {"type": "state", "phase": "generating", "message": f"思考中 (第{iteration}/{total}步)", "progress": int(iteration / total * 75)}
        elif event_type == "token_usage":
            pass

    logger.debug("[_stream_answer_react] Done, %d events processed", event_count)


def stream_answer(question: str, provider: str = "openai", top_k: int = 5, temperature: float = None, 
                  top_p: float = None, max_tokens: int = None, 
                  presence_penalty: float = None, frequency_penalty: float = None,
                  enable_thinking: bool = None, use_react: bool = None,
                  messages: List[dict] = None, include_state: bool = False,
                  use_skill: bool = None, skill_name: str = None, skill_params: dict = None):
    """
    流式回答问题
    
    Args:
        question: 当前用户问题
        provider: LLM供应商
        top_k: 检索文档数量
        temperature: 温度参数
        top_p: top_p参数
        max_tokens: 最大令牌数
        presence_penalty: 存在惩罚
        frequency_penalty: 频率惩罚
        enable_thinking: 是否启用思考阶段
        use_react: 是否启用ReAct多步推理模式
        messages: 对话历史，格式为 [{"role": "user"|"assistant", "content": "..."}]
        include_state: 是否包含思考状态事件输出
    """
    # 检查是否使用ReAct模式
    if use_react:
        logger.info("[QA] ReAct mode for: %s...", question[:50])
        et_react = enable_thinking if enable_thinking is not None else cfg.get("enable_thinking", False)
        yield from _stream_answer_react(question, provider=provider, messages=messages, max_tokens=max_tokens, enable_thinking=et_react)
        return
    cfg = get_complete_config()
    
    if use_skill is not None and skill_name is not None:
        should_use_skill_flag = use_skill
        resolved_skill_name = skill_name
        resolved_skill_params = skill_params or {}
    else:
        skill_manager = get_skill_manager()
        should_use_skill_flag, resolved_skill_name, resolved_skill_params = skill_manager.should_use_skill(question, provider=provider)
    
    logger.debug("[QA] question=%s, use_skill=%s, skill=%s, params=%s",
                 question[:50], should_use_skill_flag, resolved_skill_name, resolved_skill_params)
    
    skill_result_text = ""
    docs = []
    sources = []
    
    if should_use_skill_flag and resolved_skill_name and resolved_skill_params:
        logger.info("[QA] Skill mode: %s, skipping RAG retrieval", resolved_skill_name)
        if include_state:
            yield {"type": "state", "phase": "skill_call", "message": f"正在调用 {resolved_skill_name} 技能...", "progress": 10}
        
        skill_mgr = get_skill_manager()
        skill_result = skill_mgr.execute_skill(resolved_skill_name, **resolved_skill_params)
        
        if not skill_result.get("success", False):
            logger.warning("技能 %s 执行失败，降级到 RAG 检索", resolved_skill_name)
            should_use_skill_flag = False
            resolved_skill_name = None
            docs = _retrieve_documents(question, provider, top_k)
            context = "\n\n".join([d.get("text", "") for d in docs])
            if include_state:
                yield {"type": "state", "phase": "retrieving", "message": "技能执行失败，已降级到知识库检索...", "progress": 25}
        else:
            skill_result_text = skill_mgr.format_skill_result(skill_result)
            yield {"type": "skill_result", "skill_name": resolved_skill_name, "result": skill_result_text}
            if include_state:
                yield {"type": "state", "phase": "skill_call", "message": f"{resolved_skill_name} 技能执行完成", "progress": 40}
            context = f"## 技能执行结果\n{skill_result_text}"
            logger.debug("[QA] Skill context length: %d", len(context))
    else:
        # 不使用技能，进行正常的 RAG 检索
        logger.info("[QA] RAG mode")
        summary_config = cfg.get("summary_search", {})
        use_two_layer = summary_config.get("enabled", False)
        hybrid_config = cfg.get("hybrid_search", {})
        use_hybrid = hybrid_config.get("enabled", True)
        
        if include_state:
            if use_two_layer:
                yield {"type": "state", "phase": "retrieving", "message": "正在使用双层检索系统（先检索摘要）...", "progress": 0}
            elif use_hybrid:
                yield {"type": "state", "phase": "retrieving", "message": "正在使用混合检索系统查找相关文档...", "progress": 0}
            else:
                yield {"type": "state", "phase": "retrieving", "message": "正在连接 Chroma 向量库...", "progress": 0}
        
        docs = _retrieve_documents(question, provider, top_k)
        
        if include_state:
            yield {"type": "state", "phase": "retrieving", "message": f"检索到 {len(docs)} 篇高度相关的文献", "progress": 25}
        
        context = "\n\n".join([d.get("text", "") for d in docs])
        logger.debug("[QA] RAG context length: %d", len(context))
    
    conversation_history = _format_conversation_history(messages)
    
    # 如果当前轮次使用了技能，将技能结果添加到上下文
    current_skill_context = ""
    if should_use_skill_flag and skill_result_text:
        current_skill_context = f"## 当前技能执行结果\n{skill_result_text}\n"
    
    # 获取当前时间（北京时间）
    from zoneinfo import ZoneInfo
    beijing_tz = ZoneInfo('Asia/Shanghai')
    current_datetime = datetime.now(beijing_tz)
    current_date_str = current_datetime.strftime('%Y年%m月%d日')
    current_year = current_datetime.year
    
    # 根据是否使用技能，调整 prompt
    if should_use_skill_flag and resolved_skill_name:
        # 使用技能模式的 prompt
        prompt = f"""
# Role: 宁波大学 RS-NBU 课题组专属学术助理 (RS-NBU Academic AI Assistant)

## 👤 Profile
你是专门为**宁波大学 RS-NBU（Remote Sensing - Ningbo University）课题组**深度定制的 AI 学术助理。
你的核心职责是：基于技能执行的结果解答用户的问题。

## ⏰ 重要时间信息
- **当前日期**：{current_date_str}
- **当前年份**：{current_year}年
请注意：这是真实的当前时间，你需要基于这个时间信息回答用户关于时间、年份的问题。

---

## 📥 输入数据区
<conversation_history>
{conversation_history}
</conversation_history>

<current_skill_result>
{current_skill_context}
</current_skill_result>

<user_question>
{question}
</user_question>

---

## 🧠 核心工作流 (Skill Mode)
你现在处于**技能执行模式**：

### 🔴 优先级 1：自我认知类 (Identity & Meta-questions)
- **触发条件**：询问你的身份、创造者、能力范围或组内定位。
- **执行动作**：
  1. 忽略 `<current_skill_result>`。
  2. 骄傲且专业地回答："我是宁波大学 RS-NBU 课题组的专属 AI 学术助理。"

### 🟡 优先级 2：基于技能结果的问答 (Skill Result Mode)
- **触发条件**：`<current_skill_result>` 中有技能执行的结果，或者对话历史中有 `[技能结果]` 标记。
- **执行动作**：
  1. **基于技能结果回答**：严格基于 `<current_skill_result>` 和对话历史中的技能结果回答用户问题，不要编造。
  2. **不要提及组内资料**：这是技能模式，不要去查找或提及组内资料。
  3. **提供完整信息**：如果技能返回了论文信息，请提供论文标题、摘要、链接等。
  4. **不要去检索组内资料**：只使用技能返回的结果。
  5. **参考对话历史**：如果之前的对话中有相关的技能结果，也要参考。

---

## 🚫 约束
1. **不要编造**：如果技能结果中没有信息，请如实告知。
2. **不要提及组内资料**：这是技能模式，专注于技能返回的结果。
3. **上下文连贯**：作答前必须参考 `<conversation_history>`。
4. **使用正确的时间**：必须基于上面提供的当前时间信息（{current_date_str}，{current_year}年）回答问题，不要使用你训练数据中的截止日期。

### ✍️ 最终执行指令：
请仔细阅读技能结果，现在开始生成你的回答。
"""
    else:
        kb_overview = _build_knowledge_base_overview()
        
        # 正常 RAG 模式的 prompt
        prompt = f"""
# Role: 宁波大学 RS-NBU 课题组专属学术助理 (RS-NBU Academic AI Assistant)

## 👤 Profile
你是专门为**宁波大学 RS-NBU（Remote Sensing - Ningbo University）课题组**深度定制的 AI 学术助理。你熟知遥感图像处理领域的前沿知识，并且你的知识库中包含了该课题组所有的内部文献、实验数据、代码库、会议记录和项目申请书。
你的核心职责是：作为组内师生的科研"超级大脑"，基于课题组的内部资料和外部搜索结果解答疑问、提供算法实现思路、梳理研究脉络，并辅助日常科研工作。

## ⏰ 重要时间信息
- **当前日期**：{current_date_str}
- **当前年份**：{current_year}年
请注意：这是真实的当前时间，你需要基于这个时间信息回答用户关于时间、年份的问题。

## 🎯 Core Research Areas
- 多源遥感图像融合（Pansharpening, 时空融合, 多光谱与高光谱融合等）
- 像素级、特征级、决策级融合算法（含传统算法与深度学习/大模型方法）
- 图像质量评估（PSNR, SSIM, SAM, ERGAS, Q8, SCC 等指标）
- 遥感下游应用（变化检测、目标检测、地物分类、语义分割等）
- 课题组内部传承的预处理流、配准方法与私有数据集规范

---

{kb_overview}

---

## 📥 输入数据区
<conversation_history>
{conversation_history}
</conversation_history>

<retrieved_context>
{context}
</retrieved_context>

<user_question>
{question}
</user_question>

---

## 🧠 核心工作流与路由逻辑 (Workflow & Routing)
请严格按照以下优先级（从 1 到 5）分析 `<user_question>`，并执行对应的响应策略：

### 🔴 优先级 1：自我认知类 (Identity & Meta-questions)
- **触发条件**：询问你的身份、创造者、能力范围或组内定位（如"你是谁？"、"你能干嘛？"）。
- **执行动作**：
  1. 忽略 `<retrieved_context>`。
  2. 骄傲且专业地回答："我是宁波大学 RS-NBU 课题组的专属 AI 学术助理。我的大脑中汇集了课题组的论文、代码、会议记录等宝贵资料。我在这里帮助组内师生解决多源遥感图像融合、深度学习算法开发及各项科研问题。我还可以帮你搜索最新的 ArXiv 学术论文！"

### 🟡 优先级 2：基于外部搜索结果的问答 (External Search Mode)
- **触发条件**：`<retrieved_context>` 中包含"## 外部搜索结果"，且用户问题与搜索内容相关。
- **执行动作**：
  1. **优先使用外部搜索结果**：如果用户询问最新研究、论文、学术动态等，首先使用外部搜索到的 ArXiv 论文信息进行回答。
  2. **论文摘要总结**：对搜索到的每篇论文进行简要总结，突出核心贡献、方法和结论。
  3. **提供链接**：务必提供每篇论文的 PDF 链接和详情链接。
  4. **结合内部知识**：如果内部知识库中有相关内容，可以结合起来回答。

### 🟢 优先级 3：基于组内知识库的问答 (Internal RAG Mode) - 【核心功能】
- **触发条件**：问题涉及具体的算法细节、论文出处、历年实验数据、组内规范等，或用户询问“我们组做过什么”、“组内关于XX的研究”等针对课题组的情况。
- **执行动作**：
  1. **明确资料属性**：请深刻认知，除明确标记为“外部搜索结果”外，`<retrieved_context>` 中的所有内容**均100%属于 RS-NBU 课题组的内部专属资料**。任何关于组内历史、研究成果、代码、数据的咨询，都请直接且自信地从这些检索内容中提取答案。
  2. **绝对忠诚**：严格基于 `<retrieved_context>` 和上方「知识库实际数据」提供的信息作答，禁止凭空捏造组内未做过的研究。
  3. **溯源引用**：在每个关键结论或数据后，必须以学术规范标注来源。格式示例：`[引用: 文件名.pdf]`。
  4. **结构化输出**：如果是询问算法对比或实验步骤，请用 Markdown 表格或有序列表呈现。
  5. **信息不足处理**：如果检索到的组内资料不全，请明确告知："根据目前的检索，组内资料库中关于该问题的记录仅包含以下信息..."，然后无缝切换至【优先级 4】补充通用学术知识。
  6. **文献统计必须准确**：当用户询问组内文献数量时，必须依据上方「知识库实际数据」中的文档总数回答，绝不可编造或估算。

### 🔵 优先级 4：遥感领域专业探讨 (Domain Expert Mode)
- **触发条件**：用户询问宽泛的学术概念、前沿趋势、代码 Bug 排查，且 `<retrieved_context>` 中无直接答案。
- **执行动作**：
  1. 动用你作为遥感领域专家的内部知识进行解答。
  2. 语气须保持**学术严谨**，涉及公式请使用 LaTeX 格式（如 $E=mc^2$ 或 `$$公式$$`），涉及代码请使用标准 Markdown 代码块并注明语言（如 Python, PyTorch, MATLAB）。
  3. 必须在回答开头或结尾声明边界："*注：检索库中未找到组内直接相关的材料，以下基于遥感领域通用知识为您解答：*"

### ⚪ 优先级 5：日常闲聊与通用辅助 (General Assistance)
- **触发条件**：与遥感科研无关的闲聊、通用文本处理（如润色英文摘要、写邮件等）。
- **执行动作**：
  1. 提供高质量的润色、翻译或礼貌的日常回复。
  2. 保持热情、专业的学长/学姐口吻，随时准备将话题引导回科研工作。

---

## 🚫 全局安全与格式约束 (Strict Constraints)
1. **组内资料绝对信任（Internal KB Priority）**：请牢记，`<retrieved_context>` 中未标记为外部搜索的内容，即代表了 RS-NBU 课题组的全部已知内部情况。当用户询问“课题组/我们组”相关问题时，请直接将其等同于对检索内容的查询，不得怀疑资料的归属性。
2. **防幻觉（Zero Hallucination）**：绝不编造课题组未发表的论文、未取得的指标（如捏造某算法在某数据集上达到了 0.99 的 SSIM）。不知道就回答"组内资料暂无记载"。关于文献数量、作者、发表年份等事实性信息，必须严格依据上方「知识库实际数据」部分，不得推测或编造。
3. **知识隔离**：如果用户的提问同时涉及内部资料和外部常识，请明确区分"课题组内部资料显示..."与"学术界通常认为..."与"ArXiv 最新论文显示..."。
4. **Markdown 优先**：复杂的数学公式必须严格使用 LaTeX 语法；代码必须有完整的注释；对比内容优先使用表格。
5. **上下文连贯**：作答前必须参考 `<conversation_history>`，避免重复回答或语境断裂。
6. **使用正确的时间**：必须基于上面提供的当前时间信息（{current_date_str}，{current_year}年）回答问题，不要使用你训练数据中的截止日期。

### ✍️ 最终执行指令：
请深呼吸，作为 RS-NBU 的一员，仔细阅读上述数据和规则，现在开始生成你的回答。
"""
    
    # 使用传入的参数或配置中的默认值
    temp = temperature if temperature is not None else cfg.get("temperature", 0.7)
    tp = top_p if top_p is not None else cfg.get("top_p", 0.9)
    mt = max_tokens if max_tokens is not None else cfg.get("max_tokens", 2048)
    pp = presence_penalty if presence_penalty is not None else cfg.get("presence_penalty", 0.0)
    fp = frequency_penalty if frequency_penalty is not None else cfg.get("frequency_penalty", 0.0)
    et = enable_thinking if enable_thinking is not None else cfg.get("enable_thinking", False)
    
    # 调试日志
    logger.debug("stream_answer params: temp=%s, top_p=%s, max_tokens=%s, pp=%s, fp=%s",
                 temp, tp, mt, pp, fp)
    
    # 流式输出处理函数
    def process_stream_chunk(chunk):
        """处理流式输出的单个chunk - 保留markdown格式"""
        if not chunk:
            return chunk
        
        # 保留GPT输出的markdown格式，不在后端进行处理
        # 让前端使用专门的markdown渲染库进行展示
        return chunk

    # 发送分析阶段状态 - 仅在RAG模式
    if include_state and not should_use_skill_flag:
        yield {"type": "state", "phase": "analyzing", "message": "正在分析检索结果...", "progress": 50}
    
    if include_state:
        if should_use_skill_flag:
            yield {"type": "state", "phase": "generating", "message": f"正在基于 {resolved_skill_name} 结果生成回答...", "progress": 75}
        else:
            # RAG模式的生成状态
            yield {"type": "state", "phase": "generating", "message": f"正在使用 {provider} 模型生成回答...", "progress": 75}

    if provider == "ollama":
        # Ollama流式响应 - 使用官方SDK或回退到HTTP请求
        try:
            if OLLAMA_SDK_AVAILABLE:
                logger.debug("Using Ollama SDK, model: %s, thinking: %s", cfg.get('ollama_model'), et)
                stream = chat(
                    model=cfg.get('ollama_model'),
                    messages=[{'role': 'user', 'content': prompt}],
                    options={
                        "temperature": temp,
                        "top_p": tp,
                        "top_k": cfg.get("top_k", 5),
                        "num_predict": mt
                    },
                    stream=True,
                    think=et  # 启用thinking阶段输出（如果模型支持）
                )
                
                in_thinking = False
                for chunk in stream:
                    # 安全获取字段，避免部分 chunk 缺失 thinking/content 属性时报错
                    thinking = getattr(chunk.message, 'thinking', None)
                    content = getattr(chunk.message, 'content', None)
                
                    # 1. 检测到思考阶段开始
                    if thinking and not in_thinking:
                        in_thinking = True
                        print('Thinking:\n', end='')
                
                    # 2. 处理思考内容（实时流式打印）
                    if thinking:
                        print(thinking, end='')
                        
                    # 3. 处理最终回答内容
                    elif content:
                        if in_thinking:
                            # 思考结束，首次输出答案时打印分隔提示
                            print('\n\nAnswer:\n', end='')
                            in_thinking = False
                            
                        # 保留原有的数据处理与 yield 机制，供外部迭代器继续消费
                        processed_chunk = process_stream_chunk(content)
                        yield processed_chunk
            else:
                logger.debug("Ollama SDK not available, falling back to HTTP request")
                endpoint = cfg.get("ollama_url").rstrip("/") + "/api/generate"
                ollama_options = {
                    "temperature": temp,
                    "top_p": tp,
                    "top_k": cfg.get("top_k", 5),
                    "num_predict": mt
                }
                
                r = requests.post(endpoint, json={
                    "model": cfg.get("ollama_model"), 
                    "prompt": prompt, 
                    "stream": True,
                    "options": ollama_options,
                    "think": et  # 启用thinking阶段输出（如果模型支持）
                }, stream=True,
                timeout=cfg.get("timeouts", {}).get("requests_stream", 60) if cfg.get("timeouts", {}).get("enabled", True) else None)
                r.raise_for_status()
                
                in_thinking = False
                for line in r.iter_lines():
                    if line:
                        try:
                            line_str = line.decode('utf-8')
                            data = json.loads(line_str)
                            
                            # 检查thinking字段（Qwen3.5等模型）
                            if "thinking" in data and data["thinking"] and not in_thinking:
                                in_thinking = True
                            
                            if "thinking" in data and data["thinking"]:
                                # 输出思考过程（可选，用于调试）
                                pass
                            elif "response" in data and data["response"]:
                                if in_thinking:
                                    in_thinking = False
                                processed_chunk = process_stream_chunk(data["response"])
                                yield processed_chunk
                            
                            if data.get("done", False):
                                break
                        except Exception as e:
                            logger.debug("Failed to parse JSON: %s", e)
                            pass
            # Ollama 流式结束，发送 done 状态
            if include_state:
                yield {"type": "state", "phase": "done", "message": "生成完毕", "progress": 100}
        except Exception as e:
            logger.error("Ollama stream failed: %s", e)
            logger.exception("Ollama stream traceback")
            if include_state:
                yield {"type": "state", "phase": "done", "message": "生成出错", "progress": 100}
            yield f"无法连接 Ollama 服务，请检查配置。错误: {str(e)}"
    else:
        # OpenAI / DeepSeek 流式响应
        try:
            client, model_name = _get_client_for_provider(cfg, provider, enable_thinking=et)
            logger.debug("Stream: provider=%s, model=%s", provider, model_name)

            api_kwargs: Dict[str, Any] = dict(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=mt,
                stream=True,
                presence_penalty=pp,
                frequency_penalty=fp,
            )
            # deepseek-reasoner does not support temperature/top_p
            if not (provider == "deepseek" and et):
                api_kwargs["temperature"] = temp
                api_kwargs["top_p"] = tp

            stream = client.chat.completions.create(**api_kwargs)

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    reasoning = getattr(delta, 'reasoning_content', None)
                    if reasoning:
                        yield {"type": "reasoning_chunk", "content": reasoning}
                    if delta.content:
                        content = delta.content
                        processed_chunk = process_stream_chunk(content)
                        yield processed_chunk
            if include_state:
                yield {"type": "state", "phase": "done", "message": "生成完毕", "progress": 100}
        except Exception as e:
            logger.error("Stream failed (provider=%s): %s", provider, e)
            logger.exception("Stream traceback")
            if include_state:
                yield {"type": "state", "phase": "done", "message": "生成出错", "progress": 100}
            yield f"LLM 调用失败，请检查配置与网络。错误: {str(e)}"


def _retrieve_documents(question: str, provider: str = "openai", top_k: int = 5):
    cfg = get_complete_config()

    logger.debug("[_retrieve_documents] Starting for: %s...", question[:50])

    pdr_config = cfg.get("parent_document_retrieval", {})
    use_parent_retrieval = pdr_config.get("enabled", False)

    if use_parent_retrieval:
        try:
            from app.services.parent_retriever import get_parent_retriever
            retriever = get_parent_retriever()
            results = retriever.retrieve(question)

            if results:
                logger.info("Parent document retrieval returned %d results", len(results))
                return results
            else:
                logger.info("Parent document retrieval returned no results, falling back to hybrid")
        except Exception as e:
            logger.error("Parent document retrieval failed: %s", e, exc_info=True)

    summary_config = cfg.get("summary_search", {})
    use_two_layer = summary_config.get("enabled", False)

    if use_two_layer:
        try:
            from app.services.two_layer_search import two_layer_search
            logger.info("Using two-layer search")
            result = two_layer_search(question, provider=provider)
            logger.info("Two-layer search returned %d results", len(result))
            return result
        except Exception as e:
            logger.error("Two-layer search failed: %s", e, exc_info=True)

    hybrid_config = cfg.get("hybrid_search", {})
    use_hybrid = hybrid_config.get("enabled", True)

    if use_hybrid:
        try:
            from app.services.hybrid_search import hybrid_search
            logger.info("Using hybrid search")
            return hybrid_search(question, provider=provider)
        except Exception as e:
            logger.error("Hybrid search failed, falling back to vector: %s", e)

    logger.info("Using vector search")
    return search(question, top_k=top_k, provider=provider)


def _get_filtered_history(session_id: str = "default") -> List[dict]:
    """
    获取过滤后的历史对话
    
    Args:
        session_id: 会话ID
        
    Returns:
        过滤后的历史消息列表
    """
    cfg = get_complete_config()
    context_config = cfg.get("context_management", {})
    
    if not context_config.get("enabled", True):
        return []
    
    try:
        from app.services.context_manager import get_context_manager
        
        max_history = context_config.get("max_history_rounds", 5)
        exclude_errors = context_config.get("exclude_error_messages", True)
        exclude_questionable = context_config.get("exclude_questionable_messages", False)
        
        context_mgr = get_context_manager(session_id, max_history=max_history)
        filtered_history = context_mgr.get_filtered_history(
            exclude_errors=exclude_errors,
            exclude_questionable=exclude_questionable
        )
        
        logger.debug("Fetched %d filtered history messages", len(filtered_history))
        return filtered_history

    except Exception as e:
        logger.error("Failed to get filtered history: %s", e, exc_info=True)
        return []


def _add_to_history(
    role: str, 
    content: str, 
    session_id: str = "default"
):
    """
    添加消息到历史记录
    
    Args:
        role: 角色（"user" 或 "assistant"）
        content: 消息内容
        session_id: 会话ID
    """
    cfg = get_complete_config()
    context_config = cfg.get("context_management", {})
    
    if not context_config.get("enabled", True):
        return
    
    try:
        from app.services.context_manager import get_context_manager
        
        max_history = context_config.get("max_history_rounds", 5)
        context_mgr = get_context_manager(session_id, max_history=max_history)
        context_mgr.add_message(role, content)
        
        logger.debug("Added %s message to history", role)
    except Exception as e:
        logger.error("Failed to add to history: %s", e, exc_info=True)
