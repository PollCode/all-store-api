from fastapi import APIRouter, Depends
from sqlmodel import Session
from api.dependencies import get_db, get_current_user

router = APIRouter()

@router.get("/mi-perfil")
def read_profile(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return current_user