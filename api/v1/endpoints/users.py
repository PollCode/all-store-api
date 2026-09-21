import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from api.dependencies import get_current_active_user, get_db, require_admin
from core.rate_limit import limiter
from ....models.users import User
from ....common.schemas import PaginatedResponse, PaginationParams
from ....filters.users import UserFilter
from ....schemas.users import (
    UserBulkCreateResponse,
    UserBulkUpdate,
    UserBulkUpdateResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from ....services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


# -------------------- CREATE --------------------
@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un usuario",
)
@limiter.limit("20/minute")
def create_user(
    request: Request,
    data: UserCreate,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
):
    return service.create(data)


@router.post(
    "/bulk",
    response_model=UserBulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear varios usuarios a la vez",
)
@limiter.limit("5/minute")
def create_users_bulk(
    request: Request,
    data: List[UserCreate],
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
):
    users = service.create_bulk(data)
    return UserBulkCreateResponse(created=len(users), items=users)


# -------------------- READ --------------------
@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    summary="Listar usuarios con filtros y paginación",
)
@limiter.limit("60/minute")
def list_users(
    request: Request,
    filters: UserFilter = Depends(),
    pagination: PaginationParams = Depends(),
    service: UserService = Depends(get_user_service),
    _: User = Depends(get_current_active_user),
):
    items, total = service.list(filters, pagination)
    return PaginatedResponse[UserRead].from_items(items, total, pagination)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Obtener un usuario por ID",
)
@limiter.limit("60/minute")
def get_user(
    request: Request,
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
    _: User = Depends(get_current_active_user),
):
    return service.get(user_id)


# -------------------- UPDATE --------------------
@router.patch(
    "/bulk",
    response_model=UserBulkUpdateResponse,
    summary="Modificar varios usuarios a la vez",
)
@limiter.limit("5/minute")
def update_users_bulk(
    request: Request,
    data: List[UserBulkUpdate],
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
):
    users = service.update_bulk(data)
    return UserBulkUpdateResponse(updated=len(users), items=users)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Modificar un usuario",
)
@limiter.limit("20/minute")
def update_user(
    request: Request,
    user_id: uuid.UUID,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(403, "Not enough permissions")
    return service.update(user_id, data)


# -------------------- DELETE --------------------
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un usuario",
)
@limiter.limit("20/minute")
def delete_user(
    request: Request,
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_admin),
):
    service.delete(user_id)
    return None