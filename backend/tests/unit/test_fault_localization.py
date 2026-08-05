from __future__ import annotations

from datetime import datetime, timedelta

from app.services.fault_localization_service import FaultLocalizationService
from app.services.topology_service import TopologyGraph, TopologyGraphService


def _make_graph() -> TopologyGraph:
    return TopologyGraph(
        poles={
            1: {"id": 1, "feeder_id": 10, "transformer_id": 100, "parent_pole_id": None, "latitude": 0.0, "longitude": 0.0, "topology_confidence": 1.0},
            2: {"id": 2, "feeder_id": 10, "transformer_id": 100, "parent_pole_id": 1, "latitude": 0.1, "longitude": 0.0, "topology_confidence": 1.0},
            3: {"id": 3, "feeder_id": 10, "transformer_id": 100, "parent_pole_id": 2, "latitude": 0.2, "longitude": 0.0, "topology_confidence": 1.0},
            4: {"id": 4, "feeder_id": 10, "transformer_id": 100, "parent_pole_id": 3, "latitude": 0.3, "longitude": 0.0, "topology_confidence": 1.0},
            5: {"id": 5, "feeder_id": 10, "transformer_id": 100, "parent_pole_id": 2, "latitude": 0.15, "longitude": 0.05, "topology_confidence": 1.0},
            6: {"id": 6, "feeder_id": 10, "transformer_id": 100, "parent_pole_id": 5, "latitude": 0.16, "longitude": 0.1, "topology_confidence": 1.0},
        },
        transformers={100: {"id": 100, "feeder_id": 10, "parent_pole_id": 1, "latitude": 0.0, "longitude": 0.0, "topology_confidence": 1.0}},
        feeders={10: {"id": 10, "name": "F1", "latitude": 0.0, "longitude": 0.0}},
        adjacency={
            1: {2}, 2: {3, 5}, 3: {4}, 5: {6}
        },
    )


def test_span_fault_is_localized_from_live_dark_boundary() -> None:
    service = FaultLocalizationService()
    graph = _make_graph()

    telemetry = {
        1: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        2: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        3: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
        4: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
        5: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        6: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
    }

    incidents = service.localize(graph, telemetry, scheduled_outages=set(), now=datetime.utcnow())

    assert any(incident["fault_type"] == "span_fault" for incident in incidents)
    assert any(incident["source_pole_id"] == 2 for incident in incidents)
    assert any(incident["affected_pole_count"] >= 2 for incident in incidents)


def test_isolated_sensor_failure_is_ignored() -> None:
    service = FaultLocalizationService()
    graph = _make_graph()

    telemetry = {
        1: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        2: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        3: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        4: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        5: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        6: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
    }

    incidents = service.localize(graph, telemetry, scheduled_outages=set(), now=datetime.utcnow())

    assert incidents == []


def test_scheduled_outage_is_ignored() -> None:
    service = FaultLocalizationService()
    graph = _make_graph()

    telemetry = {
        1: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        2: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        3: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
        4: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
        5: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        6: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
    }

    incidents = service.localize(
        graph,
        telemetry,
        scheduled_outages={3},
        now=datetime.utcnow(),
    )

    assert incidents == []


def test_multiple_faults_are_grouped_into_distinct_incidents() -> None:
    service = FaultLocalizationService()
    graph = _make_graph()

    telemetry = {
        1: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        2: {"power_lost": False, "power_restored": False, "event_time": datetime.utcnow()},
        3: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
        4: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
        5: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
        6: {"power_lost": True, "power_restored": False, "event_time": datetime.utcnow()},
    }

    incidents = service.localize(graph, telemetry, scheduled_outages=set(), now=datetime.utcnow())

    assert len(incidents) == 1
    assert incidents[0]["affected_pole_count"] == 4


def test_transformer_fallback_topology_infers_parent_child_order() -> None:
    service = TopologyGraphService()
    graph = service.build_fallback_graph(
        transformer={"id": 200, "latitude": 0.0, "longitude": 0.0},
        poles=[
            {"id": 10, "latitude": 0.01, "longitude": 0.0},
            {"id": 11, "latitude": 0.02, "longitude": 0.0},
            {"id": 12, "latitude": 0.03, "longitude": 0.0},
        ],
    )

    assert graph.adjacency[200] == {10}
    assert graph.poles[10]["parent_pole_id"] is None
    assert graph.poles[11]["parent_pole_id"] == 10
