from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.services.topology_service import TopologyGraph


@dataclass(frozen=True)
class FaultIncident:
    fault_type: str
    source_pole_id: int
    affected_pole_count: int
    confidence_score: float
    topology_confidence: float
    affected_poles: list[int]
    boundary_poles: list[int]


class FaultLocalizationService:
    def localize(
        self,
        graph: TopologyGraph,
        telemetry: dict[int, dict[str, Any]],
        scheduled_outages: set[int],
        now: datetime,
    ) -> list[dict[str, Any]]:
        dark_poles = {
            pole_id
            for pole_id, snapshot in telemetry.items()
            if snapshot.get("power_lost") and pole_id not in scheduled_outages
        }
        if not dark_poles:
            return []

        live_poles = {
            pole_id
            for pole_id, snapshot in telemetry.items()
            if not snapshot.get("power_lost") and pole_id not in scheduled_outages
        }

        incidents: list[dict[str, Any]] = []
        seen_dark: set[int] = set()

        for live_root in sorted(live_poles):
            component = self._collect_dark_descendants(live_root, dark_poles, graph.adjacency)
            if len(component) <= 1:
                continue

            seen_dark.update(component)
            boundary_poles = self._boundary_poles(live_root, component, graph, live_poles)
            fault_type = self._classify_fault(component, graph, boundary_poles, live_root)
            affected_poles = sorted(component)
            confidence = self._calculate_confidence(component, graph, live_root, fault_type)

            incidents.append(
                {
                    "fault_type": fault_type,
                    "source_pole_id": live_root,
                    "affected_pole_count": len(affected_poles),
                    "confidence_score": round(confidence, 3),
                    "topology_confidence": round(self._topology_confidence_for(component, graph), 3),
                    "affected_poles": affected_poles,
                    "boundary_poles": sorted(boundary_poles),
                }
            )

        isolated = sorted(dark_poles - seen_dark)
        if isolated:
            for dark_pole in isolated:
                if len(self._collect_dark_descendants(dark_pole, dark_poles, graph.adjacency)) == 1:
                    continue
        return incidents

    def _collect_dark_descendants(self, root: int, dark_poles: set[int], adjacency: dict[int, set[int]]) -> set[int]:
        queue: deque[int] = deque([root])
        visited: set[int] = set()
        component: set[int] = set()
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            for neighbor in adjacency.get(node, set()):
                if neighbor in dark_poles and neighbor not in component:
                    component.add(neighbor)
                    queue.append(neighbor)
        return component

    def _boundary_poles(self, live_root: int, component: set[int], graph: TopologyGraph, live_poles: set[int]) -> set[int]:
        return {live_root}

    def _select_source_pole(
        self,
        component: set[int],
        graph: TopologyGraph,
        telemetry: dict[int, dict[str, Any]],
        live_poles: set[int],
    ) -> int:
        for pole_id in sorted(component):
            for neighbor in graph.adjacency.get(pole_id, set()):
                if neighbor in live_poles:
                    return neighbor
        pole_ids = sorted(component)
        return min(
            pole_ids,
            key=lambda pole_id: (
                self._distance_from_transformer(pole_id, graph),
                telemetry.get(pole_id, {}).get("event_time", datetime.min),
            ),
        )

    def _distance_from_transformer(self, pole_id: int, graph: TopologyGraph) -> int:
        if pole_id not in graph.poles:
            return 999
        parent = graph.poles[pole_id].get("parent_pole_id")
        depth = 0
        while parent is not None:
            depth += 1
            parent = graph.poles.get(parent, {}).get("parent_pole_id")
        return depth

    def _classify_fault(
        self,
        component: set[int],
        graph: TopologyGraph,
        boundary_poles: set[int],
        source_pole_id: int,
    ) -> str:
        if self._is_transformer_branch(component, graph):
            return "dt_fault"
        if self._is_feeder_boundary(component, graph, boundary_poles):
            return "feeder_fault"
        return "span_fault"

    def _is_transformer_branch(self, component: set[int], graph: TopologyGraph) -> bool:
        root_candidates = [
            pole_id
            for pole_id in component
            if graph.poles.get(pole_id, {}).get("parent_pole_id") is None
            and graph.poles.get(pole_id, {}).get("transformer_id") is not None
        ]
        return bool(root_candidates)

    def _is_feeder_boundary(self, component: set[int], graph: TopologyGraph, boundary_poles: set[int]) -> bool:
        root_candidates = [pole_id for pole_id in component if graph.poles.get(pole_id, {}).get("parent_pole_id") is None]
        return bool(root_candidates) and len(component) >= 3 and len(boundary_poles) >= 1

    def _calculate_confidence(
        self,
        component: set[int],
        graph: TopologyGraph,
        source_pole_id: int,
        fault_type: str,
    ) -> float:
        topology_confidence = self._topology_confidence_for(component, graph)
        size_penalty = min(0.12, len(component) * 0.01)
        fault_bias = {"span_fault": 0.08, "dt_fault": 0.05, "feeder_fault": 0.03}[fault_type]
        if fault_type == "dt_fault" and topology_confidence < 0.85:
            topology_confidence *= 0.8
        return max(0.45, min(0.99, topology_confidence - size_penalty + fault_bias))

    def _topology_confidence_for(self, component: set[int], graph: TopologyGraph) -> float:
        confs = [float(graph.poles.get(pole_id, {}).get("topology_confidence", 1.0)) for pole_id in component]
        if not confs:
            return 0.55
        return sum(confs) / len(confs)
