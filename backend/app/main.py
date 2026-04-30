from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import load_config, engine, Base
from app.core.logging_config import setup_logging
from contextlib import asynccontextmanager
import logging

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和关闭事件"""
    # 启动事件
    logger.info("应用启动中...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表初始化完成")

    # 向量库启动健康检查（自动检测并修复 HNSW 索引损坏）
    try:
        from app.services.vector_store import startup_health_check
        health = startup_health_check()
        if health["healthy"]:
            logger.info(f"向量库健康检查通过: {health['message']}")
        else:
            logger.warning(f"向量库健康检查未通过: {health['message']}")
    except Exception as e:
        logger.error(f"向量库健康检查失败: {e}")

    yield

    # 关闭事件
    logger.info("应用正在关闭...")
    try:
        from app.services.vector_store import shutdown_vector_store
        shutdown_vector_store()
        logger.info("向量库已正常关闭，数据已持久化")
    except Exception as e:
        logger.error(f"关闭向量库时出错: {e}")
    logger.info("应用已关闭")


app = FastAPI(
    title="实验室智能助手 - 后端",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

from app.api import routes
from app.api import auth
from app.api import sessions
from app.api import skills
from app.core.rate_limit import login_limiter, api_limiter
from app.models.parent_document import ParentDocumentModel  # noqa: F401 - 确保表被注册

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
        if info.get("error"):
            status["services"]["vector_store"] = {"status": "error", "error": info.get("error")}
            status["status"] = "degraded"
        else:
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


@app.post("/api/vector-store/repair")
def repair_vector_store():
    """手动触发向量库修复（HNSW 索引损坏后恢复数据）"""
    try:
        from app.services.vector_store import startup_health_check
        health = startup_health_check()
        return {
            "success": health["healthy"],
            "doc_count": health["doc_count"],
            "message": health["message"]
        }
    except Exception as e:
        return {"success": False, "doc_count": 0, "message": str(e)}
