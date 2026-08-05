from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.network import Ticket
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Ticket)
