from sqlmodel import Field
from common.models import BaseModel


class User(BaseModel, table=True):
    __tablename__ = "users"
    
    email: str = Field(index=True, unique=True)
    password_hash: str = Field()
    full_name: str = Field()
    role: str
    is_active: bool = Field(default=True)
        