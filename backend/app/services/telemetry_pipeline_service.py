from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.network import Feeder, Pole, ScheduledOutage, Telemetry, Transformer
from app.repositories.telemetry_repository import TelemetryRepository
from app.services.fault_localization_service import FaultLocalizationService
from app.services.topology_service import TopologyGraphService

logger = logging.getLogger(__name__)


class TelemetryPipelineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = TelemetryRepository(db)
        self.localization = FaultLocalizationService()
        self.topology = TopologyGraphService()

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        pole = self.db.query(Pole).filter(Pole.id == payload["pole_id"]).first()
        if pole is None:
            raise ValueError("Unknown pole")

        now = datetime.utcnow()
        event_time = payload["event_time"]
        device_id = payload["device_id"]
        sequence_number = payload["sequence_number"]
        firmware_version = payload.get("firmware_version", "1.2")
        latest_sequence = self.repository.latest_sequence_for_device(device_id, payload["pole_id"])
        duplicate = self.repository.has_duplicate(device_id, sequence_number, event_time)
        stale = self.repository.is_stale(event_time, now=now, threshold=timedelta(hours=2))
        clock_skew = self._calculate_clock_skew(event_time, now)
        out_of_order = latest_sequence is not None and sequence_number < latest_sequence
        event_type = self._normalize_event_type(payload, firmware_version)

        if duplicate:
            logger.info("Duplicate telemetry drop for device %s seq %s", device_id, sequence_number)
            return {
                "status": "duplicate",
                "stored": False,
                "event_type": event_type,
                "stale_packet": stale,
                "is_out_of_order": out_of_order,
                "clock_skew_seconds": clock_skew,
            }

        if out_of_order:
            logger.warning("Out-of-order telemetry for device %s pole %s", device_id, payload["pole_id"])

        if stale:
            logger.warning("Stale telemetry for device %s pole %s", device_id, payload["pole_id"])

        if event_type == "boot":
            pole.is_sensor_online = True
        elif event_type == "power_lost":
            pole.is_sensor_online = False
        elif event_type == "power_restored":
            pole.is_sensor_online = True

        telemetry = Telemetry(
            device_id=device_id,
            pole_id=payload["pole_id"],
            sequence_number=sequence_number,
            event_type=event_type,
            power_lost=bool(payload.get("power_lost")) or event_type == "power_lost",
            power_restored=bool(payload.get("power_restored")) or event_type == "power_restored",
            voltage=payload.get("voltage"),
            current=payload.get("current"),
            temperature=payload.get("temperature"),
            firmware_version=firmware_version,
            received_at=now,
            event_time=event_time,
            source=payload.get("source", "simulator"),
            stale_packet=stale,
            clock_skew_seconds=clock_skew,
            is_out_of_order=out_of_order,
            extra_metadata=str(payload.get("metadata")) if payload.get("metadata") else None,
        )

        self.repository.save(telemetry)

        if self._should_trigger_localization(payload["pole_id"]):
            self._trigger_localization_for_pole(payload["pole_id"])

        pole.last_seen_at = now
        self.db.commit()

        return {
            "status": "accepted",
            "stored": True,
            "event_type": event_type,
            "stale_packet": stale,
            "is_out_of_order": out_of_order,
            "clock_skew_seconds": clock_skew,
        }

    def _normalize_event_type(self, payload: dict[str, Any], firmware_version: str) -> str:
        event_type = payload.get("event_type")
        if event_type in {"heartbeat", "power_lost", "power_restored", "boot"}:
            return event_type
        if payload.get("power_lost"):
            return "power_lost"
        if payload.get("power_restored"):
            return "power_restored"
        if firmware_version.startswith("1.2"):
            return "heartbeat"
        return "heartbeat"

    def _calculate_clock_skew(self, event_time: datetime, now: datetime) -> float:
        return round((now - event_time).total_seconds(), 3)

    def _should_trigger_localization(self, pole_id: int) -> bool:
        outage = (
            self.db.query(ScheduledOutage)
            .filter(ScheduledOutage.active.is_(True))
            .filter((ScheduledOutage.pole_id == pole_id) | (ScheduledOutage.feeder_id == self.db.query(Pole.feeder_id).filter(Pole.id == pole_id).scalar()))
            .first()
        )
        return outage is None

    def _trigger_localization_for_pole(self, pole_id: int) -> None:
        logger.info("Triggering localization for pole %s", pole_id)
        poles = self.db.query(Pole).all()
        transformers = self.db.query(Transformer).all()
        feeders = self.db.query(Feeder).all()
        telemetry = {
            record.pole_id: {
                "power_lost": record.power_lost,
                "power_restored": record.power_restored,
                "event_time": record.event_time,
            }
            for record in self.repository.get_recent_telemetry_snapshot(limit=500)
        }
        scheduled_outages = {
            row.pole_id for row in self.db.query(ScheduledOutage).filter(ScheduledOutage.active.is_(True)).all() if row.pole_id is not None
        }
        graph = self.topology.load_graph(
            poles=[
                {
                    "id": pole.id,
                    "feeder_id": pole.feeder_id,
                    "transformer_id": pole.transformer_id,
                    "parent_pole_id": pole.parent_pole_id,
                    "latitude": float(pole.latitude),
                    "longitude": float(pole.longitude),
                    "topology_confidence": float(pole.topology_confidence),
                }
                for pole in poles
            ],
            transformers=[
                {
                    "id": transformer.id,
                    "feeder_id": transformer.feeder_id,
                    "parent_pole_id": transformer.parent_pole_id,
                    "latitude": float(transformer.latitude),
                    "longitude": float(transformer.longitude),
                    "topology_confidence": float(transformer.topology_confidence),
                }
                for transformer in transformers
            ],
            feeders=[
                {
                    "id": feeder.id,
                    "name": feeder.name,
                    "latitude": float(feeder.latitude),
                    "longitude": float(feeder.longitude),
                }
                for feeder in feeders
            ],
        )
        incidents = self.localization.localize(graph, telemetry, scheduled_outages, now=datetime.utcnow())
        if incidents:
            logger.info("Localization produced %s incidents", len(incidents))
