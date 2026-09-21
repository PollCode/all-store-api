from fastapi import FastAPI
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .core.database import init_db
from .core.config import settings
from .api.v1.endpoints.users import router as user_router
from core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    
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

# Middlewares
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(user_router, prefix="/api/v1")

@app.get('/api/v1/health')
def health_check():
    return {"status": "OK", }