from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_, or_, text
from sqlalchemy.orm import selectinload
import math

from src.models.node import Node
from src.models.edge import Edge
from src.models.brainmap_meta import BrainMapMeta
from src.schemas.node import NodeCreate, NodeUpdate
from src.schemas.edge import EdgeCreate, EdgeUpdate
from src.schemas.brainmap import (
    BrainMapCreate, BrainMapUpdate, BrainMapStats,
    PathFindRequest, PathFindResponse,
    SubGraphRequest, NeighborQuery,
    BatchNodeUpdateRequest,
)


class BrainMapService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== BrainMap 整体操作 ==========

    async def create_brainmap(self, data: BrainMapCreate) -> Dict[str, Any]:
        """创建新的脑图，同时创建元数据记录和根节点"""
        # 检查是否已存在
        existing = await self.db.get(BrainMapMeta, data.brainmap_id)
        if existing:
            raise ValueError(f"BrainMap '{data.brainmap_id}' already exists")

        # 创建元数据
        meta = BrainMapMeta(
            brainmap_id=data.brainmap_id,
            title=data.title,
            description=data.description,
        )
        self.db.add(meta)

        # 创建根节点
        root_data = data.root_node or {}
        root = Node(
            brainmap_id=data.brainmap_id,
            label=root_data.get("label", data.title),
            content=root_data.get("content", data.description),
            node_type=root_data.get("node_type", "root"),
            pos_x=root_data.get("pos_x", 0.0),
            pos_y=root_data.get("pos_y", 0.0),
            pos_z=root_data.get("pos_z", 0.0),
            size=root_data.get("size", 2.0),
            color=root_data.get("color", "#4F46E5"),
            layer=0,
        )
        self.db.add(root)
        await self.db.commit()
        await self.db.refresh(root)
        await self.db.refresh(meta)
        return {
            "brainmap_id": data.brainmap_id,
            "title": data.title,
            "description": data.description,
            "root_node_id": root.id,
        }

    async def list_brainmaps(
        self, keyword: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> tuple[List[BrainMapMeta], int]:
        """获取脑图列表"""
        query = select(BrainMapMeta)
        count_query = select(func.count()).select_from(BrainMapMeta)

        if keyword:
            like_str = f"%{keyword}%"
            query = query.where(
                or_(
                    BrainMapMeta.brainmap_id.ilike(like_str),
                    BrainMapMeta.title.ilike(like_str),
                )
            )
            count_query = count_query.where(
                or_(
                    BrainMapMeta.brainmap_id.ilike(like_str),
                    BrainMapMeta.title.ilike(like_str),
                )
            )

        query = query.order_by(BrainMapMeta.updated_at.desc())
        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total or 0

    async def get_brainmap_meta(self, brainmap_id: str) -> Optional[BrainMapMeta]:
        """获取脑图元数据"""
        return await self.db.get(BrainMapMeta, brainmap_id)

    async def update_brainmap(self, brainmap_id: str, data: BrainMapUpdate) -> Optional[BrainMapMeta]:
        """更新脑图元数据"""
        meta = await self.get_brainmap_meta(brainmap_id)
        if not meta:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(meta, field, value)
        await self.db.commit()
        await self.db.refresh(meta)
        return meta

    async def get_brainmap_full(self, brainmap_id: str) -> Dict[str, Any]:
        """获取完整脑图（所有节点和边）用于3D渲染"""
        nodes_result = await self.db.execute(
            select(Node).where(Node.brainmap_id == brainmap_id)
        )
        nodes = nodes_result.scalars().all()

        edges_result = await self.db.execute(
            select(Edge).where(Edge.brainmap_id == brainmap_id)
        )
        edges = edges_result.scalars().all()

        meta = await self.get_brainmap_meta(brainmap_id)

        return {
            "brainmap_id": brainmap_id,
            "title": meta.title if meta else brainmap_id,
            "description": meta.description if meta else None,
            "nodes": nodes,
            "edges": edges,
        }

    async def delete_brainmap(self, brainmap_id: str) -> bool:
        """删除整个脑图"""
        await self.db.execute(delete(Edge).where(Edge.brainmap_id == brainmap_id))
        await self.db.execute(delete(Node).where(Node.brainmap_id == brainmap_id))
        await self.db.execute(delete(BrainMapMeta).where(BrainMapMeta.brainmap_id == brainmap_id))
        await self.db.commit()
        return True

    async def get_brainmap_stats(self, brainmap_id: str) -> BrainMapStats:
        """获取脑图统计信息"""
        node_count = await self.db.scalar(
            select(func.count()).where(Node.brainmap_id == brainmap_id)
        )
        edge_count = await self.db.scalar(
            select(func.count()).where(Edge.brainmap_id == brainmap_id)
        )

        # 节点类型分布
        type_result = await self.db.execute(
            select(Node.node_type, func.count())
            .where(Node.brainmap_id == brainmap_id)
            .group_by(Node.node_type)
        )
        node_types = {row[0]: row[1] for row in type_result.all()}

        # 关系类型分布
        rel_result = await self.db.execute(
            select(Edge.relation_type, func.count())
            .where(Edge.brainmap_id == brainmap_id)
            .group_by(Edge.relation_type)
        )
        relation_types = {row[0]: row[1] for row in rel_result.all()}

        # 层级分布
        layer_result = await self.db.execute(
            select(Node.layer, func.count())
            .where(Node.brainmap_id == brainmap_id)
            .group_by(Node.layer)
        )
        layers = {str(row[0]): row[1] for row in layer_result.all()}

        # 分组分布
        group_result = await self.db.execute(
            select(Node.group_id, func.count())
            .where(Node.brainmap_id == brainmap_id)
            .group_by(Node.group_id)
        )
        groups = {str(row[0] or "default"): row[1] for row in group_result.all()}

        # 重心计算
        cog_result = await self.db.execute(
            select(
                func.avg(Node.pos_x),
                func.avg(Node.pos_y),
                func.avg(Node.pos_z),
            ).where(Node.brainmap_id == brainmap_id)
        )
        cog = cog_result.first()

        return BrainMapStats(
            brainmap_id=brainmap_id,
            total_nodes=node_count or 0,
            total_edges=edge_count or 0,
            node_types=node_types,
            relation_types=relation_types,
            layers=layers,
            groups=groups,
            center_of_gravity={
                "x": float(cog[0] or 0),
                "y": float(cog[1] or 0),
                "z": float(cog[2] or 0),
            },
        )

    # ========== Node CRUD ==========

    async def create_node(self, data: NodeCreate) -> Node:
        node = Node(**data.model_dump())
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def get_node(self, node_id: int) -> Optional[Node]:
        result = await self.db.execute(select(Node).where(Node.id == node_id))
        return result.scalar_one_or_none()

    async def update_node(self, node_id: int, data: NodeUpdate) -> Optional[Node]:
        node = await self.get_node(node_id)
        if not node:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(node, field, value)
        await self.db.commit()
        await self.db.refresh(node)
        return node

    async def delete_node(self, node_id: int) -> bool:
        node = await self.get_node(node_id)
        if not node:
            return False
        # 级联删除关联的边
        await self.db.execute(
            delete(Edge).where(
                or_(Edge.source_id == node_id, Edge.target_id == node_id)
            )
        )
        await self.db.delete(node)
        await self.db.commit()
        return True

    async def list_nodes(
        self,
        brainmap_id: str,
        node_type: Optional[str] = None,
        layer: Optional[int] = None,
        group_id: Optional[str] = None,
        keyword: Optional[str] = None,
        bbox: Optional[Dict[str, float]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Node], int]:
        query = select(Node).where(Node.brainmap_id == brainmap_id)
        count_query = select(func.count()).where(Node.brainmap_id == brainmap_id)

        if node_type:
            query = query.where(Node.node_type == node_type)
            count_query = count_query.where(Node.node_type == node_type)
        if layer is not None:
            query = query.where(Node.layer == layer)
            count_query = count_query.where(Node.layer == layer)
        if group_id:
            query = query.where(Node.group_id == group_id)
            count_query = count_query.where(Node.group_id == group_id)
        if keyword:
            like_str = f"%{keyword}%"
            query = query.where(
                or_(Node.label.ilike(like_str), Node.content.ilike(like_str))
            )
            count_query = count_query.where(
                or_(Node.label.ilike(like_str), Node.content.ilike(like_str))
            )
        if bbox:
            query = query.where(
                and_(
                    Node.pos_x >= bbox.get("xmin", -float("inf")),
                    Node.pos_x <= bbox.get("xmax", float("inf")),
                    Node.pos_y >= bbox.get("ymin", -float("inf")),
                    Node.pos_y <= bbox.get("ymax", float("inf")),
                    Node.pos_z >= bbox.get("zmin", -float("inf")),
                    Node.pos_z <= bbox.get("zmax", float("inf")),
                )
            )
            count_query = count_query.where(
                and_(
                    Node.pos_x >= bbox.get("xmin", -float("inf")),
                    Node.pos_x <= bbox.get("xmax", float("inf")),
                    Node.pos_y >= bbox.get("ymin", -float("inf")),
                    Node.pos_y <= bbox.get("ymax", float("inf")),
                    Node.pos_z >= bbox.get("zmin", -float("inf")),
                    Node.pos_z <= bbox.get("zmax", float("inf")),
                )
            )

        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total or 0

    async def search_nodes_global(
        self, keyword: str, skip: int = 0, limit: int = 50
    ) -> tuple[List[Node], int]:
        """全局跨脑图搜索节点"""
        like_str = f"%{keyword}%"
        query = select(Node).where(
            or_(Node.label.ilike(like_str), Node.content.ilike(like_str))
        )
        count_query = select(func.count()).where(
            or_(Node.label.ilike(like_str), Node.content.ilike(like_str))
        )
        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total or 0

    # ========== Edge CRUD ==========

    async def create_edge(self, data: EdgeCreate) -> Edge:
        edge = Edge(**data.model_dump())
        self.db.add(edge)
        await self.db.commit()
        await self.db.refresh(edge)
        return edge

    async def get_edge(self, edge_id: int) -> Optional[Edge]:
        result = await self.db.execute(select(Edge).where(Edge.id == edge_id))
        return result.scalar_one_or_none()

    async def update_edge(self, edge_id: int, data: EdgeUpdate) -> Optional[Edge]:
        edge = await self.get_edge(edge_id)
        if not edge:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(edge, field, value)
        await self.db.commit()
        await self.db.refresh(edge)
        return edge

    async def delete_edge(self, edge_id: int) -> bool:
        edge = await self.get_edge(edge_id)
        if not edge:
            return False
        await self.db.delete(edge)
        await self.db.commit()
        return True

    async def list_edges(
        self,
        brainmap_id: str,
        relation_type: Optional[str] = None,
        source_id: Optional[int] = None,
        target_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Edge], int]:
        query = select(Edge).where(Edge.brainmap_id == brainmap_id)
        count_query = select(func.count()).where(Edge.brainmap_id == brainmap_id)

        if relation_type:
            query = query.where(Edge.relation_type == relation_type)
            count_query = count_query.where(Edge.relation_type == relation_type)
        if source_id:
            query = query.where(Edge.source_id == source_id)
            count_query = count_query.where(Edge.source_id == source_id)
        if target_id:
            query = query.where(Edge.target_id == target_id)
            count_query = count_query.where(Edge.target_id == target_id)

        total = await self.db.scalar(count_query)
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total or 0

    # ========== 3D 空间查询 ==========

    async def spatial_query(
        self,
        brainmap_id: str,
        center_x: float,
        center_y: float,
        center_z: float,
        radius: float,
    ) -> List[Node]:
        """3D 空间球体范围查询"""
        # 先通过包围盒粗略过滤，再精确计算距离
        result = await self.db.execute(
            select(Node).where(
                and_(
                    Node.brainmap_id == brainmap_id,
                    Node.pos_x >= center_x - radius,
                    Node.pos_x <= center_x + radius,
                    Node.pos_y >= center_y - radius,
                    Node.pos_y <= center_y + radius,
                    Node.pos_z >= center_z - radius,
                    Node.pos_z <= center_z + radius,
                )
            )
        )
        nodes = result.scalars().all()
        # 精确球体过滤
        filtered = []
        for node in nodes:
            dist = math.sqrt(
                (node.pos_x - center_x) ** 2
                + (node.pos_y - center_y) ** 2
                + (node.pos_z - center_z) ** 2
            )
            if dist <= radius:
                filtered.append(node)
        return filtered

    async def find_neighbors(self, query: NeighborQuery) -> List[Node]:
        """查找节点的邻居"""
        if query.direction == "out":
            edge_query = select(Edge.target_id).where(Edge.source_id == query.node_id)
        elif query.direction == "in":
            edge_query = select(Edge.source_id).where(Edge.target_id == query.node_id)
        else:
            edge_query = select(
                Edge.source_id,
                Edge.target_id,
            ).where(
                or_(Edge.source_id == query.node_id, Edge.target_id == query.node_id)
            )

        if query.relation_types:
            edge_query = edge_query.where(Edge.relation_type.in_(query.relation_types))

        result = await self.db.execute(edge_query.limit(query.limit))
        rows = result.all()

        neighbor_ids = set()
        for row in rows:
            if query.direction == "both" and isinstance(row, tuple):
                for nid in row:
                    if nid != query.node_id:
                        neighbor_ids.add(nid)
            elif query.direction == "out":
                neighbor_ids.add(row[0])
            elif query.direction == "in":
                neighbor_ids.add(row[0])

        if not neighbor_ids:
            return []

        nodes_result = await self.db.execute(
            select(Node).where(Node.id.in_(neighbor_ids))
        )
        return nodes_result.scalars().all()

    async def get_subgraph(self, req: SubGraphRequest) -> Dict[str, Any]:
        """获取以某节点为中心的子图（支持多跳）"""
        # BFS 获取范围内的节点ID
        visited = {req.center_node_id}
        current_layer = {req.center_node_id}
        all_edges = []

        for _ in range(req.radius):
            if not current_layer:
                break
            edge_filter = [Edge.source_id.in_(current_layer), Edge.target_id.in_(current_layer)]
            if req.relation_types:
                edge_filter.append(Edge.relation_type.in_(req.relation_types))

            result = await self.db.execute(
                select(Edge).where(and_(*edge_filter))
            )
            edges = result.scalars().all()
            next_layer = set()
            for edge in edges:
                all_edges.append(edge)
                next_layer.add(edge.source_id)
                next_layer.add(edge.target_id)
            current_layer = next_layer - visited
            visited.update(current_layer)

        nodes_result = await self.db.execute(select(Node).where(Node.id.in_(visited)))
        nodes = nodes_result.scalars().all()

        return {"nodes": nodes, "edges": all_edges}

    async def find_paths(self, req: PathFindRequest) -> PathFindResponse:
        """查找两节点之间的路径（BFS）"""
        from collections import deque

        # 构建邻接表
        result = await self.db.execute(
            select(Edge).where(Edge.brainmap_id == (
                select(Node.brainmap_id).where(Node.id == req.source_node_id).scalar_subquery()
            ))
        )
        edges = result.scalars().all()

        adj = {}
        edge_map = {}
        for edge in edges:
            if req.relation_types and edge.relation_type not in req.relation_types:
                continue
            adj.setdefault(edge.source_id, []).append(edge.target_id)
            if not edge.directed:
                adj.setdefault(edge.target_id, []).append(edge.source_id)
            edge_map[(edge.source_id, edge.target_id)] = edge

        # BFS
        queue = deque([(req.source_node_id, [req.source_node_id])])
        visited = {req.source_node_id}
        paths = []

        while queue and len(paths) < 5:
            current, path = queue.popleft()
            if len(path) > req.max_depth + 1:
                continue
            if current == req.target_node_id and len(path) > 1:
                paths.append(path)
                continue
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        # 获取详细路径信息
        paths_detail = []
        for path in paths:
            detail = []
            for nid in path:
                node = await self.get_node(nid)
                if node:
                    detail.append({
                        "id": node.id,
                        "label": node.label,
                        "node_type": node.node_type,
                        "pos": {"x": node.pos_x, "y": node.pos_y, "z": node.pos_z},
                    })
            paths_detail.append(detail)

        return PathFindResponse(
            paths=paths,
            paths_detail=paths_detail,
            distance=len(paths[0]) - 1 if paths else None,
        )

    # ========== 批量操作 ==========

    async def batch_create_nodes(self, brainmap_id: str, nodes_data: List[Dict[str, Any]]) -> List[Node]:
        """批量创建节点"""
        nodes = []
        for data in nodes_data:
            data["brainmap_id"] = brainmap_id
            node = Node(**data)
            self.db.add(node)
            nodes.append(node)
        await self.db.commit()
        for node in nodes:
            await self.db.refresh(node)
        return nodes

    async def batch_create_edges(self, brainmap_id: str, edges_data: List[Dict[str, Any]]) -> List[Edge]:
        """批量创建边"""
        edges = []
        for data in edges_data:
            data["brainmap_id"] = brainmap_id
            edge = Edge(**data)
            self.db.add(edge)
            edges.append(edge)
        await self.db.commit()
        for edge in edges:
            await self.db.refresh(edge)
        return edges

    async def batch_update_nodes(self, req: BatchNodeUpdateRequest) -> List[Node]:
        """批量更新节点（主要用于保存3D布局）"""
        updated = []
        for item in req.updates:
            node = await self.get_node(item.id)
            if not node:
                continue
            update_data = item.model_dump(exclude_unset=True)
            del update_data["id"]  # 不更新ID
            for field, value in update_data.items():
                if value is not None:
                    setattr(node, field, value)
            updated.append(node)
        if updated:
            await self.db.commit()
            for node in updated:
                await self.db.refresh(node)
        return updated

    # ========== 导入/导出 ==========

    async def export_brainmap(self, brainmap_id: str) -> Dict[str, Any]:
        """导出脑图为JSON"""
        data = await self.get_brainmap_full(brainmap_id)
        meta = await self.get_brainmap_meta(brainmap_id)
        return {
            "brainmap_id": brainmap_id,
            "title": meta.title if meta else brainmap_id,
            "description": meta.description if meta else None,
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "content": n.content,
                    "node_type": n.node_type,
                    "pos_x": n.pos_x,
                    "pos_y": n.pos_y,
                    "pos_z": n.pos_z,
                    "size": n.size,
                    "color": n.color,
                    "shape": n.shape,
                    "opacity": n.opacity,
                    "layer": n.layer,
                    "group_id": n.group_id,
                    "parent_id": n.parent_id,
                    "metadata_json": n.metadata_json,
                }
                for n in data["nodes"]
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation_type": e.relation_type,
                    "label": e.label,
                    "weight": e.weight,
                    "directed": e.directed,
                    "color": e.color,
                    "width": e.width,
                    "style": e.style,
                    "control_points": e.control_points,
                    "metadata_json": e.metadata_json,
                }
                for e in data["edges"]
            ],
        }

    async def import_brainmap(
        self, brainmap_id: str, nodes_data: List[Dict[str, Any]], edges_data: List[Dict[str, Any]], overwrite: bool = False
    ) -> Dict[str, Any]:
        """从JSON导入脑图"""
        if overwrite:
            await self.delete_brainmap(brainmap_id)
            # 重新创建元数据
            meta = BrainMapMeta(brainmap_id=brainmap_id, title=brainmap_id)
            self.db.add(meta)
            await self.db.commit()

        # 清除旧数据（如果不覆盖则先删除该脑图的数据）
        existing = await self.get_brainmap_meta(brainmap_id)
        if not existing:
            meta = BrainMapMeta(brainmap_id=brainmap_id, title=brainmap_id)
            self.db.add(meta)

        await self.db.execute(delete(Edge).where(Edge.brainmap_id == brainmap_id))
        await self.db.execute(delete(Node).where(Node.brainmap_id == brainmap_id))
        await self.db.commit()

        # ID映射（处理导入时ID冲突）
        id_mapping = {}
        created_nodes = []
        for data in nodes_data:
            old_id = data.get("id")
            data["brainmap_id"] = brainmap_id
            if "id" in data:
                del data["id"]  # 让数据库自动生成ID
            node = Node(**data)
            self.db.add(node)
            created_nodes.append((old_id, node))

        await self.db.commit()
        for old_id, node in created_nodes:
            await self.db.refresh(node)
            if old_id is not None:
                id_mapping[old_id] = node.id

        created_edges = []
        for data in edges_data:
            data["brainmap_id"] = brainmap_id
            if "id" in data:
                del data["id"]
            # 映射source/target ID
            if data.get("source_id") in id_mapping:
                data["source_id"] = id_mapping[data["source_id"]]
            if data.get("target_id") in id_mapping:
                data["target_id"] = id_mapping[data["target_id"]]
            edge = Edge(**data)
            self.db.add(edge)
            created_edges.append(edge)

        await self.db.commit()
        for edge in created_edges:
            await self.db.refresh(edge)

        return {
            "brainmap_id": brainmap_id,
            "nodes_created": len(created_nodes),
            "edges_created": len(created_edges),
        }
