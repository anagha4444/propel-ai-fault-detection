from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.network import Fault
from app.repositories.base import BaseRepository


class FaultRepository(BaseRepository[Fault]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Fault)
