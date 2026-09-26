from fastapi import APIRouter, Depends, Request, status
from sqlmodel import Session

from api.dependencies import get_current_active_user, get_db, oauth2_scheme
from core.rate_limit import limiter
from models.users import User
from schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión y obtener tokens JWT",
)
@limiter.limit("10/minute")
def login(
    request: Request,
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.login(data.email, data.password, request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token usando un refresh token",
)
@limiter.limit("30/minute")
def refresh(
    request: Request,
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.refresh(data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión (revoca el access token y opcionalmente los refresh tokens)",
)
@limiter.limit("30/minute")
def logout(
    request: Request,
    data: LogoutRequest,
    access_token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
):
    service.logout(
        access_token=access_token,
        refresh_token=data.refresh_token,
        user_id=current_user.id,
        all_devices=data.all_devices,
    )
    return None