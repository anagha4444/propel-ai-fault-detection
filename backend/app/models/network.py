from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Pole(Base):
    __tablename__ = "poles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    feeder_id: Mapped[int | None] = mapped_column(ForeignKey("feeders.id"), nullable=True, index=True)
    transformer_id: Mapped[int | None] = mapped_column(ForeignKey("transformers.id"), nullable=True, index=True)
    parent_pole_id: Mapped[int | None] = mapped_column(ForeignKey("poles.id"), nullable=True, index=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    firmware_version: Mapped[str] = mapped_column(String(32), default="1.2")
    is_sensor_online: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    topology_confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=1.0)
    extra_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped["Pole | None"] = relationship("Pole", remote_side="Pole.id", foreign_keys=[parent_pole_id], back_populates="children")
    children: Mapped[list["Pole"]] = relationship("Pole", back_populates="parent", foreign_keys=[parent_pole_id])
    feeder: Mapped["Feeder | None"] = relationship("Feeder", back_populates="poles")
    transformer: Mapped["Transformer | None"] = relationship("Transformer", back_populates="poles")
    telemetry: Mapped[list["Telemetry"]] = relationship("Telemetry", back_populates="pole")
    downstream_faults: Mapped[list["Fault"]] = relationship("Fault", back_populates="source_pole")


class Transformer(Base):
    __tablename__ = "transformers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    feeder_id: Mapped[int | None] = mapped_column(ForeignKey("feeders.id"), nullable=True, index=True)
    parent_pole_id: Mapped[int | None] = mapped_column(ForeignKey("poles.id"), nullable=True, index=True)
    topology_confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=1.0)

    feeder: Mapped["Feeder | None"] = relationship("Feeder", back_populates="transformers")
    poles: Mapped[list[Pole]] = relationship("Pole", back_populates="transformer")


class Feeder(Base):
    __tablename__ = "feeders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    extra_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    poles: Mapped[list[Pole]] = relationship("Pole", back_populates="feeder")
    transformers: Mapped[list[Transformer]] = relationship("Transformer", back_populates="feeder")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    pole_id: Mapped[int] = mapped_column(ForeignKey("poles.id"), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), default="heartbeat", nullable=False, index=True)
    power_lost: Mapped[bool] = mapped_column(Boolean, default=False)
    power_restored: Mapped[bool] = mapped_column(Boolean, default=False)
    voltage: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    current: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    firmware_version: Mapped[str] = mapped_column(String(32), default="1.2")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="simulator")
    stale_packet: Mapped[bool] = mapped_column(Boolean, default=False)
    clock_skew_seconds: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    is_out_of_order: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    pole: Mapped[Pole] = relationship("Pole", back_populates="telemetry")


class Fault(Base):
    __tablename__ = "faults"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fault_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_pole_id: Mapped[int | None] = mapped_column(ForeignKey("poles.id"), nullable=True, index=True)
    affected_pole_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="Detected")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    topology_confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=1.0)
    extra_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_pole: Mapped[Pole | None] = relationship("Pole", back_populates="downstream_faults")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="fault")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fault_id: Mapped[int] = mapped_column(ForeignKey("faults.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="Detected")
    crew_assigned: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    extra_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    fault: Mapped[Fault] = relationship("Fault", back_populates="tickets")


class ScheduledOutage(Base):
    __tablename__ = "scheduled_outages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    feeder_id: Mapped[int | None] = mapped_column(ForeignKey("feeders.id"), nullable=True, index=True)
    pole_id: Mapped[int | None] = mapped_column(ForeignKey("poles.id"), nullable=True, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class SimulationLog(Base):
    __tablename__ = "simulation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
