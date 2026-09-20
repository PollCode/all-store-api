from fastapi import FastAPI
from contextlib import asynccontextmanager
from .core.database import init_db
from .core.config import settings

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

@app.get('/health')
def health_check():
    return {"status": "OK", }