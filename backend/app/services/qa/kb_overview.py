"""
Knowledge base overview builder — injects real-time KB metadata into prompts
to prevent LLM hallucination about available documents.
"""
import logging

logger = logging.getLogger(__name__)


def build_knowledge_base_overview() -> str:
    overview_parts = []

    try:
        from app.services.summary_store import get_summary_store
        from app.services.vector_store import get_collection_info

        store = get_summary_store()
        all_summaries = store.get_all_summaries()

        collection_info = get_collection_info()
        doc_count = collection_info.get("count", 0)

        overview_parts.append("## 📊 知识库实际数据（实时统计，请严格依据此数据回答）")
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
