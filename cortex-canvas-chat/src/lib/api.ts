// 前端 API 客户端：对接 Python 后端
// 通过 VITE_API_BASE_URL 配置后端地址（默认 http://localhost:8000）
import type { ChatMessage, MindMap } from "@/components/mindmap/types";

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ||
  "http://localhost:8000";

export interface ChatRequest {
  messages: ChatMessage[];
  mindmap: MindMap;
}

export interface ChatResponse {
  reply: string;
  /** 后端如果决定改图，可一并返回，前端会合并到 /mindmap/update 的结果上 */
  updatedMindmap?: MindMap | null;
  error?: string;
}

export interface MindmapUpdateRequest {
  /** 自然语言指令，比如 "添加一个产品营销分支" */
  instruction: string;
  mindmap: MindMap;
}

export interface MindmapUpdateResponse {
  mindmap: MindMap;
  explanation?: string;
  error?: string;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    throw new Error(`后端返回了非 JSON 内容 (${res.status}): ${text.slice(0, 200)}`);
  }
  if (!res.ok) {
    const msg =
      (data as { error?: string; detail?: string } | null)?.error ||
      (data as { error?: string; detail?: string } | null)?.detail ||
      `请求失败 (${res.status})`;
    throw new Error(msg);
  }
  return data as T;
}

/** POST /chat —— 纯问答 */
export function chatWithBackend(body: ChatRequest) {
  return postJSON<ChatResponse>("/chat", body);
}

/** POST /mindmap/update —— 让后端根据指令返回新的脑图 */
export function updateMindmapWithBackend(body: MindmapUpdateRequest) {
  return postJSON<MindmapUpdateResponse>("/mindmap/update", body);
}

/** 简单的关键词判断：用户的输入是否像“修改脑图”的指令 */
const MUTATION_KEYWORDS = [
  "添加", "新增", "加一个", "加个", "插入",
  "删除", "去掉", "移除",
  "修改", "改成", "替换", "重命名",
  "重组", "重构", "整理", "优化结构", "拆分", "合并",
  "扩展", "展开", "细化",
  "add", "remove", "delete", "rename", "restructure", "expand",
];
export function looksLikeMutation(text: string) {
  const t = text.toLowerCase();
  return MUTATION_KEYWORDS.some((k) => t.includes(k.toLowerCase()));
}