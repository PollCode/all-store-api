import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlmodel import Session
from .core.database import init_db
from .core.config import settings
from .core.seed import create_default_admin
from .core.rate_limit import limiter
from .core.database import engine
from .core.exception_handlers import register_exception_handlers
from .api.v1.endpoints.users import router as user_router
from .api.v1.endpoints.auth import router as auth_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup ----
    logger.info("Starting up...")
    init_db()
    try:
        with Session(engine) as db:
            create_default_admin(db)
    except Exception:
        logger.exception("Failed to seed default admin")

    yield

    # ---- Shutdown ----
    logger.info("Shutting down...")
    
app = FastAPI(
    title="All Store API",
    #root_path=settings.BASE_URL,
    #root_path_in_servers=False,
    lifespan=lifespan,
    version="0.1.0",
    openapi_url="/api/openapi.json",   
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers
register_exception_handlers(app)

# Middlewares
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(user_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.get('/api/v1/health')
def health_check():
    return {"status": "OK", }