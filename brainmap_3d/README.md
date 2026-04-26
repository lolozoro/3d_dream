# BrainMap 3D Backend

支持3D脑图展示的后端服务项目，提供完整的脑图CRUD接口、3D空间查询、图算法以及大模型智能问答能力。

## 项目结构

```
brainmap_3d/
├── src/
│   ├── api/              # REST API 路由层
│   │   ├── brainmap.py   # 脑图、节点、边、3D查询接口
│   │   └── llm.py        # 大模型问答、摘要、扩展接口
│   ├── core/             # 核心配置
│   │   └── config.py     # 环境变量与配置管理
│   ├── db/               # 数据库
│   │   ├── base.py       # SQLAlchemy 基类
│   │   └── session.py    # 异步会话与引擎
│   ├── models/           # ORM 数据模型
│   │   ├── node.py       # 3D节点模型（坐标、层级、分组、可视化属性）
│   │   └── edge.py       # 边模型（关系类型、权重、3D控制点）
│   ├── schemas/          # Pydantic 数据校验
│   │   ├── node.py
│   │   ├── edge.py
│   │   ├── brainmap.py
│   │   └── llm.py
│   ├── services/         # 业务逻辑层
│   │   ├── brainmap.py   # 脑图CRUD + 图算法
│   │   └── llm_service.py # LLM上下文构建与调用
│   ├── llm/              # 大模型集成
│   │   ├── client.py     # OpenAI API 客户端封装
│   │   └── prompts.py    # 提示词模板与脑图上下文构建
│   ├── utils/            # 工具函数
│   │   └── graph_utils.py # 3D图算法工具
│   └── main.py           # FastAPI 应用入口
├── tests/                # 单元测试
├── requirements.txt
├── .env.example
└── README.md
```

## 核心功能

### 1. 3D脑图数据管理
- **节点(Node)**: 支持3D坐标 (`pos_x`, `pos_y`, `pos_z`)、层级(`layer`)、分组(`group_id`)、大小/颜色/形状/透明度等可视化属性
- **边(Edge)**: 支持关系类型、权重、方向、3D曲线控制点
- **层级与分组**: 天然支持多维数据组织，前端可按层级或分组进行3D空间排布

### 2. 3D空间查询
- `GET /api/v1/brainmaps/{id}/spatial-search` — 球体范围搜索
- `GET /api/v1/brainmaps/{id}/nodes?bbox={...}` — 包围盒过滤
- `POST /api/v1/brainmaps/{id}/subgraph` — 多跳子图提取
- `POST /api/v1/brainmaps/{id}/paths` — 节点间路径查找
- `POST /api/v1/brainmaps/{id}/neighbors` — 邻居查询

### 3. 大模型集成
- `POST /api/v1/llm/chat` — 基于脑图上下文的智能问答
- `POST /api/v1/llm/chat/stream` — 流式SSE问答
- `POST /api/v1/llm/summarize/{id}` — 脑图摘要
- `POST /api/v1/llm/suggest-connections/{id}` — AI建议新连接
- `POST /api/v1/llm/expand-node/{id}/{node_id}` — 为节点生成AI扩展建议

## 快速开始

### 1. 安装依赖

```bash
cd brainmap_3d
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，设置数据库和OpenAI API Key
```

### 3. 启动服务

```bash
# 方式1：同时启动后端 + 前端（推荐）
python start.py

# 方式2：仅启动后端 API
python -m src.main
```

启动后访问：
- **前端界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **数据接口**: http://localhost:8000/api/v1

> 前端文件位于 `frontend/` 目录，后端启动时会自动挂载为静态文件服务。
> 前端通过 CDN 引入 Three.js，无需额外构建步骤。

### 4. 运行测试

```bash
pytest tests/ -v
```

## 前端功能

本项目已包含完整的前端3D脑图编辑器，位于 `frontend/` 目录：

### 前端特性
- **3D 渲染**: 基于 Three.js，支持球体/立方体/圆锥/四面体等节点形状
- **交互操作**: 鼠标拖拽旋转视角、滚轮缩放、节点拖拽移动、Shift+点击连线
- **节点编辑**: 左侧面板实时编辑节点标签、类型、3D坐标、颜色、大小、透明度
- **自动布局**: 支持层级布局、球面布局等多种自动排布算法
- **AI 助手**: 右侧聊天面板支持基于当前脑图的智能问答（流式输出）
  - 脑图摘要生成
  - AI建议新连接
  - 节点智能扩展

### 前端文件结构
```
frontend/
├── index.html          # 主页面
├── css/
│   └── style.css       # 样式
└── js/
    ├── main.js         # 主逻辑（UI交互、API调用、状态管理）
    ├── engine3d.js     # Three.js 3D渲染引擎
    └── api.js          # 后端API封装
```

### 前端快捷键
| 操作 | 说明 |
|------|------|
| 左键拖拽空白处 | 旋转视角 |
| 滚轮 | 缩放 |
| 右键拖拽 | 平移 |
| 左键点击节点 | 选中 / 显示属性 |
| 左键拖拽节点 | 移动节点位置 |
| Shift + 点击节点 | 开始连接（再点击目标完成） |
| 双击节点 | 聚焦该节点 |

### 自定义前端开发
如需扩展前端，直接编辑 `frontend/js/` 下的文件即可，无需构建工具。
前端通过 `fetch` 调用后端 `http://localhost:8000/api/v1` 接口。

## 数据库支持

- **SQLite** (默认): 适合本地开发和测试
- **PostgreSQL**: 生产环境推荐，支持更复杂的3D空间查询和大量数据

## API 示例

### 创建脑图
```bash
curl -X POST "http://localhost:8000/api/v1/brainmaps" \
  -H "Content-Type: application/json" \
  -d '{"brainmap_id": "my-map", "title": "My 3D BrainMap"}'
```

### 添加3D节点
```bash
curl -X POST "http://localhost:8000/api/v1/brainmaps/my-map/nodes" \
  -H "Content-Type: application/json" \
  -d '{
    "brainmap_id": "my-map",
    "label": "AI",
    "node_type": "topic",
    "pos_x": 10, "pos_y": 5, "pos_z": -3,
    "size": 2, "color": "#3B82F6"
  }'
```

### 连接节点
```bash
curl -X POST "http://localhost:8000/api/v1/brainmaps/my-map/edges" \
  -H "Content-Type: application/json" \
  -d '{"brainmap_id": "my-map", "source_id": 1, "target_id": 2, "relation_type": "related"}'
```

### AI问答
```bash
curl -X POST "http://localhost:8000/api/v1/llm/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "这个脑图的核心主题是什么？",
    "brainmap_id": "my-map"
  }'
```
