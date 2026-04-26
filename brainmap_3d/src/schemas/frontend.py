"""
Schemas matching the frontend API contract from BACKEND_API.md
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class MindMapNode(BaseModel):
    """前端节点模型 —— id 为字符串，全局唯一"""
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    color: Optional[str] = None


class MindMapEdge(BaseModel):
    """前端边模型 —— from/to 引用 node.id"""
    from_: str = Field(..., alias="from")
    to: str = Field(...)

    model_config = {"populate_by_name": True}


class MindMap(BaseModel):
    """前端脑图快照"""
    nodes: List[MindMapNode]
    edges: List[MindMapEdge]


class ChatMessage(BaseModel):
    """对话消息"""
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """POST /chat 请求体"""
    messages: List[ChatMessage]
    mindmap: MindMap


class ChatResponse(BaseModel):
    """POST /chat 响应体"""
    reply: str
    updated_mindmap: Optional[MindMap] = Field(default=None, alias="updatedMindmap")

    model_config = {"populate_by_name": True}


class MindMapUpdateRequest(BaseModel):
    """POST /mindmap/update 请求体"""
    instruction: str
    mindmap: MindMap


class MindMapUpdateResponse(BaseModel):
    """POST /mindmap/update 响应体"""
    mindmap: MindMap
    explanation: Optional[str] = None
