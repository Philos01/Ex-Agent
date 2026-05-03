import logging
from typing import List, Dict
from app.services.vector_store import search_with_distances, init_collection
from app.services.embedding import EmbeddingService
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

    def search_in_documents(self, query: str, target_documents: List[str]) -> List[Dict]:
        collection = init_collection()
        if collection is None:
            return []

        try:
            EmbeddingService.initialize()
        except Exception:
            pass

        q_emb = EmbeddingService.embed_texts([query])

        all_child_results = []
        for doc_name in target_documents:
            try:
                if q_emb and q_emb[0]:
                    res = collection.query(
                        query_embeddings=q_emb,
                        n_results=10,
                        where={"source": doc_name},
                        include=["documents", "metadatas", "distances"]
                    )
                else:
                    res = collection.query(
                        query_texts=[query],
                        n_results=10,
                        where={"source": doc_name},
                        include=["documents", "metadatas", "distances"]
                    )

                docs_list = res.get("documents", [[]])[0]
                metas_list = res.get("metadatas", [[]])[0]
                dists_list = res.get("distances", [[]])[0]
                for d, m, dist in zip(docs_list, metas_list, dists_list):
                    all_child_results.append({"text": d, "metadata": m, "distance": dist})
            except Exception as e:
                logger.warning(f"在文档 {doc_name} 中搜索失败: {e}")
                continue

        if not all_child_results:
            return []

        parent_hits = {}
        for child in all_child_results:
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

        results = []
        for pid, info in sorted_parents:
            if info["is_legacy"]:
                results.append({
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

        return results

    def enhance_query(self, original_query: str, suggestions: Dict) -> str:
        query_hint = suggestions.get("query_hint", "")
        focus_entities = suggestions.get("focus_entities", [])
        search_angle = suggestions.get("search_angle", "")

        parts = []
        if query_hint:
            parts.append(query_hint)
        if focus_entities:
            parts.extend(focus_entities)
        if search_angle:
            parts.append(search_angle)

        seen = set()
        unique_parts = []
        for p in parts:
            key = p.lower()
            if key not in seen:
                seen.add(key)
                unique_parts.append(p)

        return " ".join(unique_parts) if unique_parts else original_query

    def rerank_with_focus(self, results: List[Dict], focus_entities: List[str]) -> List[Dict]:
        if not focus_entities:
            return results

        focus_lower = [e.lower() for e in focus_entities]

        scored = []
        for result in results:
            text_lower = result.get("text", "").lower()
            match_count = sum(1 for entity in focus_lower if entity in text_lower)
            original_score = result.get("metadata", {}).get("score", 0)
            adjusted_score = original_score + (match_count * 0.2)
            scored.append((result, adjusted_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in scored]

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        best = {}
        for result in results:
            key = result.get("metadata", {}).get("source") or result.get("metadata", {}).get("parent_id")
            if key is None:
                key = id(result)
            score = result.get("metadata", {}).get("score", 0)
            if key not in best or score > best[key].get("metadata", {}).get("score", 0):
                best[key] = result
        return list(best.values())

    def retrieve_with_clues(self, original_query: str, suggestions: Dict) -> List[Dict]:
        parent_max_count = self.parent_max_count
        target_min_count = parent_max_count - 1

        enhanced_query = self.enhance_query(original_query, suggestions)

        target_documents = suggestions.get("target_documents", [])
        focus_entities = suggestions.get("focus_entities", [])

        results = []
        if target_documents:
            results = self.search_in_documents(enhanced_query, target_documents)

        if len(results) < target_min_count:
            full_results = self.retrieve(enhanced_query)
            results.extend(full_results)
            results = self._deduplicate_results(results)

        results = self.rerank_with_focus(results, focus_entities)
        results = results[:parent_max_count]

        return results


_parent_retriever = None


def get_parent_retriever() -> ParentDocumentRetriever:
    global _parent_retriever
    if _parent_retriever is None:
        _parent_retriever = ParentDocumentRetriever()
    return _parent_retriever
