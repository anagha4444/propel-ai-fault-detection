from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.network import Telemetry
from app.schemas.telemetry import TelemetryIngest, TelemetryResponse
from app.services.telemetry_pipeline_service import TelemetryPipelineService

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("", response_model=list[TelemetryResponse])
def list_recent_telemetry(db: Session = Depends(get_db)) -> list[TelemetryResponse]:
    records = db.query(Telemetry).order_by(Telemetry.received_at.desc()).limit(50).all()
    return [
        TelemetryResponse(
            id=record.id,
            status=record.event_type,
            pole_id=record.pole_id,
            device_id=record.device_id,
            sequence_number=record.sequence_number,
            event_type=record.event_type,
            power_lost=record.power_lost,
            power_restored=record.power_restored,
            event_time=record.event_time,
            received_at=record.received_at,
            stale_packet=record.stale_packet,
            is_out_of_order=record.is_out_of_order,
            clock_skew_seconds=float(record.clock_skew_seconds) if record.clock_skew_seconds is not None else None,
        )
        for record in records
    ]


@router.post("", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
def ingest_telemetry(payload: TelemetryIngest, db: Session = Depends(get_db)) -> TelemetryResponse:
    service = TelemetryPipelineService(db)
    try:
        result = service.ingest(payload.model_dump(mode="python"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return TelemetryResponse(
        id=0,
        status=result["status"],
        pole_id=payload.pole_id,
        device_id=payload.device_id,
        sequence_number=payload.sequence_number,
        event_type=result["event_type"],
        power_lost=payload.power_lost,
        power_restored=payload.power_restored,
        event_time=payload.event_time,
        received_at=payload.event_time,
        stale_packet=bool(result.get("stale_packet")),
        is_out_of_order=bool(result.get("is_out_of_order")),
        clock_skew_seconds=result.get("clock_skew_seconds"),
    )
