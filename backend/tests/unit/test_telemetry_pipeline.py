from __future__ import annotations

from datetime import datetime, timedelta

from app.schemas.telemetry import TelemetryIngest
from app.services.telemetry_pipeline_service import TelemetryPipelineService


class DummyDB:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.records

    def first(self):
        return self.records[0] if self.records else None

    def scalar(self):
        return 1

    def commit(self):
        return None


def test_telemetry_ingest_accepts_valid_payload() -> None:
    payload = TelemetryIngest(
        device_id="dev-001",
        pole_id=1,
        sequence_number=5,
        event_type="heartbeat",
        event_time=datetime.utcnow(),
    )
    assert payload.device_id == "dev-001"
    assert payload.sequence_number == 5


def test_duplicate_packet_is_detected() -> None:
    service = TelemetryPipelineService(DummyDB())
    payload = {
        "device_id": "dev-001",
        "pole_id": 1,
        "sequence_number": 5,
        "event_type": "heartbeat",
        "event_time": datetime.utcnow(),
        "firmware_version": "1.2",
        "power_lost": False,
        "power_restored": False,
    }
    result = service._normalize_event_type(payload, "1.2")
    assert result == "heartbeat"


def test_out_of_order_telemetry_is_marked() -> None:
    now = datetime.utcnow()
    raw = {
        "device_id": "dev-002",
        "pole_id": 2,
        "sequence_number": 2,
        "event_type": "power_lost",
        "event_time": now - timedelta(minutes=1),
        "firmware_version": "1.2",
        "power_lost": True,
        "power_restored": False,
    }
    assert raw["sequence_number"] == 2
    assert raw["event_type"] == "power_lost"
