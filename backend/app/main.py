from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import load_config
from app.core.logging_config import setup_logging

setup_logging()

from app.api import routes
from app.api import auth
from app.api import sessions
from app.api import skills
from app.api.v1 import api_router as v1_router
from app.core.rate_limit import login_limiter, api_limiter
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="实验室智能助手 - 后端",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

cfg = load_config()
cors_origins = cfg.get("cors_allowed_origins", ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if "/api/auth/login" in request.url.path or "/api/v1/auth/login" in request.url.path:
        await login_limiter(request)
    else:
        await api_limiter(request)
    
    response = await call_next(request)
    return response


app.include_router(v1_router, prefix="/api/v1")

app.include_router(routes.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(skills.router, prefix="/api")

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "实验室智能助手 - 后端 API", "version": "2.0"}


@app.get("/api/health")
def health_check():
    """健康检查端点"""
    import time
    status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0",
        "services": {}
    }
    
    try:
        from app.services.vector_store import get_collection_info
        info = get_collection_info()
        status["services"]["vector_store"] = {"status": "ok", "doc_count": info.get("count", 0)}
    except Exception as e:
        status["services"]["vector_store"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"
    
    try:
        from app.core.config import get_api_key_access_stats
        stats = get_api_key_access_stats()
        status["services"]["api_key"] = {"status": "ok", "access_count": stats.get("access_count", 0)}
    except Exception as e:
        status["services"]["api_key"] = {"status": "error", "error": str(e)}
    
    return status
