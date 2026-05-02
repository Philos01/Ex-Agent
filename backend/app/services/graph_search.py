"""
Graph Search — entity lookup, BFS traversal, hybrid (graph + vector) search.
"""
import json
import logging
from typing import Dict, List, Any, Optional

from app.services.graph_store import get_graph_store
from app.core.config import get_complete_config

logger = logging.getLogger(__name__)

ENTITY_LOOKUP_PROMPT = """Extract the search-relevant entities from this question.
Entities can be any type: people, methods, datasets, concepts, tools, events...

Question: {question}

Output JSON:
{{
  "entities": ["entity_name_1", "entity_name_2"]
}}

Output ONLY the JSON."""


class GraphSearcher:
    """
    Hybrid search combining graph traversal with vector search.
    """

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.cfg = get_complete_config()
        self._store = get_graph_store()

    # ── Entity lookup ─────────────────────────────────────

    def entity_lookup(self, question: str) -> List[str]:
        """Extract entity names from the question using LLM."""
        prompt = ENTITY_LOOKUP_PROMPT.format(question=question)
        try:
            result = self._call_llm(prompt)
            if result:
                return result.get("entities", [])
        except Exception as e:
            logger.warning("[GraphSearch] Entity lookup failed: %s", e)
        return []

    # ── Graph traversal ───────────────────────────────────

    def graph_traverse(
        self, entity_names: List[str], max_depth: int = 2
    ) -> List[Dict]:
        """
        BFS from entity nodes, collecting related documents.
        """
        results = []
        seen_docs = set()
        for ename in entity_names:
            node_id = self._store.get_node_by_name(ename)
            if not node_id:
                # fuzzy search
                matches = self._store.search_nodes(ename, limit=3)
                if not matches:
                    continue
                node_id = matches[0]["id"]

            neighbors = self._store.get_neighbors(node_id, max_depth=max_depth)
            for n in neighbors:
                if n["node"].get("type") == "DOCUMENT":
                    doc_name = n["node"].get("name", "")
                    if doc_name not in seen_docs:
                        seen_docs.add(doc_name)
                        results.append({
                            "filename": doc_name,
                            "relevance": 1.0 / n["depth"],
                            "reason": f"Connected via '{n['node'].get('name')}' ({n['via_edge'].get('type')}) at depth {n['depth']}",
                        })
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results

    # ── Hybrid search ─────────────────────────────────────

    def hybrid_search(
        self, question: str, top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Combine graph traversal and vector search for comprehensive results.

        Returns:
            {
              "graph_results": [...],
              "vector_results": [...],
              "merged_documents": [...],
              "related_entities": [...],
              "paths": [...]
            }
        """
        entities = self.entity_lookup(question)
        graph_results = self.graph_traverse(entities, max_depth=2) if entities else []

        vector_results = self._vector_search(question, top_k)

        merged = self._merge_results(graph_results, vector_results, top_k)

        paths = []
        if len(entities) >= 2:
            path = self._store.find_path(entities[0], entities[1])
            if path:
                paths = path

        related_entities = []
        for ename in entities:
            node_id = self._store.get_node_by_name(ename)
            if node_id:
                neighbors = self._store.get_neighbors(node_id, max_depth=1)
                related_entities.extend([
                    n["node"].get("name") for n in neighbors[:10]
                ])

        return {
            "graph_results": graph_results,
            "vector_results": [{"filename": d.get("metadata", {}).get("source", ""),
                                "text": d.get("text", "")[:200]} for d in vector_results],
            "merged_documents": merged,
            "related_entities": list(set(related_entities)),
            "paths": paths,
        }

    # ── Structured query ──────────────────────────────────

    def structured_query(self, question: str, query_type: str = "entity_list") -> Dict:
        """
        Handle structured questions like "有哪些人/方法/数据集".
        """
        if query_type == "entity_list":
            return self._query_entity_list(question)

        entities = self.entity_lookup(question)
        graph = self.graph_traverse(entities)
        return {
            "type": query_type,
            "entities_found": entities,
            "related_documents": graph,
        }

    def _query_entity_list(self, question: str) -> Dict:
        """Answer '有哪些X' type questions by listing matching nodes."""
        # Try to infer the target type from the question
        type_hint = None
        type_keywords = {
            "人": "作者", "作者": "作者", "方法": "方法", "算法": "方法",
            "模型": "方法", "数据": "数据集", "数据集": "数据集",
            "指标": "指标", "期刊": "期刊/会议", "概念": "概念",
            "工具": "工具", "议题": "议题", "决策": "决策",
            "模块": "模块", "函数": "函数",
        }
        for kw, t in type_keywords.items():
            if kw in question:
                type_hint = t
                break

        entity_names = self.entity_lookup(question)
        all_entities = []
        for ename in entity_names:
            matches = self._store.search_nodes(ename, type_filter=type_hint, limit=10)
            for m in matches:
                all_entities.append({
                    "type": m.get("type"),
                    "name": m.get("name"),
                    "description": m.get("description"),
                    "source_doc": m.get("source_doc"),
                })

        # If no specific entities found, list all of the hinted type
        if not all_entities and type_hint:
            for nid, data in self._store._graph.nodes(data=True):
                if data.get("type") == type_hint:
                    all_entities.append({
                        "type": data.get("type"),
                        "name": data.get("name"),
                        "description": data.get("description"),
                        "source_doc": data.get("source_doc"),
                    })

        return {
            "type": "entity_list",
            "entity_type": type_hint,
            "entities": all_entities,
        }

    # ── Helpers ───────────────────────────────────────────

    def _vector_search(self, question: str, top_k: int) -> List[Dict]:
        from app.services.vector_store import search
        return search(question, top_k=top_k, provider=self.provider)

    def _merge_results(self, graph_results, vector_results, top_k):
        merged = {}
        for gr in graph_results:
            fname = gr["filename"]
            merged[fname] = {"filename": fname, "source": "graph", "score": gr["relevance"]}
        for vr in vector_results:
            fname = vr.get("metadata", {}).get("source", "")
            if not fname:
                continue
            if fname in merged:
                merged[fname]["source"] = "both"
                merged[fname]["score"] = merged[fname]["score"] * 0.6 + 0.4
            else:
                merged[fname] = {"filename": fname, "source": "vector", "score": 0.3}
        return sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:top_k]

    def _call_llm(self, prompt: str) -> Optional[Dict]:
        from app.agents.llm_client import create_llm_client
        client = create_llm_client()
        return client.complete_json(
            prompt=prompt,
            system_prompt="You extract entity names from questions. Output ONLY valid JSON.",
        )
