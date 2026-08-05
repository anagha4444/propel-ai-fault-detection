from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.network import Fault, Pole, ScheduledOutage, SimulationLog, Telemetry
from app.repositories.telemetry_repository import TelemetryRepository


class SimulatorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TelemetryRepository(db)

    def span_fault(self, pole_id: int) -> dict[str, Any]:
        return self._create_fault_event("span_fault", pole_id)

    def dt_fault(self, pole_id: int) -> dict[str, Any]:
        return self._create_fault_event("dt_fault", pole_id)

    def feeder_fault(self, feeder_id: int) -> dict[str, Any]:
        return self._create_fault_event("feeder_fault", feeder_id=feeder_id)

    def device_failure(self, pole_id: int) -> dict[str, Any]:
        pole = self.db.get(Pole, pole_id)
        if pole is None:
            raise ValueError("Unknown pole")
        pole.is_sensor_online = False
        pole.last_seen_at = datetime.utcnow()
        self._record_simulation_log("device_failure", {"pole_id": pole_id})
        self.db.commit()
        return {"status": "device_failure", "pole_id": pole_id}

    def scheduled_outage(self, pole_id: int, duration_minutes: int = 60) -> dict[str, Any]:
        outage = ScheduledOutage(
            pole_id=pole_id,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(minutes=duration_minutes),
            active=True,
        )
        self.db.add(outage)
        self._record_simulation_log("scheduled_outage", {"pole_id": pole_id, "duration_minutes": duration_minutes})
        self.db.commit()
        return {"status": "scheduled_outage", "pole_id": pole_id, "duration_minutes": duration_minutes}

    def repair(self, pole_id: int) -> dict[str, Any]:
        pole = self.db.get(Pole, pole_id)
        if pole is None:
            raise ValueError("Unknown pole")
        pole.is_sensor_online = True
        pole.last_seen_at = datetime.utcnow()
        self._record_simulation_log("repair", {"pole_id": pole_id})
        self.db.commit()
        return {"status": "repair", "pole_id": pole_id}

    def duplicate_telemetry(self, pole_id: int) -> dict[str, Any]:
        return self._emit_telemetry(pole_id, duplicate=True)

    def delayed_telemetry(self, pole_id: int, delay_seconds: int = 120) -> dict[str, Any]:
        return self._emit_telemetry(pole_id, delayed=True, delay_seconds=delay_seconds)

    def missing_packets(self, pole_id: int) -> dict[str, Any]:
        self._record_simulation_log("missing_packets", {"pole_id": pole_id})
        self.db.commit()
        return {"status": "missing_packets", "pole_id": pole_id}

    def _emit_telemetry(self, pole_id: int, duplicate: bool = False, delayed: bool = False, delay_seconds: int = 120) -> dict[str, Any]:
        pole = self.db.get(Pole, pole_id)
        if pole is None:
            raise ValueError("Unknown pole")
        event_time = datetime.utcnow() - timedelta(seconds=delay_seconds) if delayed else datetime.utcnow()
        seq = random.randint(1000, 9999)
        telemetry = Telemetry(
            device_id=f"sim-{pole_id}",
            pole_id=pole_id,
            sequence_number=seq,
            event_type="heartbeat",
            power_lost=False,
            power_restored=False,
            firmware_version="1.2",
            received_at=datetime.utcnow(),
            event_time=event_time,
            source="simulator",
            stale_packet=delayed,
            is_out_of_order=duplicate,
            extra_metadata="{\"simulator\": true, \"duplicate\": false, \"delayed\": false}",
        )
        self.repository.save(telemetry)
        self._record_simulation_log("telemetry", {"pole_id": pole_id, "duplicate": duplicate, "delayed": delayed})
        return {"status": "telemetry", "pole_id": pole_id, "duplicate": duplicate, "delayed": delayed}

    def _create_fault_event(self, fault_type: str, pole_id: int | None = None, feeder_id: int | None = None) -> dict[str, Any]:
        fault = Fault(
            fault_type=fault_type,
            source_pole_id=pole_id,
            affected_pole_count=1,
            confidence_score=0.95,
            status="Detected",
            detected_at=datetime.utcnow(),
            topology_confidence=1.0,
            extra_metadata=f"{{\"fault_type\": \"{fault_type}\"}}",
        )
        self.db.add(fault)
        self._record_simulation_log(fault_type, {"pole_id": pole_id, "feeder_id": feeder_id})
        self.db.commit()
        return {"status": fault_type, "pole_id": pole_id, "feeder_id": feeder_id}

    def _record_simulation_log(self, event_type: str, payload: dict[str, Any]) -> None:
        self.db.add(SimulationLog(event_type=event_type, payload=str(payload), created_at=datetime.utcnow()))
