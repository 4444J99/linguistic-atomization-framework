from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from neo4j import Driver, GraphDatabase

from nexus_babel.models import Document


PROJECTION_CHUNK_SIZE = 500


@dataclass
class LocalGraphCache:
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)


class HypergraphProjector:
    def __init__(self, uri: str | None, username: str | None, password: str | None):  # allow-secret
        self._driver: Driver | None = None
        self.local = LocalGraphCache()
        if uri and username and password:
            self._driver = GraphDatabase.driver(uri, auth=(username, password))

    @property
    def enabled(self) -> bool:
        return self._driver is not None

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def project_document(self, document_id: str, document_payload: dict[str, Any], atoms: list[dict[str, Any]]) -> dict[str, Any]:
        doc_node_id = f"doc:{document_id}"
        self._clear_local_projection(doc_node_id)
        self.local.nodes[doc_node_id] = {"label": "Document", **document_payload}

        atom_ids: list[str] = []
        for atom in atoms:
            atom_node_id = f"atom:{atom['id']}"
            atom_ids.append(atom_node_id)
            self.local.nodes[atom_node_id] = {"label": "Atom", **atom}
            self.local.edges.append(
                {
                    "type": "CONTAINS",
                    "from": doc_node_id,
                    "to": atom_node_id,
                    "metadata": {"atom_level": atom.get("atom_level")},
                }
            )

        if self._driver:
            with self._driver.session() as neo_session:
                neo_session.run(
                    "MATCH (d:Document {id: $id})-[r:CONTAINS]->(a:Atom) "
                    "DELETE r "
                    "WITH collect(a) AS atoms "
                    "UNWIND atoms AS atom "
                    "DETACH DELETE atom",
                    id=document_id,
                )
                neo_session.run(
                    "MERGE (d:Document {id: $id}) SET d += $props",
                    id=document_id,
                    props=document_payload,
                )
                for start in range(0, len(atoms), PROJECTION_CHUNK_SIZE):
                    chunk = atoms[start : start + PROJECTION_CHUNK_SIZE]
                    neo_session.run(
                        "UNWIND $atoms AS atom "
                        "MERGE (a:Atom {id: atom.id}) "
                        "SET a += atom "
                        "WITH a, atom "
                        "MATCH (d:Document {id: $did}) "
                        "MERGE (d)-[:CONTAINS]->(a)",
                        atoms=chunk,
                        did=document_id,
                    )

        return {"document_node_id": doc_node_id, "atom_node_ids": atom_ids}

    def _clear_local_projection(self, doc_node_id: str) -> None:
        stale_atom_ids = [edge["to"] for edge in self.local.edges if edge["from"] == doc_node_id and edge["type"] == "CONTAINS"]
        self.local.edges = [edge for edge in self.local.edges if edge["from"] != doc_node_id]
        for atom_id in stale_atom_ids:
            self.local.nodes.pop(atom_id, None)
        self.local.nodes.pop(doc_node_id, None)

    def integrity_for_document(self, document: Document) -> dict[str, Any]:
        expected = int(document.atom_count or 0)
        projected = int(document.graph_projected_atom_count or 0)
        base = {
            "document_id": document.id,
            "document_nodes": 1,
            "atom_nodes": projected,
            "contains_edges": projected,
            "expected_atom_nodes": expected,
            "projection_status": document.graph_projection_status,
            "neo4j_verified": False,
            "neo4j_document_nodes": None,
            "neo4j_atom_nodes": None,
            "neo4j_contains_edges": None,
            "consistent": document.graph_projection_status == "complete" and expected == projected,
        }

        if not self._driver:
            return base

        with self._driver.session() as neo_session:
            record = neo_session.run(
                "MATCH (d:Document {id: $id}) "
                "OPTIONAL MATCH (d)-[r:CONTAINS]->(a:Atom) "
                "RETURN count(DISTINCT d) AS document_nodes, count(DISTINCT a) AS atom_nodes, count(r) AS contains_edges",
                id=document.id,
            ).single()

        neo_document_nodes = int(record["document_nodes"]) if record else 0
        neo_atom_nodes = int(record["atom_nodes"]) if record else 0
        neo_contains_edges = int(record["contains_edges"]) if record else 0

        return {
            **base,
            "neo4j_verified": True,
            "neo4j_document_nodes": neo_document_nodes,
            "neo4j_atom_nodes": neo_atom_nodes,
            "neo4j_contains_edges": neo_contains_edges,
            "consistent": base["consistent"] and neo_document_nodes == 1 and neo_atom_nodes == expected and neo_contains_edges == expected,
        }

    def query(
        self,
        *,
        document_id: str | None = None,
        node_id: str | None = None,
        relationship_type: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        rel_filter = relationship_type.upper() if relationship_type else None
        target_node = node_id
        if not target_node and document_id:
            target_node = f"doc:{document_id}"

        if target_node and target_node in self.local.nodes:
            edges = [
                edge
                for edge in self.local.edges
                if (edge["from"] == target_node or edge["to"] == target_node)
                and (rel_filter is None or edge["type"] == rel_filter)
            ][:limit]
            node_ids = {target_node}
            for edge in edges:
                node_ids.add(edge["from"])
                node_ids.add(edge["to"])
            nodes = [{"id": nid, **self.local.nodes.get(nid, {})} for nid in node_ids]
            return {
                "source": "local_cache",
                "nodes": nodes,
                "edges": edges,
                "count": {"nodes": len(nodes), "edges": len(edges)},
            }

        if self._driver and document_id:
            with self._driver.session() as neo_session:
                records = neo_session.run(
                    "MATCH (d:Document {id: $id})-[r]->(n) "
                    "RETURN d.id AS doc_id, type(r) AS rel_type, n.id AS node_id "
                    "LIMIT $limit",
                    id=document_id,
                    limit=limit,
                ).data()
            edges = [
                {
                    "type": r["rel_type"],
                    "from": f"doc:{r['doc_id']}",
                    "to": f"atom:{r['node_id']}",
                }
                for r in records
                if rel_filter is None or r["rel_type"] == rel_filter
            ]
            node_ids = {edge["from"] for edge in edges} | {edge["to"] for edge in edges}
            nodes = [{"id": nid} for nid in node_ids]
            return {
                "source": "neo4j",
                "nodes": nodes,
                "edges": edges,
                "count": {"nodes": len(nodes), "edges": len(edges)},
            }

        return {"source": "empty", "nodes": [], "edges": [], "count": {"nodes": 0, "edges": 0}}
