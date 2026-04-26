from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.node import NodeCreate, NodeUpdate, NodeResponse, NodeListResponse
from src.schemas.edge import EdgeCreate, EdgeUpdate, EdgeResponse, EdgeListResponse
from src.schemas.brainmap import (
    BrainMapCreate, BrainMapUpdate, BrainMapResponse, BrainMapFullResponse,
    BrainMapStats, PathFindRequest, PathFindResponse,
    SubGraphRequest, NeighborQuery, GraphData,
)
from src.services.brainmap import BrainMapService

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> BrainMapService:
    return BrainMapService(db)


# ========== BrainMap 整体接口 ==========

@router.post("", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def create_brainmap(data: BrainMapCreate, service: BrainMapService = Depends(get_service)):
    """创建新的3D脑图"""
    return await service.create_brainmap(data)


@router.get("/{brainmap_id}/full", response_model=BrainMapFullResponse)
async def get_brainmap_full(brainmap_id: str, service: BrainMapService = Depends(get_service)):
    """获取完整脑图数据（用于前端3D渲染）"""
    data = await service.get_brainmap_full(brainmap_id)
    if not data["nodes"] and not data["edges"]:
        # 允许空脑图返回
        pass
    return BrainMapFullResponse(
        brainmap_id=brainmap_id,
        title=brainmap_id,
        description=None,
        nodes=data["nodes"],
        edges=data["edges"],
    )


@router.get("/{brainmap_id}/graph-data", response_model=GraphData)
async def get_graph_data(brainmap_id: str, service: BrainMapService = Depends(get_service)):
    """获取图数据（nodes + edges），前端3D渲染专用"""
    data = await service.get_brainmap_full(brainmap_id)
    return GraphData(
        nodes=data["nodes"],
        edges=data["edges"],
    )


@router.delete("/{brainmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brainmap(brainmap_id: str, service: BrainMapService = Depends(get_service)):
    """删除整个脑图"""
    await service.delete_brainmap(brainmap_id)
    return None


@router.get("/{brainmap_id}/stats", response_model=BrainMapStats)
async def get_brainmap_stats(brainmap_id: str, service: BrainMapService = Depends(get_service)):
    """获取脑图统计信息"""
    return await service.get_brainmap_stats(brainmap_id)


# ========== Node 节点接口 ==========

@router.post("/{brainmap_id}/nodes", status_code=status.HTTP_201_CREATED, response_model=NodeResponse)
async def create_node(brainmap_id: str, data: NodeCreate, service: BrainMapService = Depends(get_service)):
    """在脑图中创建新节点（支持3D坐标）"""
    if data.brainmap_id != brainmap_id:
        raise HTTPException(status_code=400, detail="brainmap_id mismatch")
    return await service.create_node(data)


@router.get("/{brainmap_id}/nodes", response_model=NodeListResponse)
async def list_nodes(
    brainmap_id: str,
    node_type: Optional[str] = None,
    layer: Optional[int] = None,
    group_id: Optional[str] = None,
    keyword: Optional[str] = None,
    bbox: Optional[str] = None,  # JSON字符串
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: BrainMapService = Depends(get_service),
):
    """查询节点（支持3D包围盒过滤）"""
    import json
    bbox_dict = None
    if bbox:
        try:
            bbox_dict = json.loads(bbox)
        except Exception:
            raise HTTPException(status_code=400, detail="bbox must be valid JSON")
    items, total = await service.list_nodes(
        brainmap_id=brainmap_id,
        node_type=node_type,
        layer=layer,
        group_id=group_id,
        keyword=keyword,
        bbox=bbox_dict,
        skip=skip,
        limit=limit,
    )
    return NodeListResponse(total=total, items=items)


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, service: BrainMapService = Depends(get_service)):
    """获取单个节点详情"""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.patch("/nodes/{node_id}", response_model=NodeResponse)
async def update_node(node_id: int, data: NodeUpdate, service: BrainMapService = Depends(get_service)):
    """更新节点（支持3D坐标更新）"""
    node = await service.update_node(node_id, data)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: int, service: BrainMapService = Depends(get_service)):
    """删除节点（级联删除关联边）"""
    success = await service.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return None


