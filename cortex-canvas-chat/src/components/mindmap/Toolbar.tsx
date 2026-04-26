import { Brain, Download, Upload, RotateCw, Save, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { MindMap } from "./types";
import { toast } from "sonner";
import { useRef } from "react";

interface Props {
  mindmap: MindMap;
  setMindmap: (m: MindMap) => void;
  autoRotate: boolean;
  setAutoRotate: (v: boolean) => void;
}

export default function Toolbar({ mindmap, setMindmap, autoRotate, setAutoRotate }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(mindmap, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mindmap-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("已导出脑图 JSON");
  };

  const importJson = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result));
        if (Array.isArray(parsed.nodes) && Array.isArray(parsed.edges)) {
          setMindmap(parsed);
          toast.success("脑图已导入");
        } else {
          throw new Error("格式不正确");
        }
      } catch {
        toast.error("无效的脑图文件");
      }
    };
    reader.readAsText(file);
  };

  const save = () => {
    localStorage.setItem("mindmap-3d-data", JSON.stringify(mindmap));
    toast.success("已保存到本地");
  };

  return (
    <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
      <div className="panel rounded-2xl px-3 py-2 flex items-center gap-1.5 shadow-panel">
        <Button
          size="sm"
          variant={autoRotate ? "default" : "ghost"}
          className="h-8 gap-1.5"
          onClick={() => setAutoRotate(!autoRotate)}
        >
          <RotateCw className={`h-3.5 w-3.5 ${autoRotate ? "animate-spin" : ""}`} />
          <span className="text-xs">自动旋转</span>
        </Button>
        <div className="h-5 w-px bg-border/60" />
        <Button size="sm" variant="ghost" className="h-8 gap-1.5" onClick={save}>
          <Save className="h-3.5 w-3.5" />
          <span className="text-xs">保存</span>
        </Button>
        <Button size="sm" variant="ghost" className="h-8 gap-1.5" onClick={exportJson}>
          <Download className="h-3.5 w-3.5" />
          <span className="text-xs">导出</span>
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-8 gap-1.5"
          onClick={() => fileRef.current?.click()}
        >
          <Upload className="h-3.5 w-3.5" />
          <span className="text-xs">导入</span>
        </Button>
        <input
          ref={fileRef}
          type="file"
          accept="application/json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) importJson(f);
            e.target.value = "";
          }}
        />
      </div>
    </div>
  );
}

export function Brand() {
  return (
    <div className="absolute top-4 left-4 z-10 panel rounded-2xl px-3 py-2 flex items-center gap-2 shadow-panel">
      <div className="h-8 w-8 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow animate-pulse-glow">
        <Brain className="h-4 w-4 text-primary-foreground" />
      </div>
      <div>
        <h1 className="text-sm font-bold leading-tight text-gradient">Neural Mind</h1>
        <p className="text-[10px] text-muted-foreground leading-tight flex items-center gap-1">
          <Sparkles className="h-2.5 w-2.5" /> 3D 智能脑图工作台
        </p>
      </div>
    </div>
  );
}