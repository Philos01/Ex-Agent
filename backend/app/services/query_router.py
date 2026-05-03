"""
Query Router — classify user questions and route to the right search strategy.
"""
import json
import logging
import re
from typing import Dict, Any, Optional, List

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


def extract_entities_from_question(question: str) -> List[str]:
    tokens = re.split(r'[\s，。？！,.\?!]', question)
    return [t for t in tokens if t]


def format_route_result(question: str, graph_store, router_result: Dict) -> Dict:
    route = router_result.get("route", "semantic")
    merged_documents = router_result.get("merged_documents", [])
    if not merged_documents:
        merged_documents = router_result.get("documents", [])

    related_entities = []
    seen_entity_names = set()

    for doc in merged_documents:
        filename = doc.get("filename", "") or doc.get("source", "")
        if not filename:
            continue
        entities = graph_store.get_entities_by_document(filename)
        for entity in entities:
            name = entity.get("name")
            if name and name not in seen_entity_names:
                seen_entity_names.add(name)
                related_entities.append(entity)

    paths = []
    seen_path_keys = set()

    entities_from_question = extract_entities_from_question(question)
    entities_from_question.extend([e.get("name") for e in related_entities if e.get("name")])

    for entity1 in entities_from_question:
        for entity2 in entities_from_question:
            if entity1 != entity2:
                path = graph_store.find_direct_relation(entity1, entity2)
                if path:
                    key = f"{entity1}-{path.get('relation')}-{entity2}"
                    key_rev = f"{entity2}-{path.get('relation')}-{entity1}"
                    if key not in seen_path_keys and key_rev not in seen_path_keys:
                        seen_path_keys.add(key)
                        paths.append({
                            "from": entity1,
                            "relation": path.get("relation", ""),
                            "to": entity2,
                            "description": path.get("description", "")
                        })

    existing_paths = router_result.get("paths", [])
    for p in existing_paths:
        key = f"{p.get('from')}-{p.get('relation')}-{p.get('to')}"
        if key not in seen_path_keys:
            seen_path_keys.add(key)
            paths.append(p)

    return {
        "route": route,
        "related_entities": related_entities,
        "merged_documents": merged_documents,
        "paths": paths
    }


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
