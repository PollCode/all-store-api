import uuid
from sqlmodel import SQLModel, Field
from sqlalchemy import func
from datetime import datetime


class BaseModel(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda:datetime.now()) 
    created_by: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(),sa_column_kwargs={"onupdate": func.now()})
    updated_by: str | None = Field(default=None)
