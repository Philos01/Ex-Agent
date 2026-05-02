"""
Graph Analysis — community detection, bridge nodes, path analysis, knowledge gaps.

All analysis is content-agnostic: it operates on graph topology, not entity types.
"""
import logging
from typing import Dict, List, Any, Optional

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from app.services.graph_store import get_graph_store

logger = logging.getLogger(__name__)


class GraphAnalyzer:
    """
    Topological analysis of the knowledge graph.

    Key methods:
    - community_detection: Leiden/greedy clustering
    - find_bridges: betweenness centrality for hub nodes
    - find_path: shortest path between entities
    - knowledge_gaps: isolated nodes, thin communities
    """

    def __init__(self):
        self._store = get_graph_store()

    @property
    def _graph(self) -> nx.DiGraph:
        return self._store._graph

    # ── Community detection ──────────────────────────────

    def community_detection(self) -> Dict[str, Any]:
        """
        Detect communities using modularity-based clustering.
        Runs on an undirected copy for clustering.
        """
        ug = self._graph.to_undirected()
        if ug.number_of_nodes() < 3:
            return {"community_count": 0, "communities": []}

        try:
            communities = list(greedy_modularity_communities(ug))
        except Exception:
            communities = list(nx.community.label_propagation_communities(ug))

        result = []
        for i, comm in enumerate(communities):
            members = []
            for nid in comm:
                data = self._graph.nodes.get(nid, {})
                members.append({
                    "id": nid,
                    "name": data.get("name", nid),
                    "type": data.get("type", "unknown"),
                })
            result.append({
                "community_id": i,
                "size": len(members),
                "members": members[:20],  # cap for display
            })

        return {
            "community_count": len(result),
            "communities": result,
        }

    # ── Bridge / hub nodes ────────────────────────────────

    def find_bridges(self, top_n: int = 10) -> List[Dict]:
        """Find bridge nodes via betweenness centrality."""
        ug = self._graph.to_undirected()
        if ug.number_of_nodes() < 2:
            return []

        bc = nx.betweenness_centrality(ug)
        sorted_nodes = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:top_n]

        result = []
        for nid, score in sorted_nodes:
            data = self._graph.nodes.get(nid, {})
            result.append({
                "id": nid,
                "name": data.get("name", nid),
                "type": data.get("type", "unknown"),
                "centrality": round(score, 4),
                "source_doc": data.get("source_doc", ""),
            })
        return result

    # ── Path analysis ────────────────────────────────────

    def find_path(self, source: str, target: str) -> Optional[List[Dict]]:
        return self._store.find_path(source, target)

    # ── Knowledge gaps ───────────────────────────────────

    def knowledge_gaps(self) -> Dict[str, Any]:
        """
        Identify structural weaknesses:
        - isolated nodes (no edges)
        - thin communities (< 3 members)
        - nodes without any document connection
        """
        ug = self._graph.to_undirected()

        isolated = list(nx.isolates(ug))
        isolated_info = [
            {"id": n, "name": self._graph.nodes[n].get("name", n),
             "type": self._graph.nodes[n].get("type", "unknown")}
            for n in isolated
        ]

        # nodes not connected to any DOCUMENT node
        doc_ids = set(self._store.get_all_document_node_ids())
        orphaned = []
        for n in self._graph.nodes:
            if n in doc_ids:
                continue
            connected = False
            for neighbor in nx.neighbors(ug, n):
                if neighbor in doc_ids:
                    connected = True
                    break
            if not connected:
                orphaned.append({
                    "id": n,
                    "name": self._graph.nodes[n].get("name", n),
                    "type": self._graph.nodes[n].get("type", "unknown"),
                })

        return {
            "isolated_nodes": isolated_info,
            "isolated_count": len(isolated),
            "orphaned_entities": orphaned,
            "orphaned_count": len(orphaned),
        }

    # ── Summary ──────────────────────────────────────────

    # ── Visualization ────────────────────────────────────

    def visualize(self, output_path: str = "knowledge_graph.html",
                  height: str = "750px", width: str = "100%") -> str:
        """
        Generate an interactive HTML visualization of the knowledge graph.

        Uses pyvis (vis.js) for interactive zoom/pan/drag/click.
        Nodes are colored by type, sized by degree, with labeled edges.

        Args:
            output_path: Where to save the HTML file.
            height: CSS height of the canvas.
            width: CSS width of the canvas.

        Returns:
            Path to the generated HTML file.
        """
        from pyvis.network import Network

        g = self._graph
        net = Network(height=height, width=width, bgcolor="#ffffff", font_color="#333333",
                      directed=True, notebook=False, cdn_resources="in_line")

        # Dynamic node colors by type
        type_colors = self._build_type_color_map()

        for node_id, data in g.nodes(data=True):
            ntype = data.get("type", "unknown")
            name = data.get("name", node_id)
            description = data.get("description", "")
            source_doc = data.get("source_doc", "")
            degree = g.degree(node_id)

            # Size: larger for hubs, clamped
            size = min(10 + degree * 2, 50)
            color = type_colors.get(ntype, "#999999")

            # Tooltip with details
            title = f"<b>{name}</b><br>Type: {ntype}<br>"
            if description:
                title += f"{description}<br>"
            if source_doc:
                title += f"Source: {source_doc}<br>"
            title += f"Connections: {degree}"

            net.add_node(node_id, label=name[:30], title=title,
                        color=color, size=size,
                        shape="dot" if ntype == "DOCUMENT" else "box",
                        borderWidth=2 if ntype == "DOCUMENT" else 1)

        for src, dst, data in g.edges(data=True):
            etype = data.get("type", "")
            label = etype[:20] if etype else ""
            net.add_edge(src, dst, title=f"{etype}: {data.get('description', '')}",
                        label=label, arrows="to",
                        color={"color": "#cccccc", "opacity": 0.6})

        # Physics options for better layout
        net.set_options("""
        {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -3000,
              "centralGravity": 0.3,
              "springLength": 150,
              "springConstant": 0.04,
              "damping": 0.09
            },
            "minVelocity": 0.75
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        """)

        # pyvis.write_html uses system encoding (gbk on Windows) — force utf-8
        html = net.generate_html()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("[GraphAnalyzer] Visualization saved to %s", output_path)
        return output_path

    def _build_type_color_map(self) -> Dict[str, str]:
        palette = [
            "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
            "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
            "#86bcb6", "#d37295", "#8cd17d", "#b6992d", "#499894",
            "#e15759", "#fabfd2", "#b3e2cd", "#fdcdac", "#cbd5e8",
        ]
        types = set()
        for _, data in self._graph.nodes(data=True):
            types.add(data.get("type", "unknown"))
        return {t: palette[i % len(palette)] for i, t in enumerate(sorted(types))}

    def summary(self) -> Dict[str, Any]:
        stats = self._store.stats()
        bridges = self.find_bridges(5)
        gaps = self.knowledge_gaps()
        return {
            **stats,
            "top_bridges": bridges,
            "isolated_count": gaps["isolated_count"],
        }
