import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from src.core.config import settings
from src.core.logging_utils import setup_logging, get_logger, StepTimer
from src.db.base import Base
from src.db.session import engine
from src.api import api_router, frontend_router_tagged

setup_logging(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 应用启动中...")
    with StepTimer(logger, " lifespan: 数据库初始化"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ 应用启动完成，数据库表已初始化")
    yield
    logger.info("🛑 应用关闭中...")
    with StepTimer(logger, "lifespan: 引擎释放"):
        await engine.dispose()
    logger.info("✅ 应用关闭完成")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置 —— 匹配 BACKEND_API.md 第 7 节
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://localhost:5173",
        "*",  # 保留通配符方便 Docker 内网部署
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 前端契约路由（直接挂载在根路径） ----
# 提供 /chat 和 /mindmap/update
app.include_router(frontend_router_tagged)

# ---- REST API v1（传统 CRUD + LLM 扩展） ----
app.include_router(api_router)

# 静态文件（前端）—— 仅当 frontend 目录存在时
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    with StepTimer(logger, "API serve_index"):
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}

@app.get("/health")
async def health_check():
    with StepTimer(logger, "API health_check"):
        return {"status": "ok", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
