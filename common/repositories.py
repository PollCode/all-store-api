import uuid
from typing import Generic, Optional, Sequence, Tuple, Type, TypeVar
from sqlmodel import Session, SQLModel, func, select
from ..common.schemas import PaginationParams
from ..common.filters import BaseFilter

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, obj_id: uuid.UUID) -> Optional[ModelT]:
        return self.db.get(self.model, obj_id)

    def get_many(self, ids: Sequence[uuid.UUID]) -> Sequence[ModelT]:
        statement = select(self.model).where(self.model.id.in_(ids))
        return self.db.exec(statement).all()

    def list(
        self,
        filters: BaseFilter,
        pagination: PaginationParams,
    ) -> Tuple[Sequence[ModelT], int]:
        filtered = filters.apply(select(self.model), self.model)
        total = self.db.exec(
            select(func.count()).select_from(filtered.subquery())
        ).one()
        statement = (
            filtered.order_by(filters.order_by(self.model))
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return self.db.exec(statement).all(), total

    def create(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def create_bulk(self, objs: Sequence[ModelT]) -> Sequence[ModelT]:
        self.db.add_all(objs)
        self.db.commit()
        for obj in objs:
            self.db.refresh(obj)
        return objs

    def update(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_bulk(self, objs: Sequence[ModelT]) -> Sequence[ModelT]:
        for obj in objs:
            self.db.add(obj)
        self.db.commit()
        for obj in objs:
            self.db.refresh(obj)
        return objs

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.commit()