import uuid
from typing import List, Sequence, Tuple
from fastapi import HTTPException, status
from sqlmodel import Session
from core.exceptions import ConflictError, NotFoundError, BadRequestError
from core.security import hash_password
from models.users import User
from repositories.users import UserRepository
from common.schemas import PaginationParams
from filters.users import UserFilter
from schemas.users import UserBulkUpdate, UserCreate, UserUpdate

VALID_ROLES = {"buyer", "seller", "admin"}


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    # ---------- Create ----------
    def create(self, data: UserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise ConflictError(
                message=f"Email '{data.email}' already registered",
                details={"field": "email", "value": data.email},
            )
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=data.is_active,
        )
        return self.repo.create(user)

    def create_bulk(self, data: List[UserCreate]) -> Sequence[User]:
        emails = [d.email for d in data]
        if len(emails) != len(set(emails)):
            raise BadRequestError(
                message="Duplicate emails in payload",
            )
        existing = self.repo.get_existing_emails(emails)
        if existing:
            raise ConflictError(
                message=f"Emails already registered",
                details={"field": "email", "value": existing},
            )
        users = [
            User(
                email=d.email,
                password_hash=hash_password(d.password),
                full_name=d.full_name,
                role=d.role,
                is_active=d.is_active,
            )
            for d in data
        ]
        return self.repo.create_bulk(users)

    # ---------- Read ----------
    def list(
        self, filters: UserFilter, pagination: PaginationParams
    ) -> Tuple[Sequence[User], int]:
        return self.repo.list(filters, pagination)

    def get(self, user_id: uuid.UUID) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError(
                message=f"User '{user_id}' not found",
            )
        return user

    # ---------- Update ----------
    def update(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        user = self.get(user_id)
        payload = data.model_dump(exclude_unset=True, exclude_none=True)

        if "password" in payload:
            payload["password_hash"] = hash_password(payload.pop("password"))

        if "email" in payload and payload["email"] != user.email:
            if self.repo.get_by_email(payload["email"]):
                raise ConflictError(
                    message=f"Email already registered",
                    details={"field": "email", "value": payload['email']}
                )

        for key, value in payload.items():
            setattr(user, key, value)
        return self.repo.update(user)

    def update_bulk(self, data: List[UserBulkUpdate]) -> Sequence[User]:
        ids = [d.id for d in data]
        if len(ids) != len(set(ids)):
            raise BadRequestError(message="Duplicate IDs in payload")

        users = self.repo.get_many(ids)
        users_map = {u.id: u for u in users}

        missing = set(ids) - set(users_map.keys())
        if missing:
            raise NotFoundError(
                message=f"Users not found",
                details={"field": "id", "value": sorted(missing)}   
            )

        # Verificar emails duplicados dentro del payload
        new_emails = [d.email for d in data if d.email]
        if len(new_emails) != len(set(new_emails)):
            raise BadRequestError(message="Duplicate emails in payload")

        # Verificar emails ya usados por otros
        existing = self.repo.get_existing_emails(new_emails)
        for d in data:
            if d.email and d.email in existing:
                current = users_map[d.id]
                if current.email != d.email:
                    raise ConflictError(
                        message=f"Email already registered",
                        details={"field": "email", "value": d.email}
                    )

        for item in data:
            user = users_map[item.id]
            payload = item.model_dump(exclude={"id"}, exclude_unset=True, exclude_none=True)
            if "password" in payload:
                payload["password_hash"] = hash_password(payload.pop("password"))
            for key, value in payload.items():
                setattr(user, key, value)

        return self.repo.update_bulk(list(users_map.values()))

    # ---------- Delete ----------
    def delete(self, user_id: uuid.UUID) -> None:
        user = self.get(user_id)
        self.repo.delete(user)