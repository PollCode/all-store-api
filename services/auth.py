from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlmodel import Session

from ..core.config import settings
from ..core.exceptions import UnauthorizedError
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    verify_password,
)
from ..models.token import RefreshToken, RevokedAccessToken
from ..repositories.token import RefreshTokenRepository, RevokedAccessTokenRepository
from ..repositories.users import UserRepository
from ..schemas.auth import TokenResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.revoked_tokens = RevokedAccessTokenRepository(db)

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _issue_tokens(self, user, request: Optional[Request] = None) -> TokenResponse:
        """Genera access + refresh token y persiste el refresh en BD."""
        access_token = create_access_token(str(user.id), user.role)
        refresh_str = create_refresh_token(str(user.id))

        payload = decode_refresh_token(refresh_str)
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        self.refresh_tokens.create(
            RefreshToken(
                user_id=user.id,
                token=refresh_str,
                expires_at=expires_at,
                user_agent=request.headers.get("user-agent") if request else None,
                ip_address=(request.client.host if request and request.client else None),
            )
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_str,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # Públicos
    # ------------------------------------------------------------------
    def login(
        self, email: str, password: str, request: Optional[Request] = None
    ) -> TokenResponse:
        user = self.users.get_by_email(email)
        print(user)
        if not user:
            raise UnauthorizedError(message="Invalid email")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError(message="Invalid password")
        if not user.is_active:
            raise UnauthorizedError(message="User account is inactive")
        return self._issue_tokens(user, request)

    def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            decode_refresh_token(refresh_token)
        except Exception:
            raise UnauthorizedError(message="Invalid or expired refresh token")

        stored = self.refresh_tokens.get_by_token(refresh_token)
        if not stored or stored.revoked:
            raise UnauthorizedError(message="Refresh token has been revoked")

        if stored.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedError(message="Refresh token has expired")

        user = self.users.get(stored.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError(message="User not found or inactive")

        # Rotación: revocamos el refresh usado y emitimos uno nuevo
        self.refresh_tokens.revoke(stored)

        return self._issue_tokens(user)

    def logout(
        self,
        access_token: str,
        refresh_token: Optional[str],
        user_id,
        all_devices: bool = False,
    ) -> None:
        # 1. Blacklist del access token actual hasta su expiración
        try:
            payload = decode_access_token(access_token)
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        except Exception:
            exp = datetime.now(timezone.utc)

        if not self.revoked_tokens.is_revoked(access_token):
            self.revoked_tokens.create(
                RevokedAccessToken(token=access_token, expires_at=exp)
            )

        # 2. Revocar refresh tokens
        if all_devices:
            self.refresh_tokens.revoke_all_for_user(user_id)
        elif refresh_token:
            stored = self.refresh_tokens.get_by_token(refresh_token)
            if stored and not stored.revoked:
                self.refresh_tokens.revoke(stored)