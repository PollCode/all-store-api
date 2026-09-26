"""
Configuración global de pytest.

Se usan dos estrategias clave:
1. SQLite en memoria con StaticPool → cada test comparte la misma conexión.
2. Override de `get_db` → los endpoints usan la sesión de test.
3. Desactivación de rate limiting → para no bloquear los tests.
"""
import os

# --- Variables de entorno ANTES de importar la app ---
os.environ["CREATE_DEFAULT_ADMIN"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-only-for-tests"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_MINUTES"] = "10080"
os.environ["DATABASE_URL"] = "sqlite://"

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from main import app

from core.database import get_db
from core.rate_limit import limiter

# ------------------------------------------------------------------
# Base de datos de prueba (SQLite en memoria, compartida)
# ------------------------------------------------------------------
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="session", autouse=True)
def _setup_schema():
    """Crea el esquema una sola vez por sesión de tests."""
    # Importa los modelos para que SQLModel los registre
    import models  # noqa: F401

    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(autouse=True)
def _clean_tables(_setup_schema):
    """Limpia las tablas entre tests para garantizar aislamiento."""
    yield
    with Session(test_engine) as session:
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.exec(table.delete())  # type: ignore[arg-type]
        session.commit()


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Sesión de base de datos para usar directamente en tests/factories."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    TestClient con `get_db` sobreescrito para usar la sesión de test.
    No usamos `with` para evitar que corra el lifespan (seeder incluido).
    """
    limiter.enabled = False  # desactiva rate limiting en tests

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()
        limiter.enabled = True


# ------------------------------------------------------------------
# Factories
# ------------------------------------------------------------------
from ..tests.factories import make_access_token, make_user  # noqa: E402


@pytest.fixture
def admin_user(db: Session):
    return make_user(
        db,
        email="admin@test.com",
        password="AdminPass123!",
        full_name="Admin",
        role="admin",
    )


@pytest.fixture
def buyer_user(db: Session):
    return make_user(
        db,
        email="buyer@test.com",
        password="BuyerPass123!",
        full_name="Buyer",
        role="buyer",
    )


@pytest.fixture
def seller_user(db: Session):
    return make_user(
        db,
        email="seller@test.com",
        password="SellerPass123!",
        full_name="Seller",
        role="seller",
    )


@pytest.fixture
def admin_headers(admin_user):
    token = make_access_token(admin_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def buyer_headers(buyer_user):
    token = make_access_token(buyer_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seller_headers(seller_user):
    token = make_access_token(seller_user)
    return {"Authorization": f"Bearer {token}"}