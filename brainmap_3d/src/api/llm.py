from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from src.core.logging_utils import get_logger, StepTimer
from src.db.session import get_db
from src.schemas.llm import LLMChatRequest, LLMChatResponse, LLMStreamChunk
from src.services.llm_service import LLMService

router = APIRouter()
logger = get_logger(__name__)


def get_llm_service(db: AsyncSession = Depends(get_db)) -> LLMService:
    return LLMService(db)


@router.post("/chat", response_model=LLMChatResponse)
async def llm_chat(req: LLMChatRequest, service: LLMService = Depends(get_llm_service)):
    """基于3D脑图上下文的智能问答（非流式）"""
    with StepTimer(logger, f"API llm_chat | brainmap_id={req.brainmap_id}"):
        try:
            return await service.chat(req)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@router.post("/chat/stream")
async def llm_chat_stream(req: LLMChatRequest, service: LLMService = Depends(get_llm_service)):
    """基于3D脑图上下文的智能问答（流式SSE）"""
    from fastapi.encoders import jsonable_encoder
    import json

    with StepTimer(logger, f"API llm_chat_stream | brainmap_id={req.brainmap_id}"):
        async def event_generator():
            try:
                async for chunk in service.chat_stream(req):
                    data = json.dumps(jsonable_encoder(chunk))
                    yield f"data: {data}\n\n"
                yield f"data: {json.dumps({'chunk': '', 'finish_reason': 'stop'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'chunk': '', 'error': str(e), 'finish_reason': 'error'})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )


@router.post("/summarize/{brainmap_id}", response_model=Dict[str, str])
async def summarize_brainmap(brainmap_id: str, service: LLMService = Depends(get_llm_service)):
    """生成脑图摘要"""
    with StepTimer(logger, f"API summarize_brainmap | brainmap_id={brainmap_id}"):
        try:
            summary = await service.summarize_brainmap(brainmap_id)
            return {"brainmap_id": brainmap_id, "summary": summary}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@router.post("/suggest-connections/{brainmap_id}", response_model=List[Dict[str, Any]])
async def suggest_connections(brainmap_id: str, service: LLMService = Depends(get_llm_service)):
    """大模型建议新的节点连接"""
    with StepTimer(logger, f"API suggest_connections | brainmap_id={brainmap_id}"):
        try:
            return await service.suggest_connections(brainmap_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


@router.post("/expand-node/{brainmap_id}/{node_id}", response_model=List[Dict[str, Any]])
async def expand_node(
    brainmap_id: str,
    node_id: int,
    num: int = 3,
    service: LLMService = Depends(get_llm_service),
):
    """为指定节点生成扩展建议（AI辅助添加子节点）"""
    with StepTimer(logger, f"API expand_node | brainmap_id={brainmap_id} node_id={node_id} num={num}"):
        try:
            return await service.expand_node(brainmap_id, node_id, num)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
