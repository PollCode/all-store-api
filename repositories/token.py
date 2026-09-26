import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import select

from ..models.token import RefreshToken, RevokedAccessToken
from ..common.repositories import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        return self.db.exec(
            select(RefreshToken).where(RefreshToken.token == token)
        ).first()

    def revoke(self, token_obj: RefreshToken) -> RefreshToken:
        token_obj.revoked = True
        token_obj.revoked_at = datetime.now(timezone.utc)
        return self.update(token_obj)

    def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,  # noqa: E712
        )
        tokens = self.db.exec(stmt).all()
        now = datetime.now(timezone.utc)
        for t in tokens:
            t.revoked = True
            t.revoked_at = now
            self.db.add(t)
        self.db.commit()
        return len(tokens)


class RevokedAccessTokenRepository(BaseRepository[RevokedAccessToken]):
    model = RevokedAccessToken

    def is_revoked(self, token: str) -> bool:
        return (
            self.db.exec(
                select(RevokedAccessToken).where(RevokedAccessToken.token == token)
            ).first()
            is not None
        )

    def cleanup_expired(self) -> int:
        """Elimina tokens revocados que ya expiraron. Útil para tareas programadas."""
        now = datetime.now(timezone.utc)
        stmt = select(RevokedAccessToken).where(RevokedAccessToken.expires_at < now)
        expired = self.db.exec(stmt).all()
        for t in expired:
            self.db.delete(t)
        self.db.commit()
        return len(expired)