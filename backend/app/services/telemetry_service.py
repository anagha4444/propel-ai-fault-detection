from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.network import Pole, Telemetry
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.telemetry import TelemetryIngest

logger = logging.getLogger(__name__)


class TelemetryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TelemetryRepository(db)

    def ingest(self, payload: TelemetryIngest) -> dict[str, object]:
        pole = self.db.query(Pole).filter(Pole.id == payload.pole_id).first()
        if pole is None:
            raise ValueError("Unknown pole")

        stale = self.repository.is_stale(payload.event_time)
        latest_sequence = self.repository.latest_sequence_for_pole(payload.pole_id)
        duplicate = self.repository.has_duplicate(payload.pole_id, payload.sequence_number, payload.event_time)

        if duplicate:
            return {"status": "duplicate", "stored": False}

        if latest_sequence is not None and payload.sequence_number < latest_sequence:
            logger.warning("Out-of-order telemetry received for pole %s", payload.pole_id)

        if stale:
            logger.warning("Stale packet received for pole %s", payload.pole_id)

        telemetry = Telemetry(
            pole_id=payload.pole_id,
            sequence_number=payload.sequence_number,
            power_lost=payload.power_lost,
            power_restored=payload.power_restored,
            voltage=payload.voltage,
            current=payload.current,
            temperature=payload.temperature,
            firmware_version=payload.firmware_version,
            event_time=payload.event_time,
            received_at=datetime.utcnow(),
            source=payload.source,
            stale_packet=stale,
            extra_metadata=str(payload.metadata) if payload.metadata else None,
        )

        self.repository.save(telemetry)
        pole.last_seen_at = telemetry.received_at
        pole.is_sensor_online = not payload.power_lost
        self.db.commit()

        return {
            "status": "accepted",
            "stored": True,
            "stale_packet": stale,
            "sequence_number": payload.sequence_number,
        }
