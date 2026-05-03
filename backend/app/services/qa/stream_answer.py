"""
Main streaming QA entry point — orchestrates skill selection, RAG retrieval,
prompt building, and LLM streaming (OpenAI / Ollama / DeepSeek).
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

import requests

from app.core.config import get_complete_config
from app.skills import get_skill_manager

from app.services.qa.utils import format_conversation_history, get_client_for_provider
from app.services.qa.kb_overview import build_knowledge_base_overview
from app.services.qa.prompts import build_rag_prompt, build_skill_prompt
from app.services.qa.retrieval import retrieve_documents
from app.services.qa.react_stream import stream_answer_react

try:
    from ollama import chat as ollama_chat
    OLLAMA_SDK_AVAILABLE = True
except ImportError:
    OLLAMA_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


def stream_answer(
    question: str,
    provider: str = "openai",
    top_k: int = 5,
    temperature: float = None,
    top_p: float = None,
    max_tokens: int = None,
    presence_penalty: float = None,
    frequency_penalty: float = None,
    enable_thinking: bool = None,
    use_react: bool = None,
    messages: List[dict] = None,
    include_state: bool = False,
    use_skill: bool = None,
    skill_name: str = None,
    skill_params: dict = None,
    reasoning_effort: str = None,
    use_graph: bool = None,
):
    cfg = get_complete_config()

    # ── ReAct mode (delegates) ──────────────────────────────
    if use_react:
        logger.info("[QA] ReAct mode for: %s...", question[:50])
        et_react = enable_thinking if enable_thinking is not None else cfg.get("enable_thinking", False)
        yield from stream_answer_react(
            question, provider=provider, messages=messages,
            max_tokens=max_tokens, enable_thinking=et_react,
        )
        return

    # ── 判断是否应该显示引用材料（仅在不使用技能时） ─────────────────
    def should_show_sources(question, using_skill):
        # 如果使用技能，不显示 RAG 的 sources
        if using_skill:
            return False
        
        # 检查是否是自我认知类问题
        self_identity_keywords = ['你是谁', '你叫什么', '你的名字', '你是', '你能做什么', '你基于什么', '谁开发的', '开发者', '你来自']
        for keyword in self_identity_keywords:
            if keyword in question:
                return False
        
        # 检查是否是纯闲聊问题
        casual_keywords = ['笑话', '故事', '聊天', '你好', '嗨', '哈喽', '早上好', '下午好', '晚上好']
        is_casual = any(keyword in question for keyword in casual_keywords)
        
        if is_casual:
            return True
        
        return True

    # ── Skill selection ─────────────────────────────────────
    if use_skill is not None and skill_name is not None:
        should_use_skill_flag = use_skill
        resolved_skill_name = skill_name
        resolved_skill_params = skill_params or {}
    else:
        skill_manager = get_skill_manager()
        conv_history = format_conversation_history(messages)
        should_use_skill_flag, resolved_skill_name, resolved_skill_params = \
            skill_manager.should_use_skill(
                question, provider=provider, conversation_history=conv_history,
            )

    logger.debug(
        "[QA] question=%s, use_skill=%s, skill=%s, params=%s",
        question[:50], should_use_skill_flag, resolved_skill_name, resolved_skill_params,
    )

    # ── Context acquisition (skill or RAG) ──────────────────
    skill_result_text = ""
    docs = []
    context = ""
    _graph_result = None  # populated by graph search in RAG mode
    graph_sources = []  # store graph sources for later merging

    if should_use_skill_flag and resolved_skill_name and resolved_skill_params:
        logger.info("[QA] Skill mode: %s, skipping RAG retrieval", resolved_skill_name)
        if include_state:
            yield {"type": "state", "phase": "skill_call",
                   "message": f"正在调用 {resolved_skill_name} 技能...", "progress": 10}

        skill_mgr = get_skill_manager()
        skill_result = skill_mgr.execute_skill(resolved_skill_name, **resolved_skill_params)

        if not skill_result.get("success", False):
            logger.warning("技能 %s 执行失败，降级到 RAG 检索", resolved_skill_name)
            should_use_skill_flag = False
            resolved_skill_name = None
            docs = retrieve_documents(question, provider, top_k)
            context = "\n\n".join([d.get("text", "") for d in docs])
            if include_state:
                yield {"type": "state", "phase": "retrieving",
                       "message": "技能执行失败，已降级到知识库检索...", "progress": 25}
        else:
            skill_result_text = skill_mgr.format_skill_result(skill_result)
            yield {"type": "skill_result", "skill_name": resolved_skill_name, "result": skill_result_text}
            if include_state:
                yield {"type": "state", "phase": "skill_call",
                       "message": f"{resolved_skill_name} 技能执行完成", "progress": 40}
            context = f"## 技能执行结果\n{skill_result_text}"
            logger.debug("[QA] Skill context length: %d", len(context))
    else:
        logger.info("[QA] RAG mode")

        # ── Graph-first retrieval ──
        _graph_result = None
        graph_enabled = use_graph if use_graph is not None else cfg.get("graph_search", {}).get("enabled", True)
        if graph_enabled:
            try:
                from app.services.query_router import QueryRouter
                router = QueryRouter(provider=provider)
                _graph_result = router.route(question, top_k=top_k)
            except Exception as e:
                logger.warning("[QA] Graph search failed (non-fatal): %s", e)

        # ── Text retrieval ──
        if include_state:
            yield {"type": "state", "phase": "retrieving",
                   "message": "正在知识库中检索相关文档...", "progress": 0}

        docs = retrieve_documents(question, provider, top_k)
        context = "\n\n".join([d.get("text", "") for d in docs])
        logger.debug("[QA] RAG text context length: %d", len(context))

        if include_state:
            yield {"type": "state", "phase": "retrieving",
                   "message": f"检索到 {len(docs)} 篇相关文献", "progress": 25}

        # Merge graph results + fetch full text for graph-identified documents
        if _graph_result:
            graph_context = _format_graph_context(_graph_result)
            # Fetch Chroma-stored text for documents the graph identified
            doc_text, graph_sources = _fetch_graph_document_text(_graph_result, question, top_k)
            if doc_text:
                graph_context = "## 知识图谱检索结果（请优先参考以下结构化信息）\n" + graph_context
                graph_context += "\n\n## 图谱关联文档的完整内容\n" + doc_text
            if graph_context:
                context = graph_context + "\n\n---\n\n## 向量检索结果\n" + context

    conversation_history = format_conversation_history(messages)

    # ── 发送合并的 sources 事件给前端 ─────────────────────────────
    all_sources = []
    if should_show_sources(question, should_use_skill_flag):
        # 添加普通检索的 sources
        if docs:
            all_sources.extend([d.get("metadata", {}) for d in docs])
        
        # 添加图检索的 sources
        if graph_sources:
            all_sources.extend(graph_sources)
        
        # 发送合并的 sources 事件
        yield {"type": "sources", "sources": all_sources}
    else:
        # 发送空 sources
        yield {"type": "sources", "sources": []}

    # ── Time info ───────────────────────────────────────────
    from zoneinfo import ZoneInfo
    beijing_tz = ZoneInfo('Asia/Shanghai')
    current_datetime = datetime.now(beijing_tz)
    current_date_str = current_datetime.strftime('%Y年%m月%d日')
    current_year = current_datetime.year

    # ── Prompt building ─────────────────────────────────────
    if should_use_skill_flag and resolved_skill_name:
        prompt = build_skill_prompt(
            question=question,
            skill_result_text=skill_result_text,
            conversation_history=conversation_history,
            current_date_str=current_date_str,
            current_year=current_year,
        )
    else:
        kb_overview = build_knowledge_base_overview()
        prompt = build_rag_prompt(
            question=question,
            context=context,
            conversation_history=conversation_history,
            kb_overview=kb_overview,
            current_date_str=current_date_str,
            current_year=current_year,
        )

    # ── Generation params ───────────────────────────────────
    temp = temperature if temperature is not None else cfg.get("temperature", 0.7)
    tp = top_p if top_p is not None else cfg.get("top_p", 0.9)
    mt = max_tokens if max_tokens is not None else cfg.get("max_tokens", 2048)
    pp = presence_penalty if presence_penalty is not None else cfg.get("presence_penalty", 0.0)
    fp = frequency_penalty if frequency_penalty is not None else cfg.get("frequency_penalty", 0.0)
    et = enable_thinking if enable_thinking is not None else cfg.get("enable_thinking", False)

    logger.debug("stream_answer params: temp=%s, top_p=%s, max_tokens=%s, pp=%s, fp=%s",
                 temp, tp, mt, pp, fp)

    def _process_chunk(chunk: str) -> str:
        return chunk if chunk else ""

    # ── State: analyzing ────────────────────────────────────
    if include_state and not should_use_skill_flag:
        yield {"type": "state", "phase": "analyzing", "message": "正在分析检索结果...", "progress": 50}

    if include_state:
        if should_use_skill_flag:
            yield {"type": "state", "phase": "generating",
                   "message": f"正在基于 {resolved_skill_name} 结果生成回答...", "progress": 75}
        else:
            yield {"type": "state", "phase": "generating",
                   "message": f"正在使用 {provider} 模型生成回答...", "progress": 75}

    # ── LLM streaming ───────────────────────────────────────
    if provider == "ollama":
        yield from _stream_ollama(cfg, prompt, temp, tp, mt, et, include_state)
    else:
        yield from _stream_openai_or_deepseek(
            cfg, provider, prompt, temp, tp, mt, pp, fp, et,
            messages, reasoning_effort, include_state,
        )


# ── Graph context formatter ────────────────────────────────

def _format_graph_context(route_result: dict) -> str:
    """Format graph search results as context text for the LLM prompt."""
    parts = []
    parts.append("## 图结构检索结果")

    paths = route_result.get("paths", [])
    if paths:
        parts.append("### 实体关系路径")
        for step in paths:
            parts.append(f"- {step['from']} → [{step['relation']}] → {step['to']}")

    entities = route_result.get("related_entities", [])
    if entities:
        parts.append(f"### 关联实体: {', '.join(entities[:15])}")

    merged = route_result.get("merged_documents", [])
    if merged:
        parts.append("### 通过关系网络找到的文档")
        for doc in merged[:5]:
            parts.append(f"- **{doc.get('filename', '')}** (来源: {doc.get('source', '')}, 相关度: {doc.get('score', 0):.2f})")

    # structured query results (entity list)
    if route_result.get("route") == "entity_list":
        ent_list = route_result.get("entities", [])
        if ent_list:
            parts.append(f"### 查询到的实体 ({route_result.get('target_type', '全部')})")
            for ent in ent_list[:20]:
                parts.append(f"- [{ent.get('type', '')}] **{ent.get('name', '')}** — {ent.get('description', '')} (来源: {ent.get('source_doc', '')})")

    if len(parts) == 1:
        return ""  # no useful graph results
    return "\n".join(parts)


def _fetch_graph_document_text(route_result: dict, question: str, top_k: int):
    """Fetch actual document text from Chroma for documents the graph identified.
    Returns (text: str, sources: list)."""
    filenames = _extract_source_filenames(route_result)
    if not filenames:
        return "", []
    try:
        from app.services.vector_store import init_collection
        collection = init_collection()
        if collection is None:
            return "", []
        parts = []
        sources = []
        seen_sources = set()
        for fname in filenames:
            if fname in seen_sources:
                continue
            seen_sources.add(fname)
            sources.append({"source": fname, "via": "graph"})
            try:
                result = collection.get(
                    where={"source": fname},
                    include=["documents", "metadatas"],
                    limit=max(3, top_k),
                )
                for chunk, meta in zip(result.get("documents", []),
                                       result.get("metadatas", [])):
                    section = meta.get("section_title", "") if meta else ""
                    header = f"来源: {fname}"
                    if section:
                        header += f" (章节: {section})"
                    parts.append(header + "\n" + chunk[:2000])
            except Exception:
                continue
        return ("\n\n---\n".join(parts) if parts else ""), sources
    except Exception:
        return "", []


def _extract_source_filenames(route_result: dict) -> list:
    """Walk graph result and collect all unique source_doc references."""
    filenames = set()
    def _walk(obj):
        if isinstance(obj, dict):
            src = obj.get("source_doc") or obj.get("filename") or obj.get("source")
            if src and isinstance(src, str) and not src.startswith("http"):
                filenames.add(src)
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
    _walk(route_result)
    return list(filenames)


# ── LLM streaming helpers ──────────────────────────────────

def _stream_ollama(cfg, prompt, temp, tp, mt, et, include_state):
    try:
        if OLLAMA_SDK_AVAILABLE:
            logger.debug("Using Ollama SDK, model: %s, thinking: %s", cfg.get('ollama_model'), et)
            stream = ollama_chat(
                model=cfg.get('ollama_model'),
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    "temperature": temp, "top_p": tp,
                    "top_k": cfg.get("top_k", 5), "num_predict": mt,
                },
                stream=True,
                think=et,
            )
            in_thinking = False
            for chunk in stream:
                thinking = getattr(chunk.message, 'thinking', None)
                content = getattr(chunk.message, 'content', None)
                if thinking and not in_thinking:
                    in_thinking = True
                if thinking:
                    pass
                elif content:
                    if in_thinking:
                        in_thinking = False
                    yield content
        else:
            logger.debug("Ollama SDK not available, falling back to HTTP request")
            endpoint = cfg.get("ollama_url").rstrip("/") + "/api/generate"
            ollama_options = {
                "temperature": temp, "top_p": tp,
                "top_k": cfg.get("top_k", 5), "num_predict": mt,
            }
            r = requests.post(endpoint, json={
                "model": cfg.get("ollama_model"),
                "prompt": prompt,
                "stream": True,
                "options": ollama_options,
                "think": et,
            }, stream=True, timeout=cfg.get("timeouts", {}).get("requests_stream", 60)
               if cfg.get("timeouts", {}).get("enabled", True) else None)
            r.raise_for_status()

            in_thinking = False
            for line in r.iter_lines():
                if line:
                    try:
                        line_str = line.decode('utf-8')
                        data = json.loads(line_str)
                        if "thinking" in data and data["thinking"] and not in_thinking:
                            in_thinking = True
                        if "thinking" in data and data["thinking"]:
                            pass
                        elif "response" in data and data["response"]:
                            if in_thinking:
                                in_thinking = False
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except Exception:
                        pass
        if include_state:
            yield {"type": "state", "phase": "done", "message": "生成完毕", "progress": 100}
    except Exception as e:
        logger.error("Ollama stream failed: %s", e)
        logger.exception("Ollama stream traceback")
        if include_state:
            yield {"type": "state", "phase": "done", "message": "生成出错", "progress": 100}
        yield f"无法连接 Ollama 服务，请检查配置。错误: {str(e)}"


def _stream_openai_or_deepseek(cfg, provider, prompt, temp, tp, mt, pp, fp, et,
                                messages, reasoning_effort, include_state):
    try:
        client, model_name = get_client_for_provider(cfg, provider, enable_thinking=et)
        logger.debug("Stream: provider=%s, model=%s", provider, model_name)

        api_messages = []
        if messages:
            for msg in messages:
                if msg.get("role") == "assistant" and not msg.get("had_tool_calls", False):
                    api_messages.append({
                        "role": "assistant",
                        "content": msg.get("content", ""),
                    })
                elif msg.get("role") == "assistant" and msg.get("had_tool_calls", False):
                    api_messages.append({
                        "role": "assistant",
                        "content": msg.get("content", ""),
                        "reasoning_content": msg.get("reasoning_content", ""),
                    })
                else:
                    api_messages.append(msg)

        api_messages.append({"role": "user", "content": prompt})

        api_kwargs: Dict[str, Any] = dict(
            model=model_name,
            messages=api_messages,
            max_tokens=mt,
            stream=True,
        )
        if not (provider == "deepseek" and et):
            api_kwargs["temperature"] = temp
            api_kwargs["top_p"] = tp
            api_kwargs["presence_penalty"] = pp
            api_kwargs["frequency_penalty"] = fp

        if provider == "deepseek":
            if et:
                effort = reasoning_effort or "high"
                if effort in ("low", "medium"):
                    effort = "high"
                elif effort == "xhigh":
                    effort = "max"
                api_kwargs["reasoning_effort"] = effort
                api_kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
            else:
                # 明确禁用思考模式，避免默认进入思考
                api_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

        stream = client.chat.completions.create(**api_kwargs)

        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, 'reasoning_content', None)
                if reasoning:
                    yield {"type": "reasoning_chunk", "content": reasoning}
                if delta.content:
                    yield delta.content
        if include_state:
            yield {"type": "state", "phase": "done", "message": "生成完毕", "progress": 100}
    except Exception as e:
        logger.error("Stream failed (provider=%s): %s", provider, e)
        logger.exception("Stream traceback")
        if include_state:
            yield {"type": "state", "phase": "done", "message": "生成出错", "progress": 100}
        yield f"LLM 调用失败，请检查配置与网络。错误: {str(e)}"
