#!/usr/bin/env python3
"""
BrainMap 3D 启动脚本
同时启动后端 FastAPI 服务，前端通过静态文件挂载访问

访问地址:
  - 前端界面: http://localhost:8000
  - API 文档: http://localhost:8000/docs
  - 健康检查: http://localhost:8000/health
"""

import uvicorn
from src.core.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print(" BrainMap 3D Starting...")
    print("=" * 60)
    print(f"  Frontend: http://{settings.HOST}:{settings.PORT}")
    print(f"  API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"  API Base: http://{settings.HOST}:{settings.PORT}/api/v1")
    print("=" * 60)
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
