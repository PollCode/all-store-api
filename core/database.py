from sqlmodel import Session, create_engine
from core.config import settings

# Motor de base de datos (PostgreSQL)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # Verifica que las conexiones estén activas antes de usarlas
    echo=False,           # Cambia a True para ver SQL en consola (debug)
)

def get_session():
    """
    Dependencia para obtener una sesión de base de datos.
    Se cierra automáticamente al finalizar la solicitud.
    """
    with Session(engine) as session:
        yield session