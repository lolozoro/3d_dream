from typing import AsyncIterator, List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.logging_utils import get_logger, StepTimer
from src.schemas.llm import LLMChatRequest, LLMChatResponse, BrainMapContext, LLMStreamChunk
from src.llm.client import LLMClient
from src.llm.prompts import PromptTemplates
from src.models.node import Node
from src.models.edge import Edge

logger = get_logger(__name__)


class LLMService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = LLMClient()

    async def _fetch_brainmap_data(
        self,
        brainmap_id: str,
        context: BrainMapContext,
    ) -> tuple[List[Dict], List[Dict]]:
        """获取脑图数据，支持聚焦特定节点"""
        with StepTimer(logger, f"LLMService._fetch_brainmap_data | brainmap_id={brainmap_id}"):
            # 查询节点
            node_query = select(Node).where(Node.brainmap_id == brainmap_id)
            if context.focus_node_ids:
                node_query = node_query.where(Node.id.in_(context.focus_node_ids))
            node_result = await self.db.execute(node_query.limit(context.max_nodes))
            nodes = node_result.scalars().all()
            node_ids = [n.id for n in nodes]

            # 查询边（只包含在节点集合内的边）
            edge_query = select(Edge).where(
                Edge.brainmap_id == brainmap_id,
                Edge.source_id.in_(node_ids),
                Edge.target_id.in_(node_ids),
            )
            edge_result = await self.db.execute(edge_query)
            edges = edge_result.scalars().all()

            # 转换为字典
            nodes_dict = [
                {
                    "id": n.id,
                    "label": n.label,
                    "content": n.content or "",
                    "node_type": n.node_type,
                    "pos": {"x": n.pos_x, "y": n.pos_y, "z": n.pos_z},
                    "layer": n.layer,
                    "group_id": n.group_id,
                    "size": n.size,
                    "color": n.color,
                }
                for n in nodes
            ]
            edges_dict = [
                {
                    "id": e.id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation_type": e.relation_type,
                    "label": e.label,
                    "weight": e.weight,
                    "directed": e.directed,
                }
                for e in edges
            ]
            return nodes_dict, edges_dict

    async def chat(self, req: LLMChatRequest) -> LLMChatResponse:
        """基于脑图上下文的非流式问答"""
        with StepTimer(logger, f"LLMService.chat | brainmap_id={req.brainmap_id}"):
            nodes, edges = await self._fetch_brainmap_data(req.brainmap_id, req.context or BrainMapContext(brainmap_id=req.brainmap_id))
            context_str = PromptTemplates.build_brainmap_context(
                nodes=nodes,
                edges=edges,
                include_structure=req.context.include_structure if req.context else True,
                include_content=req.context.include_content if req.context else True,
                include_metadata=req.context.include_metadata if req.context else False,
            )
            messages = PromptTemplates.build_chat_messages(
                user_message=req.message,
                brainmap_context=context_str,
                history=req.history,
            )

            with StepTimer(logger, "LLMService.chat -> LLM call"):
                answer = await self.client.chat(
                    messages=messages,
                    model=req.model,
                    temperature=req.temperature,
                )

            return LLMChatResponse(
                answer=answer,
                brainmap_id=req.brainmap_id,
                used_nodes=[n["id"] for n in nodes],
                used_edges=[e["id"] for e in edges],
                model=req.model or self.client.default_model,
            )

    async def chat_stream(self, req: LLMChatRequest) -> AsyncIterator[LLMStreamChunk]:
        """基于脑图上下文的流式问答"""
        with StepTimer(logger, f"LLMService.chat_stream | brainmap_id={req.brainmap_id}"):
            nodes, edges = await self._fetch_brainmap_data(req.brainmap_id, req.context or BrainMapContext(brainmap_id=req.brainmap_id))
            context_str = PromptTemplates.build_brainmap_context(
                nodes=nodes,
                edges=edges,
                include_structure=req.context.include_structure if req.context else True,
                include_content=req.context.include_content if req.context else True,
                include_metadata=req.context.include_metadata if req.context else False,
            )
            messages = PromptTemplates.build_chat_messages(
                user_message=req.message,
                brainmap_context=context_str,
                history=req.history,
            )

            async for chunk in self.client.chat_stream(
                messages=messages,
                model=req.model,
                temperature=req.temperature,
            ):
                yield LLMStreamChunk(chunk=chunk)

    async def summarize_brainmap(self, brainmap_id: str) -> str:
        """生成脑图摘要"""
        with StepTimer(logger, f"LLMService.summarize_brainmap | brainmap_id={brainmap_id}"):
            context = BrainMapContext(brainmap_id=brainmap_id, include_structure=True, include_content=True)
            nodes, edges = await self._fetch_brainmap_data(brainmap_id, context)
            context_str = PromptTemplates.build_brainmap_context(nodes, edges)
            prompt = PromptTemplates.summarize_brainmap_prompt(context_str)
            messages = [
                {"role": "system", "content": PromptTemplates.brainmap_system_prompt()},
                {"role": "user", "content": prompt},
            ]
            with StepTimer(logger, "LLMService.summarize_brainmap -> LLM call"):
                return await self.client.chat(messages=messages)

    async def suggest_connections(self, brainmap_id: str) -> List[Dict[str, Any]]:
        """建议新的节点连接"""
        with StepTimer(logger, f"LLMService.suggest_connections | brainmap_id={brainmap_id}"):
            context = BrainMapContext(brainmap_id=brainmap_id, include_structure=True, include_content=True)
            nodes, edges = await self._fetch_brainmap_data(brainmap_id, context)
            context_str = PromptTemplates.build_brainmap_context(nodes, edges)
            prompt = PromptTemplates.suggest_connections_prompt(context_str)
            messages = [
                {"role": "system", "content": PromptTemplates.brainmap_system_prompt()},
                {"role": "user", "content": prompt},
            ]
            with StepTimer(logger, "LLMService.suggest_connections -> LLM call"):
                answer = await self.client.chat(messages=messages)
            # 简单解析建议结果
            return [{"suggestion_text": answer}]

    async def expand_node(
        self,
        brainmap_id: str,
        node_id: int,
        num_suggestions: int = 3,
    ) -> List[Dict[str, Any]]:
        """基于大模型为特定节点生成扩展建议"""
        with StepTimer(logger, f"LLMService.expand_node | brainmap_id={brainmap_id} node_id={node_id}"):
            from src.services.brainmap import BrainMapService
            bm_service = BrainMapService(self.db)
            with StepTimer(logger, "LLMService.expand_node -> fetch node & neighbors"):
                node = await bm_service.get_node(node_id)
                if not node:
                    return []

                neighbors = await bm_service.find_neighbors(NeighborQuery(node_id=node_id, direction="both"))
                neighbor_labels = [n.label for n in neighbors]

            prompt = f"""节点: "{node.label}"
类型: {node.node_type}
内容: {node.content or '无'}

已有连接节点: {', '.join(neighbor_labels) if neighbor_labels else '无'}

请为该节点建议 {num_suggestions} 个相关的子主题或关联概念，用于3D脑图扩展。
每个建议包含：
1. 标签（简短名称）
2. 内容（详细描述）
3. 建议的关系类型
4. 建议的3D位置偏移方向（相对于当前节点，用x,y,z偏移描述）

请以JSON数组格式返回：
[
  {{"label": "...", "content": "...", "relation_type": "...", "offset": {{"x": 1, "y": 0, "z": 0}}}},
  ...
]
"""
            messages = [
                {"role": "system", "content": "你是一个3D脑图知识扩展助手。请严格返回JSON格式。"},
                {"role": "user", "content": prompt},
            ]
            with StepTimer(logger, "LLMService.expand_node -> LLM call"):
                answer = await self.client.chat(messages=messages, max_tokens=2048)
            # 尝试解析JSON
            import json
            try:
                # 提取JSON部分
                start = answer.find("[")
                end = answer.rfind("]") + 1
                if start >= 0 and end > start:
                    return json.loads(answer[start:end])
            except Exception:
                pass
            return [{"label": "建议", "content": answer, "relation_type": "related", "offset": {"x": 1, "y": 0, "z": 0}}]
