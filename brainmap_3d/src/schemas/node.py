from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class NodeBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    node_type: str = Field(default="concept")
    pos_x: float = Field(default=0.0)
    pos_y: float = Field(default=0.0)
    pos_z: float = Field(default=0.0)
    size: float = Field(default=1.0, ge=0.1)
    color: Optional[str] = Field(default="#4F46E5")
    shape: Optional[str] = Field(default="sphere")
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    layer: int = Field(default=0)
    group_id: Optional[str] = None
    parent_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class NodeCreate(NodeBase):
    brainmap_id: str = Field(..., min_length=1, max_length=64)


class NodeUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = None
    node_type: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_z: Optional[float] = None
    size: Optional[float] = Field(default=None, ge=0.1)
    color: Optional[str] = None
    shape: Optional[str] = None
    opacity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    layer: Optional[int] = None
    group_id: Optional[str] = None
    parent_id: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None


class NodeResponse(NodeBase):
    id: int
    brainmap_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NodeListResponse(BaseModel):
    total: int
    items: list[NodeResponse]
