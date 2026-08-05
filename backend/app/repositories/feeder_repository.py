from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.network import Feeder
from app.repositories.base import BaseRepository


class FeederRepository(BaseRepository[Feeder]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Feeder)
