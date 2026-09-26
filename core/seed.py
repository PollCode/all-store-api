import logging

from sqlmodel import Session, select

from core.config import settings
from core.security import hash_password
from models.users import User

logger = logging.getLogger(__name__)


def create_default_admin(db: Session) -> None:
    """
    Crea un usuario admin por defecto si no existe ninguno con
    el email configurado en DEFAULT_ADMIN_EMAIL.

    Es idempotente: si ya existe, no hace nada.
    """
    if not settings.CREATE_DEFAULT_ADMIN:
        logger.info("Default admin creation disabled (CREATE_DEFAULT_ADMIN=false)")
        return

    email = settings.DEFAULT_ADMIN_EMAIL.strip().lower()

    existing = db.exec(select(User).where(User.email == email)).first()
    if existing:
        logger.info("Default admin already exists: %s", email)
        return

    admin = User(
        email=email,
        password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
        full_name=settings.DEFAULT_ADMIN_FULL_NAME,
        role="admin",
        is_active=True,
        created_by="system",
        updated_by="system",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.warning(
        "✅ Default admin created: %s (id=%s). CHANGE THE PASSWORD IMMEDIATELY.",
        admin.email,
        admin.id,
    )