from typing import Optional
from sqlmodel import select
from ..models.users import User
from ..common.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.exec(select(User).where(User.email == email)).first()

    def get_existing_emails(self, emails: list[str]) -> list[str]:
        rows = self.db.exec(select(User.email).where(User.email.in_(emails))).all()
        return list(rows)