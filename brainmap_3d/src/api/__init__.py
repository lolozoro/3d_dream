from fastapi import APIRouter
from src.api.brainmap import router as brainmap_router
from src.api.llm import router as llm_router
from src.api.frontend import router as frontend_router

# REST API v1 (traditional CRUD + advanced queries)
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(brainmap_router, prefix="/brainmaps", tags=["brainmaps"])
api_router.include_router(llm_router, prefix="/llm", tags=["llm"])

# Frontend-facing flat routes (BACKEND_API.md contract)
# These are mounted at root so URLs are exactly /chat and /mindmap/update
frontend_router_tagged = APIRouter(tags=["frontend"])
frontend_router_tagged.include_router(frontend_router)
