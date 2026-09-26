from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from repositories.token import RevokedAccessTokenRepository
from core.exceptions import UnauthorizedError
from core.database import get_session as get_db
from core.security import decode_access_token
from models.users import User
import uuid

# Esquema OAuth2 para extraer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError(message="Invalid token payload")
        user_uuid = uuid.UUID(user_id)
    except Exception:
        raise UnauthorizedError(message="Could not validate credentials")

    # ¿Está revocado?
    if RevokedAccessTokenRepository(db).is_revoked(token):
        raise UnauthorizedError(message="Token has been revoked")

    user = db.get(User, user_uuid)
    if not user:
        raise UnauthorizedError(message="User not found")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica que el usuario esté activo."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

def get_current_seller(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Verifica que el usuario tenga rol de vendedor."""
    if current_user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de vendedor"
        )
    return current_user

def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user