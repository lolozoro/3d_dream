from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class BrainMapContext(BaseModel):
    brainmap_id: str
    include_structure: bool = Field(default=True)
    include_content: bool = Field(default=True)
    include_metadata: bool = Field(default=False)
    max_nodes: int = Field(default=100, ge=1, le=500)
    focus_node_ids: Optional[List[int]] = None  # 聚焦特定节点


class LLMChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    brainmap_id: str = Field(..., min_length=1)
    context: Optional[BrainMapContext] = Field(default_factory=lambda: BrainMapContext(brainmap_id=""))
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    stream: bool = Field(default=False)
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class LLMChatResponse(BaseModel):
    answer: str
    brainmap_id: str
    used_nodes: List[int] = Field(default_factory=list)
    used_edges: List[int] = Field(default_factory=list)
    model: str
    tokens_used: Optional[int] = None
    suggestions: Optional[List[str]] = Field(default_factory=list)


class LLMStreamChunk(BaseModel):
    chunk: str
    finish_reason: Optional[str] = None
