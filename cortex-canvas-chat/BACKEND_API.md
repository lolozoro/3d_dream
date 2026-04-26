# Python 后端对接文档

本前端通过 HTTP JSON 调用你的 Python 后端。本文说明：**前端在什么时候、用什么请求体、调用哪个 URL、期望什么响应、如何处理错误**，并附 FastAPI / Flask 的最小骨架，方便你直接对齐。

---

## 1. 前端如何拼接 URL

```
最终 URL = VITE_API_BASE_URL + 路径
```

- `VITE_API_BASE_URL` 来自项目根目录的 `.env.local`，默认 `http://localhost:8000`
- 前端代码集中在 [`src/lib/api.ts`](./src/lib/api.ts)
- 修改 `.env.local` 后**必须重启 `npm run dev`**，Vite 才会读取新值

前端启动：
```bash
echo 'VITE_API_BASE_URL=http://localhost:8000' > .env.local
npm install
npm run dev    # 打开 http://localhost:8080
```

---

## 2. 前端何时调用哪个接口

用户在右侧聊天框按 Enter 后，前端 [`ChatPanel.tsx`](./src/components/mindmap/ChatPanel.tsx) 做如下判断：

| 用户输入特征 | 调用接口 | 用途 |
|---|---|---|
| 含关键词：`添加 / 新增 / 删除 / 修改 / 改成 / 替换 / 重组 / 扩展 / 展开 / add / remove / rename …` | `POST /mindmap/update` | 改图 |
| 其他（提问、总结、解释等） | `POST /chat` | 问答 |

关键词列表见 `src/lib/api.ts` 的 `MUTATION_KEYWORDS`，可自行修改。

---

## 3. 共用数据结构

```ts
type MindMapNode = {
  id: string;        // 必填，唯一，建议英文小写+数字，例如 "root", "ai-1"
  label: string;     // 必填，节点显示文本
  color?: string;    // 可选，hex 颜色，例如 "#22d3ee"
};

type MindMapEdge = {
  from: string;      // 必填，起点节点 id（必须存在于 nodes 中）
  to: string;        // 必填，终点节点 id（必须存在于 nodes 中）
};

type MindMap = {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};
```

**重要约束（后端必须遵守，否则前端会渲染异常）：**
- `nodes[].id` 全局唯一，不能重复
- `edges[].from` 与 `edges[].to` 必须能在 `nodes` 里找到
- 至少保留 1 个根节点（一般沿用前端传来的 `"root"`）
- 不要用 `null`，不需要的字段直接省略或不返回

---

## 4. 接口一：`POST /chat` —— 纯问答

### 4.1 请求

- **URL**：`http://localhost:8000/chat`
- **方法**：`POST`
- **Header**：`Content-Type: application/json`
- **Body**：

```json
{
  "messages": [
    { "role": "assistant", "content": "你好！我是你的脑图 AI 助手 ✨" },
    { "role": "user", "content": "总结一下这张脑图的核心思路" }
  ],
  "mindmap": {
    "nodes": [
      { "id": "root", "label": "Neural Mind", "color": "#22d3ee" },
      { "id": "ai",   "label": "AI 助手",     "color": "#a855f7" }
    ],
    "edges": [
      { "from": "root", "to": "ai" }
    ]
  }
}
```

说明：
- `messages`：完整的历史会话（包含助手和用户）。后端可直接拼给 LLM。
- `mindmap`：当前脑图快照，给 LLM 做上下文。

### 4.2 响应（HTTP 200）

```json
{
  "reply": "这张脑图围绕 **Neural Mind** 展开，核心是 AI 助手……",
  "updatedMindmap": null
}
```

- `reply`：**必填**，字符串，支持 Markdown，会渲染到右侧聊天气泡。
- `updatedMindmap`：**可选**，如果你希望在问答时也顺手改图，就返回完整的新 `MindMap`，否则给 `null` 或省略。

### 4.3 curl 测试

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages":[{"role":"user","content":"你好"}],
    "mindmap":{"nodes":[{"id":"root","label":"Demo"}],"edges":[]}
  }'
```

---

## 5. 接口二：`POST /mindmap/update` —— 结构变更

### 5.1 请求

- **URL**：`http://localhost:8000/mindmap/update`
- **方法**：`POST`
- **Header**：`Content-Type: application/json`
- **Body**：

```json
{
  "instruction": "为这个脑图添加3个产品营销相关分支",
  "mindmap": {
    "nodes": [{ "id": "root", "label": "Neural Mind", "color": "#22d3ee" }],
    "edges": []
  }
}
```

- `instruction`：用户原始输入的自然语言指令（前端已识别为“改图意图”）。
- `mindmap`：当前脑图快照。

### 5.2 响应（HTTP 200）

