from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: type[ModelType]) -> None:
        self.db = db
        self.model = model

    def create(self, payload: ModelType) -> ModelType:
        self.db.add(payload)
        self.db.commit()
        self.db.refresh(payload)
        return payload

    def get_by_id(self, object_id: int) -> ModelType | None:
        return self.db.get(self.model, object_id)

    def get_all(self) -> list[ModelType]:
        return self.db.query(self.model).all()

    def update(self, payload: ModelType) -> ModelType:
        self.db.add(payload)
        self.db.commit()
        self.db.refresh(payload)
        return payload

    def delete(self, payload: ModelType) -> None:
        self.db.delete(payload)
        self.db.commit()
