from typing import List, Dict, Any


class PromptTemplates:
    """大模型提示词模板"""

    @staticmethod
    def brainmap_system_prompt() -> str:
        return """你是一个3D脑图智能助手。你可以根据用户提供的3D脑图结构数据进行分析和回答。

你的能力包括：
1. 理解脑图的层级结构、节点关系和3D空间布局
2. 基于脑图内容进行知识问答和推理
3. 发现节点之间的潜在联系
4. 提供脑图优化建议
5. 根据脑图生成摘要、大纲或详细解释

回答时请：
- 结合脑图的具体节点和关系进行分析
- 提及相关节点时标注其层级和类型
- 如果需要，可以建议用户在3D视图中关注特定节点或区域
- 保持简洁但信息丰富

当前脑图数据格式说明：
- nodes: 节点列表，每个节点包含 id, label(标签), content(内容), node_type(类型), pos(3D坐标), layer(层级)
- edges: 边列表，每个边包含 source_id, target_id, relation_type(关系类型), weight(权重)
"""

    @staticmethod
    def build_brainmap_context(
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        include_structure: bool = True,
        include_content: bool = True,
        include_metadata: bool = False,
    ) -> str:
        """将脑图数据构建为大模型可理解的上下文"""
        lines = []
        lines.append(f"=== 脑图数据 ===")
        lines.append(f"节点总数: {len(nodes)}")
        lines.append(f"边总数: {len(edges)}")
        lines.append("")

        # 构建节点映射
        node_map = {n["id"]: n for n in nodes}

        if include_structure:
            lines.append("【节点结构】")
            # 按层级分组
            layer_groups: Dict[int, List] = {}
            for n in nodes:
                layer_groups.setdefault(n.get("layer", 0), []).append(n)

            for layer in sorted(layer_groups.keys()):
                lines.append(f"  层级 {layer}:")
                for n in layer_groups[layer]:
                    pos = n.get("pos", {})
                    pos_str = f"({pos.get('x', 0):.1f}, {pos.get('y', 0):.1f}, {pos.get('z', 0):.1f})"
                    type_str = f"[{n.get('node_type', 'unknown')}]"
                    lines.append(f"    - ID{n['id']} {type_str} {n['label']} @ {pos_str}")
                    if include_content and n.get("content"):
                        content = n["content"]
                        if len(content) > 200:
                            content = content[:200] + "..."
                        lines.append(f"      内容: {content}")
            lines.append("")

        if include_structure:
            lines.append("【关系结构】")
            for e in edges:
                src = node_map.get(e.get("source_id"), {})
                tgt = node_map.get(e.get("target_id"), {})
                rel = e.get("relation_type", "related")
                weight = e.get("weight", 1.0)
                lines.append(
                    f"  {src.get('label', '?')} -( {rel}, w={weight:.2f} )-> {tgt.get('label', '?')}"
                )
            lines.append("")

        if include_metadata:
            lines.append("【元数据】")
            type_counts = {}
            for n in nodes:
                type_counts[n.get("node_type", "unknown")] = type_counts.get(n.get("node_type", "unknown"), 0) + 1
            for t, c in type_counts.items():
                lines.append(f"  节点类型 '{t}': {c} 个")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def build_chat_messages(
        user_message: str,
        brainmap_context: str,
        history: List[Dict[str, str]] = None,
    ) -> List[Dict[str, str]]:
        messages = [
            {"role": "system", "content": PromptTemplates.brainmap_system_prompt()},
        ]
        if history:
            # 只保留最近的10轮对话
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": f"{brainmap_context}\n\n用户问题: {user_message}"})
        return messages

    @staticmethod
    def summarize_brainmap_prompt(brainmap_context: str) -> str:
        return f"""请对以下3D脑图进行摘要总结：

{brainmap_context}

要求：
1. 概括脑图的核心主题和知识结构
2. 指出关键节点和它们之间的关系
3. 分析脑图的层级组织是否合理
4. 如果有明显的内容聚类，请指出来
5. 控制在300字以内
"""

    @staticmethod
    def suggest_connections_prompt(brainmap_context: str) -> str:
        return f"""请分析以下3D脑图，并建议可能存在的但尚未连接的节点关系：

{brainmap_context}

要求：
1. 找出语义相关但当前没有直接连接的节点对
2. 为每对建议的关系提供理由
3. 建议的关系类型（如：因果、相似、对立、补充等）
4. 最多建议5条新连接
"""
