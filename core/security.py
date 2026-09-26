import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

from ..core.config import settings

# Instancia global de PasswordHasher de argon2
ph = PasswordHasher()

# --- Funciones de hash de contraseñas ---

def hash_password(password: str) -> str:
    """Devuelve el hash de la contraseña usando Argon2."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHashError):
        return False

# --- Funciones de tokens JWT ---

def _create_token(user_id: str, role: Optional[str], token_type: str, expires_delta: timedelta) -> str:
    """Crea un token JWT con claims comunes."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),          # Identificador del usuario
        "type": token_type,           # "access" o "refresh"
        "iat": now,                   # Fecha de emisión
        "exp": now + expires_delta,   # Fecha de expiración
    }
    if role is not None:
        payload["role"] = role

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(user_id: str, role: str) -> str:
    """Genera un token de acceso de corta duración."""
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(user_id, role, "access", expires)

def create_refresh_token(user_id: str) -> str:
    """Genera un token de refresco de larga duración."""
    expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return _create_token(user_id, None, "refresh", expires)

def decode_token(token: str, expected_type: Optional[str] = None) -> dict:
    """
    Decodifica y valida un token JWT.
    - Verifica firma y expiración.
    - Si se proporciona expected_type, comprueba que el claim "type" coincida.
    Lanza jwt.PyJWTError si algo falla.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Token type mismatch: expected '{expected_type}'")
    return payload

def decode_access_token(token: str) -> dict:
    """Decodifica un token de acceso."""
    return decode_token(token, expected_type="access")

def decode_refresh_token(token: str) -> dict:
    """Decodifica un token de refresco."""
    return decode_token(token, expected_type="refresh")