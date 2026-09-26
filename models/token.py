import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field
from common.models import BaseModel


class RefreshToken(BaseModel, table=True):
    __tablename__ = "refresh_tokens"

    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    revoked: bool = Field(default=False, index=True)
    revoked_at: Optional[datetime] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)


class RevokedAccessToken(BaseModel, table=True):
    __tablename__ = "revoked_access_tokens"

    token: str = Field(unique=True, index=True)
    expires_at: datetime = Field(index=True)