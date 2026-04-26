import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Loader2, ChevronRight, ChevronLeft, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";
import type { ChatMessage, MindMap } from "./types";
import { cn } from "@/lib/utils";
import {
  API_BASE_URL,
  chatWithBackend,
  updateMindmapWithBackend,
  looksLikeMutation,
} from "@/lib/api";

interface Props {
  mindmap: MindMap;
  onMindmapUpdate: (m: MindMap) => void;
  collapsed: boolean;
  onToggle: () => void;
}

const SUGGESTIONS = [
  "为这个脑图添加3个相关分支",
  "总结当前脑图的核心思路",
  "把『新节点』替换为更贴切的命名",
  "重组结构，让逻辑更清晰",
];

export default function ChatPanel({
  mindmap,
  onMindmapUpdate,
  collapsed,
  onToggle,
}: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "你好！我是你的脑图 AI 助手 ✨\n\n你可以问我关于当前脑图的任何问题，或者让我帮你**添加、修改、重组**节点。试试下面的快捷指令？",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    const userMsg: ChatMessage = { role: "user", content: trimmed };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      // 根据用户输入决定走 /chat 还是 /mindmap/update
      if (looksLikeMutation(trimmed)) {
        const data = await updateMindmapWithBackend({
          instruction: trimmed,
          mindmap,
        });
        if (data.mindmap) {
          onMindmapUpdate(data.mindmap);
          toast.success("脑图已由 AI 更新");
        }
        setMessages((m) => [
          ...m,
          { role: "assistant", content: data.explanation || "已更新脑图。" },
        ]);
      } else {
        const data = await chatWithBackend({ messages: next, mindmap });
        setMessages((m) => [
          ...m,
          { role: "assistant", content: data.reply || "(无响应)" },
        ]);
        if (data.updatedMindmap) {
          onMindmapUpdate(data.updatedMindmap);
          toast.success("脑图已由 AI 更新");
        }
      }
    } catch (e: unknown) {
      const msg =
        e instanceof Error
          ? `${e.message}（后端地址：${API_BASE_URL}，请确认 Python 服务已启动并允许 CORS）`
          : "请求失败";
      toast.error(msg);
      setMessages((m) => [...m, { role: "assistant", content: `⚠️ ${msg}` }]);
    } finally {
      setLoading(false);
    }
  };

  if (collapsed) {
    return (
      <div className="w-12 panel rounded-2xl flex flex-col items-center py-3 gap-2">
        <Button size="icon" variant="ghost" onClick={onToggle} className="h-8 w-8">
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Sparkles className="h-4 w-4 text-accent mt-2" />
      </div>
    );
  }

  return (
    <div className="w-80 panel rounded-2xl flex flex-col overflow-hidden shadow-panel">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/60">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-primary flex items-center justify-center shadow-glow">
            <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
          </div>
          <div>
            <h2 className="text-sm font-semibold tracking-wide">AI 脑图助手</h2>
            <p className="text-[10px] text-muted-foreground">理解 · 提问 · 修改</p>
          </div>
        </div>
        <Button size="icon" variant="ghost" className="h-7 w-7" onClick={onToggle}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin px-3 py-3 space-y-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "flex gap-2",
              m.role === "user" ? "flex-row-reverse" : "flex-row",
            )}
          >
            <div
              className={cn(
                "h-6 w-6 rounded-md flex-shrink-0 flex items-center justify-center text-[10px]",
                m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-accent/80 text-accent-foreground",
              )}
            >
              {m.role === "user" ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
            </div>
            <div
              className={cn(
                "max-w-[80%] rounded-xl px-3 py-2 text-xs leading-relaxed",
                m.role === "user"
                  ? "bg-primary/15 text-foreground border border-primary/30"
                  : "bg-muted/40 border border-border/60",
              )}
            >
              <div className="prose prose-invert prose-xs max-w-none [&_p]:my-1 [&_ul]:my-1 [&_li]:my-0">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="h-6 w-6 rounded-md bg-accent/80 flex items-center justify-center">
              <Bot className="h-3 w-3 text-accent-foreground" />
            </div>
            <div className="bg-muted/40 border border-border/60 rounded-xl px-3 py-2 flex items-center gap-2">
              <Loader2 className="h-3 w-3 animate-spin text-primary" />
              <span className="text-xs text-muted-foreground">思考中...</span>
            </div>
          </div>
        )}
      </div>

      {messages.length <= 1 && (
        <div className="px-3 pb-2 flex flex-wrap gap-1.5">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="text-[10px] px-2 py-1 rounded-full bg-muted/40 hover:bg-muted border border-border/60 text-muted-foreground hover:text-foreground transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="p-3 border-t border-border/60">
        <div className="relative">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            placeholder="询问或指令脑图... (Enter 发送)"
            rows={2}
            className="resize-none text-xs bg-muted/20 border-border/60 pr-10 scrollbar-thin"
          />
          <Button
            size="icon"
            className="absolute bottom-2 right-2 h-7 w-7 bg-gradient-primary hover:opacity-90"
            disabled={loading || !input.trim()}
            onClick={() => send(input)}
          >
            <Send className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}