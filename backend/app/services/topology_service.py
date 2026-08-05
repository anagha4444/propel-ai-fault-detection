from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Any


@dataclass
class TopologyGraph:
    poles: dict[int, dict[str, Any]]
    transformers: dict[int, dict[str, Any]]
    feeders: dict[int, dict[str, Any]]
    adjacency: dict[int, set[int]]
    topology_confidence: dict[int, float] | None = None

    def __post_init__(self) -> None:
        if self.topology_confidence is None:
            self.topology_confidence = {
                pole_id: float(pole.get("topology_confidence", 1.0))
                for pole_id, pole in self.poles.items()
            }


class TopologyGraphService:
    def __init__(self) -> None:
        self._graph_cache: TopologyGraph | None = None

    def load_graph(self, poles: list[dict[str, Any]], transformers: list[dict[str, Any]], feeders: list[dict[str, Any]]) -> TopologyGraph:
        pole_map = {pole["id"]: pole for pole in poles}
        transformer_map = {transformer["id"]: transformer for transformer in transformers}
        feeder_map = {feeder["id"]: feeder for feeder in feeders}

        adjacency: dict[int, set[int]] = {pole_id: set() for pole_id in pole_map}
        topology_confidence: dict[int, float] = {}

        for pole in poles:
            if pole.get("parent_pole_id") is not None:
                parent = pole["parent_pole_id"]
                if parent in adjacency:
                    adjacency[parent].add(pole["id"])
            topology_confidence[pole["id"]] = float(pole.get("topology_confidence", 1.0))

        for transformer in transformers:
            topology_confidence[transformer["id"]] = float(transformer.get("topology_confidence", 1.0))

        self._graph_cache = TopologyGraph(
            poles=pole_map,
            transformers=transformer_map,
            feeders=feeder_map,
            adjacency=adjacency,
            topology_confidence=topology_confidence,
        )
        return self._graph_cache

    def get_cached_graph(self) -> TopologyGraph | None:
        return self._graph_cache

    def build_fallback_graph(self, transformer: dict[str, Any], poles: list[dict[str, Any]]) -> TopologyGraph:
        ordered = sorted(poles, key=lambda p: (p["latitude"], p["longitude"]))
        adjacency: dict[int, set[int]] = {transformer["id"]: set()}
        pole_map: dict[int, dict[str, Any]] = {}

        for idx, pole in enumerate(ordered):
            pole_id = pole["id"]
            pole_map[pole_id] = {
                **pole,
                "topology_confidence": float(pole.get("topology_confidence", 0.55)),
                "parent_pole_id": None if idx == 0 else ordered[idx - 1]["id"],
                "transformer_id": transformer["id"],
            }
            if idx == 0:
                adjacency[transformer["id"]].add(pole_id)
                adjacency[pole_id] = set()
            else:
                adjacency[ordered[idx - 1]["id"]].add(pole_id)
                adjacency.setdefault(pole_id, set())

        graph = TopologyGraph(
            poles=pole_map,
            transformers={transformer["id"]: {**transformer, "topology_confidence": float(transformer.get("topology_confidence", 0.55))}},
            feeders={},
            adjacency=adjacency,
            topology_confidence={
                transformer["id"]: float(transformer.get("topology_confidence", 0.55)),
                **{pole_id: float(details.get("topology_confidence", 0.55)) for pole_id, details in pole_map.items()},
            },
        )
        self._graph_cache = graph
        return graph

    def fallback_parent_from_gps(self, transformer: dict[str, Any], pole: dict[str, Any]) -> int | None:
        distance = hypot(
            float(pole["latitude"]) - float(transformer["latitude"]),
            float(pole["longitude"]) - float(transformer["longitude"]),
        )
        if distance == 0:
            return None
        return pole["id"] if distance < 0.01 else None
