"""
Synchronous non-streaming QA — RAG retrieval + LLM completion.
"""
import logging
from datetime import datetime
from typing import Tuple, List

from app.core.config import get_complete_config
from app.services.qa.utils import format_conversation_history, get_openai_client
from app.services.qa.kb_overview import build_knowledge_base_overview
from app.services.qa.retrieval import retrieve_documents
from app.services.qa.history import get_filtered_history

logger = logging.getLogger(__name__)


def answer_question(
    question: str,
    provider: str = "openai",
    top_k: int = 5,
    session_id: str = "default",
) -> Tuple[str, List[dict]]:
    logger.info("=== answer_question start ===")
    cfg = get_complete_config()

    from zoneinfo import ZoneInfo
    beijing_tz = ZoneInfo('Asia/Shanghai')
    current_datetime = datetime.now(beijing_tz)
    current_date_str = current_datetime.strftime('%Y年%m月%d日')
    current_year = current_datetime.year

    docs = retrieve_documents(question, provider, top_k)

    history_messages = get_filtered_history(session_id)
    conversation_history = format_conversation_history(history_messages)
    context = "\n\n".join([d.get("text", "") for d in docs])

    kb_overview = build_knowledge_base_overview()

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
    try:
        from app.agents.llm_client import create_llm_client, LLMConfig
        client = create_llm_client(
            provider=provider,
            config=LLMConfig(max_tokens=1024, temperature=cfg.get("temperature", 0.1)),
        )
        text = client.complete(prompt=prompt)
        if not text:
            text = "API返回格式错误，请检查配置。"
    except Exception as e:
        logger.error("LLM call failed (provider=%s): %s", provider, e)
        text = f"LLM 调用失败，请检查配置与网络。错误: {str(e)}"

    sources = [d.get("metadata", {}) for d in docs]
    return text, sources
