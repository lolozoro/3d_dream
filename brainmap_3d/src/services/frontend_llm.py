"""
Frontend-facing LLM Service
Handles the two interaction modes defined in BACKEND_API.md:
  1. /chat      -> conversational Q&A based on mindmap context
  2. /mindmap/update -> LLM-driven structural modification
"""
import os
import json
import re
from typing import Optional, Tuple, List, Dict, Any
import httpx
from openai import AsyncOpenAI

from src.core.config import settings
from src.schemas.frontend import (
    ChatRequest, MindMapUpdateRequest,
    MindMap, MindMapNode, MindMapEdge,
)


class FrontendLLMService:
    def __init__(self):
        api_key = settings.DASHSCOPE_API_KEY or os.environ.get("DASHSCOPE_API_KEY", "")
        self.has_key = bool(api_key) and api_key != "dummy-key"
        self.client = AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=settings.DASHSCOPE_BASE_URL,
            http_client=httpx.AsyncClient(timeout=120.0),
        )
        self.model = settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE

    # ------------------------------------------------------------------
    # 1. /chat
    # ------------------------------------------------------------------
    async def chat(self, req: ChatRequest) -> Tuple[str, Optional[MindMap]]:
        """
        Build a system prompt from the current mindmap, append user messages,
        call LLM, and return (reply_text, optional_new_mindmap).
        """
        system_prompt = self._build_mindmap_system_prompt(req.mindmap)
        messages = [{"role": "system", "content": system_prompt}]
        for m in req.messages:
            messages.append({"role": m.role, "content": m.content})

        if not self.has_key:
            # ---- Fallback: deterministic mock responses ----
            reply = self._mock_chat_reply(req)
            return reply, None

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False,
        )
        content = response.choices[0].message.content or ""

        # Try to detect if the assistant also wants to mutate the map.
        # We look for a markdown JSON block tagged with ```json ... ```
        updated_map = self._try_extract_mindmap(content)
        # Strip the JSON block from the visible reply so the user doesn't see raw JSON
        reply_text = self._strip_json_block(content) if updated_map else content
        return reply_text, updated_map

    # ------------------------------------------------------------------
    # 2. /mindmap/update
    # ------------------------------------------------------------------
    async def update_mindmap(self, req: MindMapUpdateRequest) -> Tuple[MindMap, Optional[str]]:
        """
        Ask the LLM to produce a **complete** new mindmap according to the instruction.
        Returns (new_mindmap, explanation).
        """
        system_prompt = self._build_update_system_prompt(req.mindmap, req.instruction)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Instruction: {req.instruction}"},
        ]

        if not self.has_key:
            # ---- Fallback: simple deterministic mutation ----
            new_map, explanation = self._mock_update_mindmap(req)
            return new_map, explanation

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False,
        )
        content = response.choices[0].message.content or ""

        # Extract JSON mindmap from the response
        parsed = self._try_extract_mindmap(content)
        if parsed is None:
            # If LLM didn't return valid JSON, fallback to echoing original + explanation
            explanation = "AI 未能生成有效结构，已保持原图。"
            return req.mindmap, explanation

        # Validate & sanitise
        new_map = self._sanitise_mindmap(parsed)
        explanation = self._try_extract_explanation(content) or "脑图已更新。"
        return new_map, explanation

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_mindmap_system_prompt(self, mindmap: MindMap) -> str:
        nodes_text = "\n".join(
            f"- [{n.id}] {n.label}" + (f" (color: {n.color})" if n.color else "")
            for n in mindmap.nodes
        )
        edges_text = "\n".join(
            f"- {e.from_} → {e.to}"
            for e in mindmap.edges
        )
        return (
            "You are a 3D mindmap AI assistant. The user is interacting with a visual mindmap.\n\n"
            "CURRENT MINDMAP STRUCTURE:\n"
            f"Nodes ({len(mindmap.nodes)}):\n{nodes_text}\n\n"
            f"Edges ({len(mindmap.edges)}):\n{edges_text}\n\n"
            "RULES:\n"
            "1. Answer the user's question based on the mindmap context.\n"
            "2. If the user wants to modify the map, you MAY embed a JSON block "
            "under ```json ... ``` containing the updated full mindmap (nodes + edges).\n"
            "3. Keep the root node id unchanged unless the user explicitly asks to rename it.\n"
            "4. Use Markdown in your reply. Be concise but helpful."
        )

    def _build_update_system_prompt(self, mindmap: MindMap, instruction: str) -> str:
        nodes_text = "\n".join(
            f"- [{n.id}] {n.label}" + (f" (color: {n.color})" if n.color else "")
            for n in mindmap.nodes
        )
        edges_text = "\n".join(
            f"- {e.from_} → {e.to}"
            for e in mindmap.edges
        )
        return (
            "You are a mindmap restructuring engine. "
            "Given a user instruction and the current mindmap, produce a COMPLETE new mindmap.\n\n"
            "CURRENT MINDMAP:\n"
            f"Nodes ({len(mindmap.nodes)}):\n{nodes_text}\n\n"
            f"Edges ({len(mindmap.edges)}):\n{edges_text}\n\n"
            f"USER INSTRUCTION: {instruction}\n\n"
            "RESPONSE FORMAT (strict JSON inside a markdown code block):\n"
            "```json\n"
            "{\n"
            '  "nodes": [\n'
            '    { "id": "root", "label": "Root Label", "color": "#22d3ee" },\n'
            '    ...\n'
            "  ],\n"
            '  "edges": [\n'
            '    { "from": "root", "to": "child" },\n'
            '    ...\n'
            "  ]\n"
            "}\n"
            "```\n\n"
            "RULES:\n"
            "1. Every node must have a unique string `id` and a `label`.\n"
            "2. Every `from` and `to` in edges MUST reference an existing node `id`.\n"
            "3. Keep the original root node id if it still makes sense; otherwise create a new root.\n"
            "4. `color` is optional (hex string).\n"
            "5. Do NOT return null values — omit optional fields entirely.\n"
            "6. After the JSON block, you may add a short `explanation:` line.\n"
        )

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _try_extract_mindmap(self, text: str) -> Optional[MindMap]:
        """Look for a ```json ... ``` block and parse it as MindMap."""
        # Find fenced JSON block
        match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
        if not match:
            # Try plain JSON object
            match = re.search(r"(\{\s*\"nodes\"\s*:\s*\[.*?\]\s*,\s*\"edges\"\s*:\s*\[.*?\]\s*\})", text, re.DOTALL)
            if not match:
                return None
        json_str = match.group(1)
        try:
            data = json.loads(json_str)
            if "nodes" not in data or "edges" not in data:
                return None
            return self._sanitise_mindmap_dict(data)
        except Exception:
            return None

    def _strip_json_block(self, text: str) -> str:
        """Remove the fenced JSON block from the text so the user doesn't see it."""
        text = re.sub(r"```json\s*\n.*?\n```", "", text, flags=re.DOTALL)
        text = text.strip()
        return text

    def _try_extract_explanation(self, text: str) -> Optional[str]:
        """Look for an `explanation:` line after the JSON block."""
        m = re.search(r"explanation[:：]\s*(.+)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    def _sanitise_mindmap_dict(self, data: Dict[str, Any]) -> MindMap:
        """Build a validated MindMap from a raw dict."""
        raw_nodes = data.get("nodes", [])
        raw_edges = data.get("edges", [])

        nodes: List[MindMapNode] = []
        seen_ids = set()
        for rn in raw_nodes:
            nid = str(rn.get("id", ""))
            if not nid or nid in seen_ids:
                continue
            seen_ids.add(nid)
            nodes.append(MindMapNode(
                id=nid,
                label=str(rn.get("label", nid)),
                color=rn.get("color") if rn.get("color") else None,
            ))

        # Ensure at least one root-like node exists
        if not nodes:
            nodes.append(MindMapNode(id="root", label="Root"))

        edges: List[MindMapEdge] = []
        for re_ in raw_edges:
            fr = str(re_.get("from", re_.get("from_", "")))
            to = str(re_.get("to", ""))
            if fr and to and fr in seen_ids and to in seen_ids and fr != to:
                edges.append(MindMapEdge(from_=fr, to=to))

        return MindMap(nodes=nodes, edges=edges)

    def _sanitise_mindmap(self, mindmap: MindMap) -> MindMap:
        """Deduplicate nodes, drop dangling edges, ensure root exists."""
        return self._sanitise_mindmap_dict({
            "nodes": [n.model_dump(by_alias=True) for n in mindmap.nodes],
            "edges": [e.model_dump(by_alias=True) for e in mindmap.edges],
        })

    # ------------------------------------------------------------------
    # Fallbacks when no API key is configured
    # ------------------------------------------------------------------

    def _mock_chat_reply(self, req: ChatRequest) -> str:
        """Return a sensible canned reply when LLM is unavailable."""
        last_user_msg = ""
        for m in reversed(req.messages):
            if m.role == "user":
                last_user_msg = m.content
                break
        node_count = len(req.mindmap.nodes)
        edge_count = len(req.mindmap.edges)

        if "总结" in last_user_msg or "summary" in last_user_msg.lower():
            labels = ", ".join(n.label for n in req.mindmap.nodes[:5])
            return (
                f"当前脑图包含 **{node_count}** 个节点、**{edge_count}** 条连接。\n\n"
                f"核心主题为：{labels} 等。您可以继续补充细节或让我帮您扩展分支。"
            )

        if "什么" in last_user_msg or "?" in last_user_msg or "？" in last_user_msg:
            return (
                f"这是一个包含 {node_count} 个节点的脑图。\n"
                "我目前处于离线模式，无法调用大模型。"
                "请在 `.env` 中配置 `DASHSCOPE_API_KEY` 以启用 AI 问答功能。"
            )

        return (
            f"收到您的消息。当前脑图有 {node_count} 个节点、{edge_count} 条边。\n"
            "（离线模式：未配置 LLM API Key）"
        )

    def _mock_update_mindmap(self, req: MindMapUpdateRequest) -> Tuple[MindMap, str]:
        """Perform a simple deterministic mutation when LLM is unavailable."""
        nodes = list(req.mindmap.nodes)
        edges = list(req.mindmap.edges)
        instruction = req.instruction

        # Simple keyword-based mutations
        inst_lower = instruction.lower()

        if any(k in inst_lower for k in ["删除", "remove", "删掉", "去掉", "delete"]):
            # Remove last non-root node
            non_root = [n for n in nodes if n.id != "root"]
            if non_root:
                to_remove = non_root[-1]
                nodes = [n for n in nodes if n.id != to_remove.id]
                edges = [e for e in edges if e.from_ != to_remove.id and e.to != to_remove.id]
                return MindMap(nodes=nodes, edges=edges), f"已删除节点 [{to_remove.label}]。"
            return MindMap(nodes=nodes, edges=edges), "没有可删除的节点。"

        if any(k in inst_lower for k in ["添加", "新增", "add", "insert", "扩展", "展开", "create"]):
            # Add a demo child under root or last node
            parent_id = "root"
            parent_candidates = [n.id for n in nodes]
            if parent_candidates:
                parent_id = parent_candidates[0]

            new_id = f"node-{len(nodes)+1}"
            label = "新节点"
            if "营销" in instruction or "market" in inst_lower:
                label = "营销策略"
            elif "产品" in instruction or "product" in inst_lower:
                label = "产品规划"
            elif "技术" in instruction or "tech" in inst_lower:
                label = "技术架构"
            elif "测试" in instruction or "test" in inst_lower:
                label = "测试节点"
            else:
                # Try to extract a meaningful label from the instruction
                cleaned = instruction.strip(".?!")
                label = cleaned[:12] if len(cleaned) <= 24 else "新分支"

            nodes.append(MindMapNode(id=new_id, label=label, color="#a855f7"))
            edges.append(MindMapEdge(from_=parent_id, to=new_id))
            return MindMap(nodes=nodes, edges=edges), f"已添加节点 [{label}]。"

        if any(k in inst_lower for k in ["重命名", "改名", "rename", "改成", "change name"]):
            # Rename last node
            if nodes:
                target = nodes[-1]
                new_label = instruction.lower().replace("重命名", "").replace("rename", "").replace("改成", "").replace("change name", "").strip(" :to")
                if not new_label:
                    new_label = "已重命名"
                updated_nodes = [
                    MindMapNode(id=n.id, label=new_label if n.id == target.id else n.label, color=n.color)
                    for n in nodes
                ]
                return MindMap(nodes=updated_nodes, edges=edges), f"已将 [{target.label}] 重命名为 [{new_label}]。"

        # Default: echo original + note
        return MindMap(nodes=nodes, edges=edges), "未识别修改指令，保持原图。（离线模式：请配置 DASHSCOPE_API_KEY 以启用 AI 改图）"
