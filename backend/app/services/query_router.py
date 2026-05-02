"""
Query Router — classify user questions and route to the right search strategy.
"""
import json
import logging
from typing import Dict, Any, Optional

from app.core.config import get_complete_config
from app.services.graph_store import get_graph_store

logger = logging.getLogger(__name__)

ROUTING_PROMPT = """Classify this user question into one of four types.

Types:
- "entity_list": asking "what/who/which X exist" — listing entities of a type
  Examples: "组里有哪些人", "用了哪些数据集", "有什么方法", "发表了什么期刊"
- "relation": asking about connections between entities
  Examples: "A和B有什么关系", "用了X数据集的论文有哪些", "谁做过图像融合"
- "semantic": asking about content meaning, explanations, summaries
  Examples: "这篇文章讲了什么", "全色锐化是什么意思", "介绍一下Transformer"
- "mixed": combines multiple types, needs both graph and semantic search

Question: {question}

Knowledge graph has these entity types: {entity_types}

Output JSON:
{{
  "type": "entity_list|relation|semantic|mixed",
  "entities": ["entity names mentioned in question"],
  "target_type": "the entity type being asked about, or null"
}}

Output ONLY the JSON."""


class QueryRouter:
    """
    Classifies user questions and routes to appropriate search.

    entity_list → graph structured_query
    relation    → graph hybrid_search
    semantic    → vector search (pass-through)
    mixed       → graph hybrid_search
    """

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.cfg = get_complete_config()

    def classify(self, question: str) -> Dict[str, Any]:
        """Classify the question type and extract target entities."""
        store = get_graph_store()
        type_summary = store.get_node_types_summary()
        entity_types = ", ".join(list(type_summary.keys())[:15])

        prompt = ROUTING_PROMPT.format(
            question=question, entity_types=entity_types
        )

        try:
            result = self._call_llm(prompt)
            if result:
                logger.info(
                    "[QueryRouter] '%s' → type=%s, entities=%s",
                    question[:50], result.get("type"), result.get("entities"),
                )
                return result
        except Exception as e:
            logger.warning("[QueryRouter] Classification failed: %s", e)

        return {"type": "semantic", "entities": [], "target_type": None}

    def route(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Classify AND execute the appropriate search."""
        classification = self.classify(question)
        qtype = classification.get("type", "semantic")

        if qtype == "semantic":
            return self._route_semantic(question, top_k)

        # graph-backed types
        from app.services.graph_search import GraphSearcher
        searcher = GraphSearcher(provider=self.provider)

        if qtype == "entity_list":
            target = classification.get("target_type")
            result = searcher.structured_query(question, query_type="entity_list")
            result["route"] = "entity_list"
            result["target_type"] = target
            return result

        if qtype in ("relation", "mixed"):
            result = searcher.hybrid_search(question, top_k=top_k)
            result["route"] = qtype
            result["classification"] = classification
            return result

        return self._route_semantic(question, top_k)

    def _route_semantic(self, question, top_k):
        from app.services.vector_store import search
        docs = search(question, top_k=top_k, provider=self.provider)
        return {
            "route": "semantic",
            "documents": [
                {"text": d.get("text", ""), "metadata": d.get("metadata", {})}
                for d in docs
            ],
        }

    def _call_llm(self, prompt: str) -> Optional[Dict]:
        from app.agents.llm_client import create_llm_client
        client = create_llm_client()
        return client.complete_json(
            prompt=prompt,
            system_prompt="You classify questions. Output ONLY valid JSON.",
        )