```json
{
  "mindmap": {
    "nodes": [
      { "id": "root",      "label": "Neural Mind",  "color": "#22d3ee" },
      { "id": "mkt",       "label": "产品营销",      "color": "#a855f7" },
      { "id": "mkt-brand", "label": "品牌定位",      "color": "#f472b6" },
      { "id": "mkt-channel","label": "投放渠道",     "color": "#fbbf24" },
      { "id": "mkt-data",  "label": "数据复盘",      "color": "#34d399" }
    ],
    "edges": [
      { "from": "root", "to": "mkt" },
      { "from": "mkt",  "to": "mkt-brand" },
      { "from": "mkt",  "to": "mkt-channel" },
      { "from": "mkt",  "to": "mkt-data" }
    ]
  },
  "explanation": "已新增 1 个营销主分支和 3 个子节点。"
}
```

- `mindmap`：**必填**，**完整**的新脑图（**全量替换**，不是增量 patch）。
- `explanation`：**可选**，会作为助手消息显示在聊天气泡。

### 5.3 curl 测试

```bash
curl -X POST http://localhost:8000/mindmap/update \
  -H "Content-Type: application/json" \
  -d '{
    "instruction":"添加一个测试节点",
    "mindmap":{"nodes":[{"id":"root","label":"Demo"}],"edges":[]}
  }'
```

---

## 6. 错误响应（两个接口通用）

- **HTTP 状态码**：非 2xx（推荐 4xx / 5xx）
- **Body**：

```json
{ "error": "AI 服务调用失败：xxx" }
```

也接受 FastAPI 默认的 `{"detail": "..."}`，前端两种都能解析并 toast 显示。

---

## 7. CORS（必做，否则浏览器会拦截）

前端在 `http://localhost:8080` 运行，后端必须允许跨域。

### FastAPI

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
```

### Flask

```python
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": ["http://localhost:8080", "http://127.0.0.1:8080"]}})
```

---

## 8. 最小可运行后端骨架（仅供对齐字段，不含 LLM 调用）

### 8.1 FastAPI

```python
# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["*"], allow_headers=["*"],
)

class Node(BaseModel):
    id: str
    label: str
    color: Optional[str] = None

class Edge(BaseModel):
    from_: str
    to: str
    class Config:
        fields = {"from_": "from"}   # JSON 字段名是 "from"
        populate_by_name = True

class MindMap(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatReq(BaseModel):
    messages: List[ChatMessage]
    mindmap: MindMap

class UpdateReq(BaseModel):
    instruction: str
    mindmap: MindMap

@app.post("/chat")
def chat(req: ChatReq):
    # TODO: 调用你的 LLM，使用 req.messages + req.mindmap 生成回答
    return {"reply": f"收到 {len(req.messages)} 条消息，当前 {len(req.mindmap.nodes)} 个节点。"}

@app.post("/mindmap/update")
def update(req: UpdateReq):
    # TODO: 让 LLM 根据 req.instruction 生成新 mindmap
    new_map = req.mindmap.model_dump(by_alias=True)
    new_map["nodes"].append({"id": "demo", "label": req.instruction[:10]})
    new_map["edges"].append({"from": "root", "to": "demo"})
    return {"mindmap": new_map, "explanation": "已添加示例节点"}

# 启动：uvicorn server:app --reload --port 8000
```

### 8.2 Flask

```python
# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:8080"]}})

@app.post("/chat")
def chat():
    data = request.get_json()
    messages = data["messages"]
    mindmap  = data["mindmap"]
    # TODO: 调 LLM
    return jsonify({"reply": f"收到 {len(messages)} 条消息"})

@app.post("/mindmap/update")
def update():
    data = request.get_json()
    instruction = data["instruction"]
    mindmap     = data["mindmap"]
    mindmap["nodes"].append({"id": "demo", "label": instruction[:10]})
    mindmap["edges"].append({"from": "root", "to": "demo"})
    return jsonify({"mindmap": mindmap, "explanation": "已添加示例节点"})

# 启动：flask --app server run --port 8000
```

---

## 9. 联调排错清单

按顺序检查：

1. **前端有没有发出请求？** 浏览器 F12 → Network → 过滤 `chat` / `update`。如果根本没有请求，看 Console 报错。
2. **请求地址对不对？** Network 里看 Request URL 是不是 `http://localhost:8000/chat`。如果还是别的地址，说明 `.env.local` 没生效 → 重启 `npm run dev`。
3. **CORS 错误？** Console 报 `blocked by CORS policy` → 后端没开 CORS，照第 7 节配置。
4. **404？** 后端路由没注册，或者前缀不对（不要加 `/api` 前缀，除非你也改了 `src/lib/api.ts`）。
5. **422 / 400？** Pydantic / 校验错误，对照第 4、5 节请求体字段名（注意 `from` / `to` 是字符串）。
6. **200 但前端没更新脑图？** 检查响应字段名：`/chat` 用 `reply`+可选 `updatedMindmap`；`/mindmap/update` 用 `mindmap`+可选 `explanation`。
7. **节点显示乱了？** 检查所有 `edges.from/to` 是否都能在 `nodes[].id` 里找到。

---

## 10. 改前端约定的地方

如果你的后端路径不是 `/chat` 和 `/mindmap/update`，**只改一个文件**：[`src/lib/api.ts`](./src/lib/api.ts)，把 `postJSON("/chat", …)` 和 `postJSON("/mindmap/update", …)` 里的路径改成你的即可，其他代码不用动。