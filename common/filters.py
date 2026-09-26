from typing import Optional, Type
from pydantic import BaseModel, ConfigDict
from sqlmodel import SQLModel
from sqlalchemy import Select

class BaseFilter(BaseModel):
    """
    Clase base para filtros de modelos.
    Cada modelo extiende esta clase y sobreescribe `apply` y `order_by`.
    """

    model_config = ConfigDict(extra="forbid")

    def apply(self, statement: Select, model: Type[SQLModel]) -> Select:
        """Aplica condiciones WHERE. Sobreescribir en subclases."""
        return statement

    def order_by(self, model: Type[SQLModel]):
        """Orden por defecto. Sobreescribir en subclases."""
        return model.created_at.desc()

    def _ilike(self, column, value: Optional[str]):
        return column.ilike(f"%{value}%") if value else None