# ========== Edge 边接口 ==========

@router.post("/{brainmap_id}/edges", status_code=status.HTTP_201_CREATED, response_model=EdgeResponse)
async def create_edge(brainmap_id: str, data: EdgeCreate, service: BrainMapService = Depends(get_service)):
    """创建边（连接两个节点）"""
    if data.brainmap_id != brainmap_id:
        raise HTTPException(status_code=400, detail="brainmap_id mismatch")
    return await service.create_edge(data)


@router.get("/{brainmap_id}/edges", response_model=EdgeListResponse)
async def list_edges(
    brainmap_id: str,
    relation_type: Optional[str] = None,
    source_id: Optional[int] = None,
    target_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: BrainMapService = Depends(get_service),
):
    """查询边"""
    items, total = await service.list_edges(
        brainmap_id=brainmap_id,
        relation_type=relation_type,
        source_id=source_id,
        target_id=target_id,
        skip=skip,
        limit=limit,
    )
    return EdgeListResponse(total=total, items=items)


@router.get("/edges/{edge_id}", response_model=EdgeResponse)
async def get_edge(edge_id: int, service: BrainMapService = Depends(get_service)):
    """获取单条边详情"""
    edge = await service.get_edge(edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return edge


@router.patch("/edges/{edge_id}", response_model=EdgeResponse)
async def update_edge(edge_id: int, data: EdgeUpdate, service: BrainMapService = Depends(get_service)):
    """更新边"""
    edge = await service.update_edge(edge_id, data)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return edge


@router.delete("/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(edge_id: int, service: BrainMapService = Depends(get_service)):
    """删除边"""
    success = await service.delete_edge(edge_id)
    if not success:
        raise HTTPException(status_code=404, detail="Edge not found")
    return None


# ========== 3D 高级查询接口 ==========

@router.get("/{brainmap_id}/spatial-search", response_model=List[NodeResponse])
async def spatial_search(
    brainmap_id: str,
    x: float = Query(..., description="中心X坐标"),
    y: float = Query(..., description="中心Y坐标"),
    z: float = Query(..., description="中心Z坐标"),
    radius: float = Query(..., gt=0, description="搜索半径"),
    service: BrainMapService = Depends(get_service),
):
    """3D空间球体范围搜索节点"""
    return await service.spatial_query(brainmap_id, x, y, z, radius)


@router.post("/{brainmap_id}/neighbors", response_model=List[NodeResponse])
async def get_neighbors(
    brainmap_id: str,
    query: NeighborQuery,
    service: BrainMapService = Depends(get_service),
):
    """获取节点的邻居节点"""
    return await service.find_neighbors(query)


@router.post("/{brainmap_id}/subgraph", response_model=GraphData)
async def get_subgraph(
    brainmap_id: str,
    req: SubGraphRequest,
    service: BrainMapService = Depends(get_service),
):
    """获取子图（以某节点为中心，多跳半径）"""
    data = await service.get_subgraph(req)
    return GraphData(nodes=data["nodes"], edges=data["edges"])


@router.post("/{brainmap_id}/paths", response_model=PathFindResponse)
async def find_paths(
    brainmap_id: str,
    req: PathFindRequest,
    service: BrainMapService = Depends(get_service),
):
    """查找两节点之间的路径"""
    return await service.find_paths(req)


# ========== 批量操作接口 ==========

@router.post("/{brainmap_id}/batch-nodes", status_code=status.HTTP_201_CREATED, response_model=List[NodeResponse])
async def batch_create_nodes(
    brainmap_id: str,
    nodes: List[Dict[str, Any]],
    service: BrainMapService = Depends(get_service),
):
    """批量创建节点（用于导入或初始化3D脑图）"""
    return await service.batch_create_nodes(brainmap_id, nodes)


@router.post("/{brainmap_id}/batch-edges", status_code=status.HTTP_201_CREATED, response_model=List[EdgeResponse])
async def batch_create_edges(
    brainmap_id: str,
    edges: List[Dict[str, Any]],
    service: BrainMapService = Depends(get_service),
):
    """批量创建边"""
    return await service.batch_create_edges(brainmap_id, edges)
