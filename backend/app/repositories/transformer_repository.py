from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.network import Transformer
from app.repositories.base import BaseRepository


class TransformerRepository(BaseRepository[Transformer]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Transformer)
