from __future__ import annotations

from pydantic import BaseModel, Field


class FaultCreateRequest(BaseModel):
    fault_type: str = Field(..., pattern="span_fault|dt_fault|feeder_fault")
    source_pole_id: int | None = None
    affected_pole_count: int = 0
    confidence_score: float = 0.0
    topology_confidence: float = 1.0
    metadata: dict[str, object] | None = None


class FaultResponse(BaseModel):
    id: int
    fault_type: str
    source_pole_id: int | None
    affected_pole_count: int
    confidence_score: float
    topology_confidence: float
    status: str
