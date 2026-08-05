from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.network import Telemetry


class TelemetryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def latest_sequence_for_device(self, device_id: str, pole_id: int) -> int | None:
        result = (
            self.db.query(Telemetry.sequence_number)
            .filter(Telemetry.device_id == device_id)
            .filter(Telemetry.pole_id == pole_id)
            .order_by(Telemetry.sequence_number.desc())
            .first()
        )
        return result[0] if result else None

    def latest_event_for_pole(self, pole_id: int) -> Telemetry | None:
        return (
            self.db.query(Telemetry)
            .filter(Telemetry.pole_id == pole_id)
            .order_by(Telemetry.event_time.desc(), Telemetry.sequence_number.desc())
            .first()
        )

    def latest_heartbeat_for_device(self, device_id: str) -> Telemetry | None:
        return (
            self.db.query(Telemetry)
            .filter(Telemetry.device_id == device_id)
            .filter(Telemetry.event_type == "heartbeat")
            .order_by(Telemetry.event_time.desc())
            .first()
        )

    def has_duplicate(self, device_id: str, sequence_number: int, event_time: datetime) -> bool:
        return (
            self.db.query(Telemetry.id)
            .filter(Telemetry.device_id == device_id)
            .filter(Telemetry.sequence_number == sequence_number)
            .filter(Telemetry.event_time == event_time)
            .first()
            is not None
        )

    def save(self, payload: Telemetry) -> Telemetry:
        self.db.add(payload)
        self.db.commit()
        self.db.refresh(payload)
        return payload

    def is_stale(self, event_time: datetime, now: datetime | None = None, threshold: timedelta = timedelta(hours=2)) -> bool:
        now = now or datetime.utcnow()
        return (now - event_time) > threshold

    def get_recent_telemetry_snapshot(self, limit: int = 500) -> list[Telemetry]:
        return (
            self.db.query(Telemetry)
            .order_by(Telemetry.received_at.desc())
            .limit(limit)
            .all()
        )
