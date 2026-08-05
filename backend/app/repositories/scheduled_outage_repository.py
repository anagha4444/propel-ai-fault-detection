from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.network import ScheduledOutage
from app.repositories.base import BaseRepository


class ScheduledOutageRepository(BaseRepository[ScheduledOutage]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ScheduledOutage)
