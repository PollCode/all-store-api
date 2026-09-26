from sqlmodel import SQLModel, Session, create_engine
from core.config import settings

# Motor de base de datos (PostgreSQL)
engine = create_engine(
    settings.DB_URL,
    pool_pre_ping=True,   # Verifica que las conexiones estén activas antes de usarlas
    echo=False,           # Cambia a True para ver SQL en consola (debug)
)

def init_db():
    # ⚠️ ELIMINA TODOS LOS DATOS EXISTENTES
    # SQLModel.metadata.drop_all(engine)  
    SQLModel.metadata.create_all(engine,checkfirst=True)

def get_session():
    """
    Dependencia para obtener una sesión de base de datos.
    Se cierra automáticamente al finalizar la solicitud.
    """
    with Session(engine) as session:
        yield session