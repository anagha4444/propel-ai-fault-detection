from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.network import SimulationLog
from app.repositories.base import BaseRepository


class SimulationLogRepository(BaseRepository[SimulationLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SimulationLog)
