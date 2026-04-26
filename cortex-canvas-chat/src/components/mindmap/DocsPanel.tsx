import { useState } from "react";
import { Plus, FileText, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { DocItem } from "./types";
import { cn } from "@/lib/utils";

interface Props {
  docs: DocItem[];
  setDocs: (d: DocItem[]) => void;
  collapsed: boolean;
  onToggle: () => void;
}

export default function DocsPanel({ docs, setDocs, collapsed, onToggle }: Props) {
  const [activeId, setActiveId] = useState(docs[0]?.id ?? null);
  const active = docs.find((d) => d.id === activeId) ?? null;

  const addDoc = () => {
    const id = `doc-${Date.now()}`;
    const next: DocItem = { id, title: "新文档", content: "" };
    setDocs([next, ...docs]);
    setActiveId(id);
  };

  const removeDoc = (id: string) => {
    const next = docs.filter((d) => d.id !== id);
    setDocs(next);
    if (activeId === id) setActiveId(next[0]?.id ?? null);
  };

  const updateActive = (patch: Partial<DocItem>) => {
    if (!active) return;
    setDocs(docs.map((d) => (d.id === active.id ? { ...d, ...patch } : d)));
  };

  if (collapsed) {
    return (
      <div className="w-12 panel rounded-2xl flex flex-col items-center py-3 gap-2">
        <Button size="icon" variant="ghost" onClick={onToggle} className="h-8 w-8">
          <ChevronRight className="h-4 w-4" />
        </Button>
        <FileText className="h-4 w-4 text-muted-foreground mt-2" />
      </div>
    );
  }

  return (
    <div className="w-72 panel rounded-2xl flex flex-col overflow-hidden shadow-panel">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/60">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-primary shadow-glow" />
          <h2 className="text-sm font-semibold tracking-wide">文档区</h2>
        </div>
        <div className="flex items-center gap-1">
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={addDoc}>
            <Plus className="h-4 w-4" />
          </Button>
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={onToggle}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="flex-shrink-0 max-h-44 overflow-y-auto scrollbar-thin border-b border-border/60">
        {docs.length === 0 && (
          <div className="px-4 py-6 text-xs text-muted-foreground text-center">
            暂无文档，点击 + 添加
          </div>
        )}
        {docs.map((d) => (
          <button
            key={d.id}
            onClick={() => setActiveId(d.id)}
            className={cn(
              "w-full flex items-center gap-2 px-4 py-2 text-left text-xs group hover:bg-muted/50 transition-colors",
              activeId === d.id && "bg-muted/70 text-primary",
            )}
          >
            <FileText className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="truncate flex-1">{d.title}</span>
            <Trash2
              className="h-3 w-3 opacity-0 group-hover:opacity-60 hover:opacity-100"
              onClick={(e) => {
                e.stopPropagation();
                removeDoc(d.id);
              }}
            />
          </button>
        ))}
      </div>

      {active ? (
        <div className="flex-1 flex flex-col p-3 gap-2 overflow-hidden">
          <Input
            value={active.title}
            onChange={(e) => updateActive({ title: e.target.value })}
            className="h-8 text-sm bg-muted/30 border-border/60"
          />
          <Textarea
            value={active.content}
            onChange={(e) => updateActive({ content: e.target.value })}
            placeholder="在这里记录你的想法、参考资料..."
            className="flex-1 resize-none text-xs leading-relaxed bg-muted/20 border-border/60 scrollbar-thin"
          />
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-xs text-muted-foreground">
          选择或新建一个文档
        </div>
      )}
    </div>
  );
}