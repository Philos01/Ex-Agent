import logging
from typing import List, Dict
from app.services.vector_store import search_with_distances
from app.services.parent_store import ParentDocumentStore
from app.core.config import get_complete_config

logger = logging.getLogger(__name__)


class ParentDocumentRetriever:

    def __init__(self):
        self.cfg = get_complete_config()
        self.parent_store = ParentDocumentStore()

        pdr_config = self.cfg.get("parent_document_retrieval", {})
        self.child_retrieve_count = pdr_config.get("child_retrieve_count", 20)
        self.parent_max_count = pdr_config.get("parent_max_count", 5)
        self.parent_max_chars = pdr_config.get("parent_max_chars_total", 12000)
        self.enable_distance_scoring = pdr_config.get("enable_distance_scoring", True)

    def retrieve(self, query: str) -> List[Dict]:
        child_results = search_with_distances(
            query,
            top_k=self.child_retrieve_count
        )

        if not child_results:
            logger.warning("子切片检索无结果")
            return []

        parent_hits = {}
        for child in child_results:
            pid = child["metadata"].get("parent_id")
            if not pid:
                pid = f"legacy_{child['metadata'].get('source', 'unknown')}"
                if pid not in parent_hits:
                    parent_hits[pid] = {
                        "hits": 0,
                        "distances": [],
                        "child_texts": [],
                        "filename": child["metadata"].get("source", ""),
                        "section_title": child["metadata"].get("section_title", "遗留文档"),
                        "is_legacy": True
                    }

            if pid not in parent_hits:
                parent_hits[pid] = {
                    "hits": 0,
                    "distances": [],
                    "child_texts": [],
                    "filename": child["metadata"].get("source", ""),
                    "section_title": child["metadata"].get("section_title", ""),
                    "is_legacy": False
                }

            parent_hits[pid]["hits"] += 1
            parent_hits[pid]["distances"].append(child.get("distance", 1.0))
            parent_hits[pid]["child_texts"].append(child["text"][:100])

        def score_func(item):
            pid, info = item
            hit_score = info["hits"]
            avg_dist = sum(info["distances"]) / len(info["distances"]) if info["distances"] else 1.0
            return hit_score * (1.0 - avg_dist / 2.0)

        sorted_parents = sorted(parent_hits.items(), key=score_func, reverse=True)
        top_parent_ids = [pid for pid, _ in sorted_parents[:self.parent_max_count]]

        results = []
        legacy_results = []
        total_chars = 0

        for pid in top_parent_ids:
            info = parent_hits[pid]

            if info["is_legacy"]:
                legacy_results.append({
                    "text": "\n\n---\n\n".join(info["child_texts"]),
                    "metadata": {
                        "source": info["filename"],
                        "section_title": "遗留文档",
                        "score": round(score_func((pid, info)), 4),
                        "child_hits": info["hits"],
                        "is_legacy": True
                    }
                })
            else:
                parent_docs = self.parent_store.get_parents_by_ids([pid])
                if parent_docs:
                    doc = parent_docs[0]
                    if total_chars + doc["char_count"] <= self.parent_max_chars:
                        results.append({
                            "text": f"[{doc['title']}]\n{doc['content']}",
                            "metadata": {
                                "source": doc["filename"],
                                "section_title": doc["title"],
                                "title_hierarchy": doc.get("title_hierarchy", []),
                                "score": round(score_func((pid, info)), 4),
                                "child_hits": info["hits"],
                                "char_count": doc["char_count"],
                                "is_legacy": False
                            }
                        })
                        total_chars += doc["char_count"]

        results.extend(legacy_results)

        logger.info(
            f"父文档检索完成: query='{query[:50]}...' "
            f"→ {len(child_results)} 子切片 → {len(results)} 父文档 "
            f"(总字符: {total_chars})"
        )
        return results


_parent_retriever = None


def get_parent_retriever() -> ParentDocumentRetriever:
    global _parent_retriever
    if _parent_retriever is None:
        _parent_retriever = ParentDocumentRetriever()
    return _parent_retriever
