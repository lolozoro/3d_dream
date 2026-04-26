import { useEffect, useState } from "react";
import MindMap3D from "@/components/mindmap/MindMap3D";
import DocsPanel from "@/components/mindmap/DocsPanel";
import ChatPanel from "@/components/mindmap/ChatPanel";
import EditorPanel from "@/components/mindmap/EditorPanel";
import Toolbar, { Brand } from "@/components/mindmap/Toolbar";
import type { DocItem, MindMap } from "@/components/mindmap/types";

const DEFAULT_MINDMAP: MindMap = {
  nodes: [
    { id: "root", label: "Neural Mind", color: "#22d3ee" },
    { id: "ai", label: "AI 助手", color: "#a855f7" },
    { id: "edit", label: "可视化编辑", color: "#f472b6" },
    { id: "doc", label: "文档关联", color: "#fbbf24" },
    { id: "export", label: "导入 / 导出", color: "#34d399" },
    { id: "chat", label: "自然语言指令", color: "#60a5fa" },
    { id: "rebuild", label: "智能重组", color: "#c084fc" },
    { id: "drag", label: "3D 旋转拖拽", color: "#fb7185" },
  ],
  edges: [
    { from: "root", to: "ai" },
    { from: "root", to: "edit" },
    { from: "root", to: "doc" },
    { from: "root", to: "export" },
    { from: "ai", to: "chat" },
    { from: "ai", to: "rebuild" },
    { from: "edit", to: "drag" },
  ],
};

const DEFAULT_DOCS: DocItem[] = [
  {
    id: "doc-welcome",
    title: "欢迎使用 Neural Mind",
    content:
      "这是一个 3D 智能脑图工作台。\n\n左侧记录你的思路与素材，中间是可旋转、可编辑的 3D 脑图，右侧是 AI 助手——可以让它帮你重组结构、补充节点、回答问题。\n\n试试在右侧输入：\n『为这个脑图添加一个关于产品营销的分支』",
  },
];

const Index = () => {
  const [mindmap, setMindmap] = useState<MindMap>(() => {
    try {
      const saved = localStorage.getItem("mindmap-3d-data");
      if (saved) return JSON.parse(saved);
    } catch { /* ignore */ }
    return DEFAULT_MINDMAP;
  });
  const [docs, setDocs] = useState<DocItem[]>(DEFAULT_DOCS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [autoRotate, setAutoRotate] = useState(false);
  const [docsCollapsed, setDocsCollapsed] = useState(false);
  const [chatCollapsed, setChatCollapsed] = useState(false);

  useEffect(() => {
    document.title = "Neural Mind · 3D 智能脑图";
  }, []);

  return (
    <div className="h-screen w-screen flex bg-background bg-glow overflow-hidden p-3 gap-3">
      <DocsPanel
        docs={docs}
        setDocs={setDocs}
        collapsed={docsCollapsed}
        onToggle={() => setDocsCollapsed(!docsCollapsed)}
      />

      <main className="flex-1 relative rounded-2xl overflow-hidden border border-border/60 bg-gradient-surface shadow-panel">
        <Brand />
        <Toolbar
          mindmap={mindmap}
          setMindmap={setMindmap}
          autoRotate={autoRotate}
          setAutoRotate={setAutoRotate}
        />
        <EditorPanel
          mindmap={mindmap}
          setMindmap={setMindmap}
          selectedId={selectedId}
          setSelectedId={setSelectedId}
        />
        <MindMap3D
          mindmap={mindmap}
          selectedId={selectedId}
          onSelect={setSelectedId}
          autoRotate={autoRotate}
        />
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 panel rounded-full px-4 py-1.5 text-[10px] text-muted-foreground shadow-panel">
          🖱️ 左键旋转 · 右键平移 · 滚轮缩放 · 点击节点编辑
        </div>
      </main>

      <ChatPanel
        mindmap={mindmap}
        onMindmapUpdate={setMindmap}
        collapsed={chatCollapsed}
        onToggle={() => setChatCollapsed(!chatCollapsed)}
      />
    </div>
  );
};

export default Index;
