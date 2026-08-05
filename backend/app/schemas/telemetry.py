from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TelemetryIngest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    pole_id: int = Field(..., ge=1)
    sequence_number: int = Field(..., ge=0)
    event_type: Literal["heartbeat", "power_lost", "power_restored", "boot"] = "heartbeat"
    power_lost: bool = False
    power_restored: bool = False
    voltage: float | None = None
    current: float | None = None
    temperature: float | None = None
    firmware_version: str = "1.2"
    event_time: datetime
    source: str = "simulator"
    metadata: dict[str, object] | None = None

    @field_validator("firmware_version")
    @classmethod
    def normalize_firmware_version(cls, value: str) -> str:
        return value.strip() or "1.2"


class TelemetryResponse(BaseModel):
    id: int
    status: str
    pole_id: int
    device_id: str
    sequence_number: int
    event_type: str
    power_lost: bool
    power_restored: bool
    event_time: datetime
    received_at: datetime
    stale_packet: bool
    is_out_of_order: bool
    clock_skew_seconds: float | None = None
