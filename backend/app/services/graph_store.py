"""
Graph Store — SQLite-persisted knowledge graph with NetworkX in-memory ops.

Node/edge types are NOT predefined. Documents self-describe their entities.
Supports incremental updates via doc_versions table.
"""
import json
import hashlib
import logging
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

import networkx as nx

from app.core.config import get_complete_config

logger = logging.getLogger(__name__)

DB_FILENAME = "knowledge_graph.db"


class GraphStore:
    """
    Persistent knowledge graph.

    Nodes: {id, type, name, description, properties, embedding, source_doc}
    Edges: {source_id, target_id, type, description, weight, properties}

    Thread-safe via internal lock.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            cfg = get_complete_config()
            data_dir = Path(cfg.get("data_dir", "data"))
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / DB_FILENAME

        self._db_path = Path(db_path)
        self._lock = threading.RLock()
        self._graph = nx.DiGraph()
        self._conn: Optional[sqlite3.Connection] = None
        self._fts_dirty = False

        try:
            self._init_db()
            self._load_to_memory()
        except Exception as e:
            logger.error("[GraphStore] Init failed: %s — recreating database", e)
            self._recreate_db()

    # ── DB init ──────────────────────────────────────────

    def _recreate_db(self):
        """Delete and recreate the database from scratch."""
        with self._lock:
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None
            self._graph.clear()
            try:
                self._db_path.unlink(missing_ok=True)
            except Exception:
                pass
            self._init_db()
            self._load_to_memory()
            logger.info("[GraphStore] Database recreated successfully")

    def _check_integrity(self) -> bool:
        """Run PRAGMA integrity_check. Returns True if OK."""
        try:
            conn = self._get_conn()
            row = conn.execute("PRAGMA integrity_check").fetchone()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    properties TEXT DEFAULT '{}',
                    embedding BLOB,
                    source_doc TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    weight REAL DEFAULT 1.0,
                    properties TEXT DEFAULT '{}',
                    UNIQUE(source_id, target_id, type)
                );
                CREATE TABLE IF NOT EXISTS doc_versions (
                    filename TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    entity_count INTEGER DEFAULT 0,
                    last_indexed_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                    name, description
                );
                CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
                CREATE INDEX IF NOT EXISTS idx_nodes_source ON nodes(source_doc);
                CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
                CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
            """)
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _load_to_memory(self):
        """Load all nodes and edges from SQLite into NetworkX DiGraph."""
        with self._lock:
            self._graph.clear()
            conn = self._get_conn()
            for row in conn.execute("SELECT * FROM nodes"):
                try:
                    props = json.loads(row["properties"]) if row["properties"] else {}
                    if not isinstance(props, dict):
                        props = {}
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse node properties, using empty dict: {e}")
                    props = {}
                self._graph.add_node(
                    row["id"],
                    type=row["type"],
                    name=row["name"],
                    description=row["description"],
                    properties=props,
                    source_doc=row["source_doc"],
                    created_at=row["created_at"],
                )
            for row in conn.execute("SELECT * FROM edges"):
                try:
                    props = json.loads(row["properties"]) if row["properties"] else {}
                    if not isinstance(props, dict):
                        props = {}
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse edge properties, using empty dict: {e}")
                    props = {}
                self._graph.add_edge(
                    row["source_id"],
                    row["target_id"],
                    type=row["type"],
                    description=row["description"],
                    weight=row["weight"],
                    properties=props,
                )
            logger.info(
                "[GraphStore] Loaded %d nodes, %d edges",
                self._graph.number_of_nodes(),
                self._graph.number_of_edges(),
            )

    # ── Node helpers ─────────────────────────────────────

    @staticmethod
    def _make_node_id(name: str) -> str:
        """Deterministic ID from entity name."""
        return hashlib.md5(name.encode("utf-8")).hexdigest()[:12]

    def _node_exists(self, node_id: str) -> bool:
        return node_id in self._graph

    # ── Entity disambiguation ─────────────────────────────

    def find_similar_entity(
        self, name: str, threshold: float = 0.85
    ) -> Optional[str]:
        """
        Find an existing entity with a similar embedding.
        Returns the node_id if found, None otherwise.
        """
        from app.services.embedding import EmbeddingService

        try:
            q_emb = EmbeddingService.embed_texts([name])[0]
        except Exception as e:
            logger.debug("[GraphStore] Embedding failed for '%s': %s", name, e)
            # fallback: exact name match
            node_id = self._make_node_id(name)
            return node_id if self._node_exists(node_id) else None

        best_id, best_sim = None, threshold
        conn = self._get_conn()
        for row in conn.execute("SELECT id, name, embedding FROM nodes WHERE embedding IS NOT NULL"):
            if row["embedding"] is None:
                continue
            try:
                stored_emb = json.loads(row["embedding"])
            except (json.JSONDecodeError, TypeError):
                continue
            sim = self._cosine(q_emb, stored_emb)
            if sim > best_sim:
                best_sim = sim
                best_id = row["id"]

        return best_id

    @staticmethod
    def _cosine(a: list, b: list) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    # ── Public write API ──────────────────────────────────

    def upsert_document(
        self,
        filename: str,
        text: str,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Insert or update a document's entities and relations.
        Handles new / changed / unchanged via content hash.
        """
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        with self._lock:
            existing = self._get_doc_version(filename)
            if existing and existing["content_hash"] == content_hash:
                logger.info("[GraphStore] Unchanged: %s", filename)
                return {"status": "unchanged", "filename": filename}

            if existing:
                self._remove_document_entities(filename)

            # link or create entity nodes
            entity_map: Dict[str, str] = {}  # entity_name → node_id
            for ent in entities:
                etype = ent.get("type", "unknown")
                ename = ent.get("name", "").strip()
                if not ename:
                    continue
                edesc = ent.get("description", "")

                # disambiguation
                similar_id = self.find_similar_entity(ename)
                if similar_id:
                    node_id = similar_id
                    self._update_node_properties(node_id, ent.get("properties", {}))
                else:
                    node_id = self._make_node_id(ename)
                    if self._node_exists(node_id):
                        node_id = self._make_node_id(f"{ename}::{filename}")  # avoid collision

                embedding_blob = self._compute_embedding_blob(ename)

                self._upsert_node(
                    node_id=node_id,
                    etype=etype,
                    name=ename,
                    description=edesc,
                    properties=ent.get("properties", {}),
                    embedding=embedding_blob,
                    source_doc=filename,
                )
                # link document → entity
                self._upsert_edge(
                    source=self._make_node_id(filename),
                    target=node_id,
                    etype="CONTAINS",
                    description=f"Document '{filename}' contains entity '{ename}'",
                )
                entity_map[ename] = node_id

            # document node
            self._upsert_node(
                node_id=self._make_node_id(filename),
                etype="DOCUMENT",
                name=filename,
                description="",
                properties={},
                embedding=None,
                source_doc=filename,
            )

            # relations
            for rel in relations:
                src_name = rel.get("source", "").strip()
                tgt_name = rel.get("target", "").strip()
                rtype = rel.get("type", "RELATED_TO")
                rdesc = rel.get("description", "")
                if not src_name or not tgt_name:
                    continue
                src_id = entity_map.get(src_name) or self._make_node_id(src_name)
                tgt_id = entity_map.get(tgt_name) or self._make_node_id(tgt_name)
                if src_id not in self._graph:
                    self._upsert_node(src_id, "unknown", src_name, "", {}, None, filename)
                if tgt_id not in self._graph:
                    self._upsert_node(tgt_id, "unknown", tgt_name, "", {}, None, filename)
                self._upsert_edge(src_id, tgt_id, rtype, rdesc)

            # cross-document shared-entity edges
            self._link_shared_entities(filename, list(entity_map.values()))

            # doc version
            self._set_doc_version(filename, content_hash, len(entities))
            self._fts_dirty = True

        logger.info(
            "[GraphStore] Upserted %s: %d entities, %d relations, status=%s",
            filename,
            len(entities),
            len(relations),
            "changed" if existing else "new",
        )
        return {
            "status": "changed" if existing else "new",
            "filename": filename,
            "entity_count": len(entities),
            "relation_count": len(relations),
        }

    def delete_document(self, filename: str) -> bool:
        """Delete a document and its exclusively-owned entities."""
        with self._lock:
            if not self._get_doc_version(filename):
                return False
            self._remove_document_entities(filename)
            doc_id = self._make_node_id(filename)
            if doc_id in self._graph:
                self._graph.remove_node(doc_id)
                self._get_conn().execute("DELETE FROM nodes WHERE id=?", (doc_id,))
            self._get_conn().execute("DELETE FROM doc_versions WHERE filename=?", (filename,))
            self._get_conn().commit()
            self._fts_dirty = True
        logger.info("[GraphStore] Deleted: %s", filename)
        return True

    def _upsert_node(self, node_id, etype, name, description, properties, embedding, source_doc):
        conn = self._get_conn()
        # 安全的 properties 序列化
        try:
            if not isinstance(properties, dict):
                properties = {}
            # 确保 properties 的键值对都是可序列化的
            safe_props = {}
            for k, v in properties.items():
                try:
                    # 测试序列化
                    json.dumps({k: v}, ensure_ascii=False)
                    # 清理键名（去除前后空格）
                    clean_k = k.strip()
                    if clean_k:
                        safe_props[clean_k] = v
                except (TypeError, ValueError):
                    # 跳过不可序列化的值
                    logger.debug(f"Skipping non-serializable property: {k}")
                    continue
            props_json = json.dumps(safe_props, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to serialize properties, using empty dict: {e}")
            props_json = "{}"
            safe_props = {}
            
        conn.execute(
            """INSERT OR REPLACE INTO nodes (id, type, name, description, properties, embedding, source_doc)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (node_id, etype, name, description, props_json, embedding, source_doc),
        )
        self._graph.add_node(
            node_id, type=etype, name=name, description=description,
            properties=safe_props, source_doc=source_doc,
        )

    def _update_node_properties(self, node_id, new_props):
        if not new_props:
            return
        existing = self._graph.nodes[node_id].get("properties", {})
        
        # 安全地合并属性
        try:
            if not isinstance(new_props, dict):
                new_props = {}
            # 合并并清理
            merged = {}
            merged.update(existing)
            for k, v in new_props.items():
                try:
                    # 测试序列化
                    json.dumps({k: v}, ensure_ascii=False)
                    # 清理键名
                    clean_k = k.strip()
                    if clean_k:
                        merged[clean_k] = v
                except (TypeError, ValueError):
                    logger.debug(f"Skipping non-serializable property in update: {k}")
                    continue
            
            self._graph.nodes[node_id]["properties"] = merged
            conn = self._get_conn()
            conn.execute(
                "UPDATE nodes SET properties=? WHERE id=?",
                (json.dumps(merged, ensure_ascii=False), node_id),
            )
        except Exception as e:
            logger.warning(f"Failed to update node properties: {e}")

    def _upsert_edge(self, source, target, etype, description, weight=1.0):
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO edges (source_id, target_id, type, description, weight)
               VALUES (?, ?, ?, ?, ?)""",
            (source, target, etype, description, weight),
        )
        if not self._graph.has_edge(source, target):
            self._graph.add_edge(source, target, type=etype, description=description, weight=weight)

    def _remove_document_entities(self, filename: str):
        """Remove entities exclusive to this document. Shared entities stay."""
        doc_id = self._make_node_id(filename)
        conn = self._get_conn()
        entities = conn.execute(
            "SELECT target_id FROM edges WHERE source_id=? AND type='CONTAINS'", (doc_id,)
        ).fetchall()

        for row in entities:
            eid = row["target_id"]
            ref_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM edges WHERE target_id=? AND type='CONTAINS' AND source_id!=?",
                (eid, doc_id),
            ).fetchone()["cnt"]
            if ref_count == 0:
                self._graph.remove_node(eid)
                conn.execute("DELETE FROM nodes WHERE id=?", (eid,))
                conn.execute("DELETE FROM edges WHERE source_id=? OR target_id=?", (eid, eid))
            else:
                conn.execute(
                    "DELETE FROM edges WHERE source_id=? AND target_id=? AND type='CONTAINS'",
                    (doc_id, eid),
                )

        if doc_id in self._graph:
            self._graph.remove_node(doc_id)
        conn.execute("DELETE FROM nodes WHERE id=?", (doc_id,))
        conn.execute("DELETE FROM edges WHERE source_id=? OR target_id=?", (doc_id, doc_id))
        conn.commit()

    def _link_shared_entities(self, filename: str, entity_ids: List[str]):
        """Create SHARES_ENTITY edges between documents that share the same entity."""
        doc_id = self._make_node_id(filename)
        for eid in entity_ids:
            conn = self._get_conn()
            other_docs = conn.execute(
                "SELECT source_id FROM edges WHERE target_id=? AND type='CONTAINS' AND source_id!=?",
                (eid, doc_id),
            ).fetchall()
            for od in other_docs:
                self._upsert_edge(
                    doc_id, od["source_id"], "SHARES_ENTITY",
                    f"Share entity via {self._graph.nodes[eid].get('name', eid)}",
                )

    # ── Versioning ────────────────────────────────────────

    def get_extractor_version(self) -> str:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT value FROM metadata WHERE key='extractor_version'"
        ).fetchone()
        return row["value"] if row else "0.0.0"

    def set_extractor_version(self, version: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES ('extractor_version', ?)",
            (version,),
        )
        conn.commit()

    def _get_doc_version(self, filename: str) -> Optional[Dict]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM doc_versions WHERE filename=?", (filename,)
        ).fetchone()
        return dict(row) if row else None

    def _set_doc_version(self, filename, content_hash, entity_count):
        self._get_conn().execute(
            """INSERT OR REPLACE INTO doc_versions (filename, content_hash, entity_count, last_indexed_at)
               VALUES (?, ?, ?, ?)""",
            (filename, content_hash, entity_count, datetime.now(timezone.utc).isoformat()),
        )
        self._get_conn().commit()

    def check_and_update_stale_documents(self) -> List[str]:
        from app.services.entity_extractor import EXTRACTOR_VERSION

        stored_version = self.get_extractor_version()
        if stored_version == EXTRACTOR_VERSION:
            return []

        conn = self._get_conn()
        rows = conn.execute("SELECT filename FROM doc_versions").fetchall()
        stale_docs = [row["filename"] for row in rows]

        self.set_extractor_version(EXTRACTOR_VERSION)
        logger.info(
            "[GraphStore] Extractor version changed: %s -> %s, %d documents need re-extraction",
            stored_version,
            EXTRACTOR_VERSION,
            len(stale_docs),
        )
        return stale_docs

    def update_document_entities(self, filename: str, text: str) -> Dict[str, Any]:
        from app.services.entity_extractor import EntityExtractor, EXTRACTOR_VERSION

        extractor = EntityExtractor()
        result = extractor.extract(text, filename)
        entities = result.get("entities", [])
        relations = result.get("relations", [])

        upsert_result = self.upsert_document(filename, text, entities, relations)
        self.set_extractor_version(EXTRACTOR_VERSION)

        logger.info(
            "[GraphStore] Re-extracted entities for %s: %d entities, %d relations",
            filename,
            len(entities),
            len(relations),
        )
        return upsert_result

    # ── FTS ───────────────────────────────────────────────

    def _rebuild_fts(self):
        conn = self._get_conn()
        # Use the FTS5 'rebuild' command — safer than DELETE+INSERT
        try:
            conn.execute("INSERT INTO nodes_fts(nodes_fts) VALUES('rebuild')")
        except Exception:
            # Fallback: manually rebuild
            try:
                conn.execute("DELETE FROM nodes_fts")
            except Exception:
                pass
            conn.execute(
                "INSERT INTO nodes_fts(rowid, name, description) SELECT rowid, name, description FROM nodes"
            )
        conn.commit()

    # ── Embedding helper ──────────────────────────────────

    @staticmethod
    def _compute_embedding_blob(name: str) -> Optional[str]:
        try:
            from app.services.embedding import EmbeddingService
            emb = EmbeddingService.embed_texts([name])[0]
            return json.dumps(emb)
        except Exception:
            return None

    # ── Public read API ───────────────────────────────────

    def get_node(self, node_id: str) -> Optional[Dict]:
        if node_id not in self._graph:
            return None
        return dict(self._graph.nodes[node_id])

    def get_node_by_name(self, name: str) -> Optional[str]:
        """Return node_id for exact name match."""
        node_id = self._make_node_id(name)
        if node_id in self._graph:
            return node_id
        conn = self._get_conn()
        row = conn.execute("SELECT id FROM nodes WHERE name=?", (name,)).fetchone()
        return row["id"] if row else None

    def get_neighbors(self, node_id: str, max_depth: int = 2) -> List[Dict]:
        """BFS from node_id, collecting all reachable nodes with path info."""
        if node_id not in self._graph:
            return []
        results = []
        visited = {node_id}
        frontier = {node_id}
        for depth in range(1, max_depth + 1):
            next_frontier = set()
            for n in frontier:
                for _, neighbor in self._graph.out_edges(n):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.add(neighbor)
                        edge_data = self._graph.edges[n, neighbor]
                        results.append({
                            "node": dict(self._graph.nodes[neighbor]),
                            "depth": depth,
                            "via_edge": dict(edge_data),
                        })
                for predecessor, _ in self._graph.in_edges(n):
                    if predecessor not in visited:
                        visited.add(predecessor)
                        next_frontier.add(predecessor)
                        edge_data = self._graph.edges[predecessor, n]
                        results.append({
                            "node": dict(self._graph.nodes[predecessor]),
                            "depth": depth,
                            "via_edge": dict(edge_data),
                        })
            frontier = next_frontier
        return results

    def search_nodes(self, query: str, type_filter: Optional[str] = None,
                     limit: int = 20) -> List[Dict]:
        """Full-text search on node names and descriptions."""
        if self._fts_dirty:
            self._rebuild_fts()
            self._fts_dirty = False
        conn = self._get_conn()
        try:
            sql = """SELECT n.* FROM nodes n
                     JOIN nodes_fts fts ON n.rowid = fts.rowid
                     WHERE nodes_fts MATCH ?
                     ORDER BY rank
                     LIMIT ?"""
            rows = conn.execute(sql, (query, limit)).fetchall()
            if not rows:
                # fallback: LIKE
                like_q = f"%{query}%"
                rows = conn.execute(
                    "SELECT * FROM nodes WHERE name LIKE ? OR description LIKE ? LIMIT ?",
                    (like_q, like_q, limit),
                ).fetchall()
            results = [dict(r) for r in rows]
            if type_filter:
                results = [r for r in results if r.get("type") == type_filter]
            return results
        except Exception:
            return self._fallback_search(query, type_filter, limit)

    def _fallback_search(self, query, type_filter, limit):
        conn = self._get_conn()
        like_q = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM nodes WHERE name LIKE ? OR description LIKE ? LIMIT ?",
            (like_q, like_q, limit),
        ).fetchall()
        results = [dict(r) for r in rows]
        if type_filter:
            results = [r for r in results if r.get("type") == type_filter]
        return results

    def find_path(self, source_name: str, target_name: str) -> Optional[List[Dict]]:
        """Shortest path between two named entities."""
        src_id = self.get_node_by_name(source_name)
        tgt_id = self.get_node_by_name(target_name)
        if not src_id or not tgt_id:
            return None
        try:
            path = nx.shortest_path(self._graph, src_id, tgt_id)
            steps = []
            for i in range(len(path) - 1):
                edge = self._graph.edges[path[i], path[i + 1]]
                steps.append({
                    "from": self._graph.nodes[path[i]]["name"],
                    "to": self._graph.nodes[path[i + 1]]["name"],
                    "relation": edge.get("type", "RELATED_TO"),
                    "description": edge.get("description", ""),
                })
            return steps
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def get_entities_by_document(self, filename: str) -> List[Dict]:
        doc_node_id = self._make_node_id(filename)
        if doc_node_id not in self._graph:
            return []
        entities = []
        for _, neighbor_id, edge_data in self._graph.out_edges(doc_node_id, data=True):
            if edge_data.get("type") == "CONTAINS":
                node_data = self._graph.nodes[neighbor_id]
                entities.append({
                    "name": node_data.get("name", ""),
                    "type": node_data.get("type", ""),
                    "description": node_data.get("description", ""),
                    "properties": node_data.get("properties", {}),
                })
        return entities

    def find_direct_relation(self, entity1_name: str, entity2_name: str) -> Optional[Dict[str, str]]:
        node1_id = self.get_node_by_name(entity1_name)
        node2_id = self.get_node_by_name(entity2_name)
        if not node1_id or not node2_id:
            return None
        if self._graph.has_edge(node1_id, node2_id):
            edge_data = self._graph.edges[node1_id, node2_id]
            return {
                "relation": edge_data.get("type", "RELATED_TO"),
                "description": edge_data.get("description", ""),
            }
        if self._graph.has_edge(node2_id, node1_id):
            edge_data = self._graph.edges[node2_id, node1_id]
            return {
                "relation": edge_data.get("type", "RELATED_TO"),
                "description": edge_data.get("description", ""),
            }
        return None

    def related_documents(self, doc_name: str, max_depth: int = 2) -> List[Dict]:
        """Find documents related to the given document via shared entities."""
        doc_id = self._make_node_id(doc_name)
        neighbors = self.get_neighbors(doc_id, max_depth=max_depth)
        return [
            n for n in neighbors
            if n["node"].get("type") == "DOCUMENT"
        ]

    def get_all_document_node_ids(self) -> List[str]:
        """Return all DOCUMENT-type node IDs."""
        return [
            n for n, data in self._graph.nodes(data=True)
            if data.get("type") == "DOCUMENT"
        ]

    def get_node_types_summary(self) -> Dict[str, int]:
        """Count nodes by type."""
        counts: Dict[str, int] = {}
        for _, data in self._graph.nodes(data=True):
            t = data.get("type", "unknown")
            counts[t] = counts.get(t, 0) + 1
        return counts

    def stats(self) -> Dict[str, Any]:
        return {
            "node_count": self._graph.number_of_nodes(),
            "edge_count": self._graph.number_of_edges(),
            "doc_count": len(self.get_all_document_node_ids()),
            "node_types": self.get_node_types_summary(),
            "db_size_kb": round(self._db_path.stat().st_size / 1024, 1)
            if self._db_path.exists() else 0,
        }

    def rebuild_from_disk(self):
        """Full rebuild: re-parse all documents. Used after schema changes."""
        pass  # reserved for future use

    def close(self):
        with self._lock:
            if self._conn:
                self._conn.commit()
                self._conn.close()
                self._conn = None


# ── singleton ──────────────────────────────────────────────

_graph_store: Optional[GraphStore] = None


def get_graph_store() -> GraphStore:
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
    return _graph_store
