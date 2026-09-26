"""Helpers para crear datos de prueba."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from core.security import create_access_token, create_refresh_token, hash_password
from models.token import RefreshToken
from models.users import User


def make_user(
    db: Session,
    *,
    email: Optional[str] = None,
    password: str = "Password123!",
    full_name: str = "Test User",
    role: str = "buyer",
    is_active: bool = True,
) -> User:
    """Crea un usuario en la BD de test y lo devuelve."""
    email = email or f"user-{uuid.uuid4().hex[:8]}@test.com"
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_access_token(user: User) -> str:
    return create_access_token(str(user.id), user.role)


def make_refresh_token(db: Session, user: User) -> str:
    """Crea y persiste un refresh token válido."""
    token_str = create_refresh_token(str(user.id))
    from core.security import decode_refresh_token

    payload = decode_refresh_token(token_str)
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    db.add(
        RefreshToken(
            user_id=user.id,
            token=token_str,
            expires_at=expires_at,
            revoked=False,
        )
    )
    db.commit()
    return token_str