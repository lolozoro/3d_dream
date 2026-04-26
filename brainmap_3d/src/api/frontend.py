"""
Frontend-facing API routes — matches BACKEND_API.md contract
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import json

from src.core.logging_utils import get_logger, StepTimer
from src.schemas.frontend import (
    ChatRequest, ChatResponse,
    MindMapUpdateRequest, MindMapUpdateResponse,
    MindMap, MindMapNode, MindMapEdge,
)
from src.services.frontend_llm import FrontendLLMService

router = APIRouter()
logger = get_logger(__name__)

# 复用同一个 service 实例（stateless，线程安全）
llm_service = FrontendLLMService()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    纯问答接口。
    接收完整对话历史 + 当前脑图快照，返回 AI 回复。
    可选返回 updatedMindmap，前端会在回复后直接替换脑图。
    """
    with StepTimer(logger, f"API /chat | messages={len(req.messages)} nodes={len(req.mindmap.nodes)}"):
        try:
            reply, updated_map = await llm_service.chat(req)
            return ChatResponse(reply=reply, updated_mindmap=updated_map)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/mindmap/update", response_model=MindMapUpdateResponse)
async def mindmap_update(req: MindMapUpdateRequest):
    """
    结构变更接口。
    接收用户改图指令 + 当前脑图快照，让 LLM 生成完整的新脑图结构。
    """
    with StepTimer(logger, f"API /mindmap/update | nodes={len(req.mindmap.nodes)} instruction={req.instruction[:30]}"):
        try:
            new_mindmap, explanation = await llm_service.update_mindmap(req)
            return MindMapUpdateResponse(mindmap=new_mindmap, explanation=explanation)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
