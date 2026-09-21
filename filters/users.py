from sqlmodel import SQLModel, Select
from typing import Optional, Type
from ..common.filters import BaseFilter


class UserFilter(BaseFilter):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None  # busca en email o full_name
    order_by_field: str = "created_at"
    order_desc: bool = True

    def apply(self, statement: Select, model: Type[SQLModel]) -> Select:
        if self.email:
            statement = statement.where(self._ilike(model.email, self.email))
        if self.full_name:
            statement = statement.where(self._ilike(model.full_name, self.full_name))
        if self.role:
            statement = statement.where(model.role == self.role)
        if self.is_active is not None:
            statement = statement.where(model.is_active == self.is_active)
        if self.search:
            statement = statement.where(
                (model.email.ilike(f"%{self.search}%"))
                | (model.full_name.ilike(f"%{self.search}%"))
            )
        return statement

    def order_by(self, model: Type[SQLModel]):
        column = getattr(model, self.order_by_field, model.created_at)
        return column.desc() if self.order_desc else column.asc()