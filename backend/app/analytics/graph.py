from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from app.analytics.transitions import Transition


@dataclass
class GraphNode:
    id: int
    name: str
    plays: int
    pagerank: float
    degree: int
    is_hub: bool


@dataclass
class GraphPayload:
    nodes: list[GraphNode]
    edges: list[dict]
    insight: str


def build_transition_graph(
    transitions: list[Transition],
    play_counts: dict[int, int],
    artist_names: dict[int, str],
    min_count: int = 2,
    max_edges: int = 36,
    hide_self_loops: bool = True,
    focus_artist_id: int | None = None,
) -> GraphPayload:
    """Keep the visual graph readable: strongest edges only, plus hubs.

    Graph metrics are computed on the filtered directed graph using NetworkX.
    """
    filtered = [
        edge
        for edge in transitions
        if edge.count >= min_count and (not hide_self_loops or edge.source_artist_id != edge.target_artist_id)
    ]
    if focus_artist_id is not None:
        filtered = [
            edge
            for edge in filtered
            if edge.source_artist_id == focus_artist_id or edge.target_artist_id == focus_artist_id
        ]
    filtered = sorted(filtered, key=lambda item: (-item.count, -item.probability))[:max_edges]

    graph = nx.DiGraph()
    for edge in filtered:
        graph.add_edge(
            edge.source_artist_id,
            edge.target_artist_id,
            weight=edge.count,
            probability=edge.probability,
        )

    if graph.number_of_nodes() == 0:
        return GraphPayload(nodes=[], edges=[], insight="Not enough within-session artist handoffs to draw a network yet.")

    ranks = nx.pagerank(graph, weight="weight") if graph.number_of_edges() else {node: 0.0 for node in graph.nodes}
    degrees = dict(graph.degree())
    hub_cutoff = 0
    if degrees:
        sorted_degrees = sorted(degrees.values(), reverse=True)
        hub_cutoff = sorted_degrees[min(2, len(sorted_degrees) - 1)]

    nodes = [
        GraphNode(
            id=node_id,
            name=artist_names.get(node_id, f"Artist {node_id}"),
            plays=play_counts.get(node_id, 0),
            pagerank=round(ranks.get(node_id, 0.0), 5),
            degree=degrees.get(node_id, 0),
            is_hub=degrees.get(node_id, 0) >= hub_cutoff and hub_cutoff > 0,
        )
        for node_id in graph.nodes
    ]
    nodes.sort(key=lambda item: -item.pagerank)

    payload_edges = [
        {
            "source": edge.source_artist_id,
            "target": edge.target_artist_id,
            "source_name": edge.source_artist_name,
            "target_name": edge.target_artist_name,
            "count": edge.count,
            "probability": round(edge.probability, 4),
        }
        for edge in filtered
    ]

    if nodes:
        center = nodes[0]
        insight = (
            f"{center.name} sits near the center of your listening network — "
            "other artists often appear just before or after."
        )
    else:
        insight = "Your network is still taking shape."

    return GraphPayload(nodes=nodes, edges=payload_edges, insight=insight)
