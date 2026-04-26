from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class EdgeBase(BaseModel):
    source_id: int
    target_id: int
    relation_type: str = Field(default="related")
    label: Optional[str] = None
    weight: float = Field(default=1.0, ge=0.0)
    directed: int = Field(default=1, ge=0, le=1)
    color: Optional[str] = Field(default="#94A3B8")
    width: float = Field(default=1.0, ge=0.1)
    style: Optional[str] = Field(default="solid")
    control_points: Optional[List[Dict[str, float]]] = Field(default_factory=list)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EdgeCreate(EdgeBase):
    brainmap_id: str = Field(..., min_length=1, max_length=64)


class EdgeUpdate(BaseModel):
    relation_type: Optional[str] = None
    label: Optional[str] = None
    weight: Optional[float] = Field(default=None, ge=0.0)
    directed: Optional[int] = Field(default=None, ge=0, le=1)
    color: Optional[str] = None
    width: Optional[float] = Field(default=None, ge=0.1)
    style: Optional[str] = None
    control_points: Optional[List[Dict[str, float]]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class EdgeResponse(EdgeBase):
    id: int
    brainmap_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EdgeListResponse(BaseModel):
    total: int
    items: list[EdgeResponse]
