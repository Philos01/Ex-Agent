import json
import logging
from typing import Dict, Any, Optional, List

from app.agents.llm_client import create_llm_client

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = """你是一个智能检索决策助手。

核心判断原则：
不要看实体或文档的数量，而是看回答问题所需的逻辑链路是否完整！

分两步判断：
1. 先分析：回答用户的问题，需要哪些关键信息点？
   - 例如："张三在哪个公司工作"需要：[张三实体, 工作单位关系, 公司名称]
   - 例如："详细介绍张三背景"需要：[教育、工作经历、项目经验等详细信息]
2. 再检查：图检索的结果是否覆盖了这些关键信息点？

特别说明图数据格式：
- "related_entities" 中的实体有 `properties` 字段，存储结构化属性（如：{{ "职位": "工程师" }}）
- "paths" 中存储实体间的关系路径（如：张三-工作单位-宁波拓普）

判断标准：
- sufficient=true 的情况：
  - 问题是事实查询（A和B的关系是什么，A有什么属性）
  - 图检索找到了问题中关键实体
  - 且直接关系路径完整或实体属性在 properties 中明确
  - 不需要详细解释或额外数据

- sufficient=false 的情况：
  - 问题需要详细描述/解释/总结
  - 问题需要具体数据/参数/数值（这些不在图中存储）
  - 图检索缺少回答问题的关键信息点
  - 问题是开放性的探索性问题
  - 虽然有事实信息，但需要详细文档内容补充

如果 sufficient=false，请给出线索：
- target_documents: 图检索找到的相关文档（最多3个）
- focus_entities: 问题中的关键实体 + 图中的相关实体（最多5个）
- search_angle: 建议的检索角度（如：详细工作信息、技术参数、项目背景等）
- query_hint: 建议的检索查询（可以优化原问题，更准确找到需要的内容）

只输出 JSON，不要其他内容。"""

JUDGE_USER_PROMPT_TEMPLATE = """用户的问题：{question}

图检索结果：
- 检索方式：{route}
- 相关实体：{related_entities}
- 相关文档：{merged_documents}
- 关系路径：{paths}

请先思考：
1. 回答这个问题，需要哪些关键信息点？
2. 图检索是否覆盖了这些信息点（包括实体的 properties 字段）？

然后按要求输出 JSON。"""


def judge_graph_sufficiency(question: str, route_result: Dict) -> Dict:
    fallback = _rule_based_judge(question, route_result)

    try:
        entity_names = []
        for ent in route_result.get("related_entities", []):
            if isinstance(ent, dict):
                entity_names.append(ent.get("name", str(ent)))
            else:
                entity_names.append(str(ent))

        doc_names = []
        for doc in route_result.get("merged_documents", []):
            if isinstance(doc, dict):
                doc_names.append(doc.get("name", doc.get("title", str(doc))))
            else:
                doc_names.append(str(doc))

        path_strs = []
        for p in route_result.get("paths", []):
            if isinstance(p, dict):
                source = p.get("source", "")
                target = p.get("target", "")
                rel_type = p.get("type", p.get("relation", ""))
                path_strs.append(f"{source}-{rel_type}-{target}")
            else:
                path_strs.append(str(p))

        user_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
            question=question,
            route=route_result.get("route", "unknown"),
            related_entities=json.dumps(entity_names, ensure_ascii=False),
            merged_documents=json.dumps(doc_names, ensure_ascii=False),
            paths=json.dumps(path_strs, ensure_ascii=False),
        )

        client = create_llm_client()
        llm_result = client.complete_json(
            prompt=user_prompt,
            provider="openai",
            system_prompt=JUDGE_SYSTEM_PROMPT,
        )

        if not llm_result:
            logger.warning("[GraphRetrievalJudge] LLM返回空结果，使用规则fallback")
            return fallback

        result = {
            "sufficient": bool(llm_result.get("sufficient", fallback["sufficient"])),
            "reason": str(llm_result.get("reason", fallback["reason"])),
            "suggestions": {
                "target_documents": llm_result.get("suggestions", {}).get("target_documents", [])[:3] if isinstance(llm_result.get("suggestions"), dict) else [],
                "focus_entities": llm_result.get("suggestions", {}).get("focus_entities", [])[:5] if isinstance(llm_result.get("suggestions"), dict) else [],
                "search_angle": str(llm_result.get("suggestions", {}).get("search_angle", "")) if isinstance(llm_result.get("suggestions"), dict) else "",
                "query_hint": str(llm_result.get("suggestions", {}).get("query_hint", "")) if isinstance(llm_result.get("suggestions"), dict) else "",
            },
        }

        logger.info("[GraphRetrievalJudge] LLM判断: sufficient=%s, reason=%s", result["sufficient"], result["reason"][:80])
        return result

    except Exception as e:
        logger.error("[GraphRetrievalJudge] LLM判断失败: %s，使用规则fallback", e)
        return fallback


def _rule_based_judge(question: str, route_result: Dict) -> Dict:
    detail_keywords = ["详细介绍", "告诉我关于", "背景", "详细说明", "全面介绍", "深入了解"]
    for kw in detail_keywords:
        if kw in question:
            return {
                "sufficient": False,
                "reason": f"问题包含详细描述关键词'{kw}'，需要文档内容补充",
                "suggestions": {
                    "target_documents": [str(d) if not isinstance(d, dict) else d.get("name", d.get("title", "")) for d in route_result.get("merged_documents", [])[:3]],
                    "focus_entities": [e.get("name", str(e)) if isinstance(e, dict) else str(e) for e in route_result.get("related_entities", [])[:5]],
                    "search_angle": "详细信息",
                    "query_hint": question,
                },
            }

    paths = route_result.get("paths", [])
    if paths:
        return {
            "sufficient": True,
            "reason": "图检索找到明确的关系路径，可回答事实查询",
            "suggestions": {
                "target_documents": [],
                "focus_entities": [],
                "search_angle": "",
                "query_hint": "",
            },
        }

    entities = route_result.get("related_entities", [])
    list_keywords = ["有哪些", "列出", "包含哪些", "都有谁"]
    for kw in list_keywords:
        if kw in question and len(entities) >= 2:
            return {
                "sufficient": True,
                "reason": "实体列表查询且图检索找到多个相关实体",
                "suggestions": {
                    "target_documents": [],
                    "focus_entities": [],
                    "search_angle": "",
                    "query_hint": "",
                },
            }

    docs = route_result.get("merged_documents", [])
    if len(docs) >= 2 and len(entities) >= 2:
        return {
            "sufficient": True,
            "reason": "图检索找到多个相关文档和实体，信息较充分",
            "suggestions": {
                "target_documents": [],
                "focus_entities": [],
                "search_angle": "",
                "query_hint": "",
            },
        }

    return {
        "sufficient": False,
        "reason": "图检索信息不足，需要文档检索补充",
        "suggestions": {
            "target_documents": [str(d) if not isinstance(d, dict) else d.get("name", d.get("title", "")) for d in docs[:3]],
            "focus_entities": [e.get("name", str(e)) if isinstance(e, dict) else str(e) for e in entities[:5]],
            "search_angle": "相关详细信息",
            "query_hint": question,
        },
    }
