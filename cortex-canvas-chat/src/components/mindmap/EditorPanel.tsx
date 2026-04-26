import { Plus, Trash2, Link2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { MindMap } from "./types";
import { useState } from "react";

interface Props {
  mindmap: MindMap;
  setMindmap: (m: MindMap) => void;
  selectedId: string | null;
  setSelectedId: (id: string | null) => void;
}

export default function EditorPanel({
  mindmap,
  setMindmap,
  selectedId,
  setSelectedId,
}: Props) {
  const selected = mindmap.nodes.find((n) => n.id === selectedId);
  const [linkMode, setLinkMode] = useState(false);
  const [linkFrom, setLinkFrom] = useState<string | null>(null);

  const addNode = () => {
    const id = `n-${Date.now().toString(36)}`;
    const newNode = { id, label: "新节点" };
    const edges = selectedId
      ? [...mindmap.edges, { from: selectedId, to: id }]
      : mindmap.edges;
    setMindmap({ nodes: [...mindmap.nodes, newNode], edges });
    setSelectedId(id);
  };

  const deleteNode = () => {
    if (!selected) return;
    setMindmap({
      nodes: mindmap.nodes.filter((n) => n.id !== selected.id),
      edges: mindmap.edges.filter(
        (e) => e.from !== selected.id && e.to !== selected.id,
      ),
    });
    setSelectedId(null);
  };

  const updateLabel = (label: string) => {
    if (!selected) return;
    setMindmap({
      ...mindmap,
      nodes: mindmap.nodes.map((n) =>
        n.id === selected.id ? { ...n, label } : n,
      ),
    });
  };

  const startLink = () => {
    if (!selected) return;
    setLinkFrom(selected.id);
    setLinkMode(true);
  };

  // Handle link target via clicking another node — exposed via window event
  if (linkMode && selected && linkFrom && selected.id !== linkFrom) {
    const exists = mindmap.edges.some(
      (e) =>
        (e.from === linkFrom && e.to === selected.id) ||
        (e.from === selected.id && e.to === linkFrom),
    );
    if (!exists) {
      setMindmap({
        ...mindmap,
        edges: [...mindmap.edges, { from: linkFrom, to: selected.id }],
      });
    }
    setLinkMode(false);
    setLinkFrom(null);
  }

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 panel rounded-2xl px-3 py-2 flex items-center gap-2 shadow-panel">
      <Button size="sm" variant="ghost" className="h-8 gap-1.5" onClick={addNode}>
        <Plus className="h-3.5 w-3.5" />
        <span className="text-xs">{selectedId ? "添加子节点" : "添加节点"}</span>
      </Button>

      {selected && (
        <>
          <div className="h-5 w-px bg-border/60" />
          <Input
            value={selected.label}
            onChange={(e) => updateLabel(e.target.value)}
            className="h-8 w-40 text-xs bg-muted/30 border-border/60"
            placeholder="节点名"
          />
          <Button
            size="sm"
            variant={linkMode ? "default" : "ghost"}
            className="h-8 gap-1.5"
            onClick={startLink}
          >
            <Link2 className="h-3.5 w-3.5" />
            <span className="text-xs">
              {linkMode ? "点击目标节点..." : "连线"}
            </span>
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 gap-1.5 text-destructive hover:text-destructive"
            onClick={deleteNode}
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span className="text-xs">删除</span>
          </Button>
          {linkMode && (
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              onClick={() => {
                setLinkMode(false);
                setLinkFrom(null);
              }}
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          )}
        </>
      )}
    </div>
  );
}