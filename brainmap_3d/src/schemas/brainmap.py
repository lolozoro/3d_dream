from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.schemas.node import NodeResponse
from src.schemas.edge import EdgeResponse


class BrainMapCreate(BaseModel):
    brainmap_id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    root_node: Optional[Dict[str, Any]] = None  # 初始根节点数据


class BrainMapUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None


class BrainMapResponse(BaseModel):
    brainmap_id: str
    title: str
    description: Optional[str]
    node_count: int = 0
    edge_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BrainMapListResponse(BaseModel):
    total: int
    items: List[BrainMapResponse]


class BrainMapFullResponse(BaseModel):
    brainmap_id: str
    title: str
    description: Optional[str]
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]


class BrainMapQuery(BaseModel):
    brainmap_id: Optional[str] = None
    node_type: Optional[str] = None
    layer: Optional[int] = None
    group_id: Optional[str] = None
    keyword: Optional[str] = None
    bbox: Optional[Dict[str, float]] = None  # 3D 空间包围盒查询 {"xmin": 0, "xmax": 10, ...}


class BrainMapStats(BaseModel):
    brainmap_id: str
    total_nodes: int
    total_edges: int
    node_types: Dict[str, int]
    relation_types: Dict[str, int]
    layers: Dict[str, int]
    groups: Dict[str, int]
    center_of_gravity: Dict[str, float]  # {"x": 0, "y": 0, "z": 0}


class Node3DCoordinate(BaseModel):
    x: float
    y: float
    z: float


class GraphData(BaseModel):
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]
    spatial_index: Optional[Dict[str, Any]] = None  # 3D 空间索引数据


class PathFindRequest(BaseModel):
    source_node_id: int
    target_node_id: int
    max_depth: int = Field(default=10, ge=1, le=50)
    relation_types: Optional[List[str]] = None


class PathFindResponse(BaseModel):
    paths: List[List[int]]  # 节点ID路径列表
    paths_detail: List[List[Dict[str, Any]]]  # 详细的节点信息路径
    distance: Optional[float] = None


class SubGraphRequest(BaseModel):
    center_node_id: int
    radius: int = Field(default=2, ge=1, le=10)  #  hops
    relation_types: Optional[List[str]] = None


class NeighborQuery(BaseModel):
    node_id: int
    direction: str = Field(default="both")  # in, out, both
    relation_types: Optional[List[str]] = None
    limit: int = Field(default=50, ge=1, le=500)


class BatchNodeUpdateItem(BaseModel):
    id: int
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    pos_z: Optional[float] = None
    label: Optional[str] = None
    color: Optional[str] = None
    size: Optional[float] = None


class BatchNodeUpdateRequest(BaseModel):
    updates: List[BatchNodeUpdateItem]


class ExportFormat(BaseModel):
    format: str = Field(default="json")  # json, xmind, markdown


class ImportData(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    overwrite: bool = Field(default=False)
