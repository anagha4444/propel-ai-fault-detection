from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.simulator_service import SimulatorService

router = APIRouter(prefix="/simulator", tags=["simulator"])


class SimulatorActionRequest(BaseModel):
    pole_id: int | None = Field(default=None, ge=1)
    feeder_id: int | None = Field(default=None, ge=1)
    duration_minutes: int = Field(default=60, ge=1)
    delay_seconds: int = Field(default=120, ge=1)


@router.post("/span-fault", status_code=status.HTTP_201_CREATED)
def span_fault(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "span_fault", request)


@router.post("/dt-fault", status_code=status.HTTP_201_CREATED)
def dt_fault(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "dt_fault", request)


@router.post("/feeder-fault", status_code=status.HTTP_201_CREATED)
def feeder_fault(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "feeder_fault", request)


@router.post("/device-failure", status_code=status.HTTP_201_CREATED)
def device_failure(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "device_failure", request)


@router.post("/scheduled-outage", status_code=status.HTTP_201_CREATED)
def scheduled_outage(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "scheduled_outage", request)


@router.post("/repair", status_code=status.HTTP_201_CREATED)
def repair(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "repair", request)


@router.post("/duplicate-telemetry", status_code=status.HTTP_201_CREATED)
def duplicate_telemetry(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "duplicate_telemetry", request)


@router.post("/delayed-telemetry", status_code=status.HTTP_201_CREATED)
def delayed_telemetry(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "delayed_telemetry", request)


@router.post("/missing-packets", status_code=status.HTTP_201_CREATED)
def missing_packets(request: SimulatorActionRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    return _run_simulator_action(db, "missing_packets", request)


def _run_simulator_action(db: Session, action: str, request: SimulatorActionRequest) -> dict[str, object]:
    service = SimulatorService(db)
    try:
        if action == "span_fault":
            return service.span_fault(request.pole_id or 1)
        if action == "dt_fault":
            return service.dt_fault(request.pole_id or 1)
        if action == "feeder_fault":
            return service.feeder_fault(request.feeder_id or 1)
        if action == "device_failure":
            return service.device_failure(request.pole_id or 1)
        if action == "scheduled_outage":
            return service.scheduled_outage(request.pole_id or 1, request.duration_minutes)
        if action == "repair":
            return service.repair(request.pole_id or 1)
        if action == "duplicate_telemetry":
            return service.duplicate_telemetry(request.pole_id or 1)
        if action == "delayed_telemetry":
            return service.delayed_telemetry(request.pole_id or 1, request.delay_seconds)
        if action == "missing_packets":
            return service.missing_packets(request.pole_id or 1)
        raise ValueError("Unsupported simulator action")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
