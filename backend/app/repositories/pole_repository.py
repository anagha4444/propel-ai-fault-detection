from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.network import Pole
from app.repositories.base import BaseRepository


class PoleRepository(BaseRepository[Pole]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Pole)

    def by_feeder(self, feeder_id: int) -> list[Pole]:
        return self.db.query(Pole).filter(Pole.feeder_id == feeder_id).all()

    def by_transformer(self, transformer_id: int) -> list[Pole]:
        return self.db.query(Pole).filter(Pole.transformer_id == transformer_id).all()
