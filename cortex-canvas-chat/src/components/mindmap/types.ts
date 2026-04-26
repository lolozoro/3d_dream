export interface MindMapNode {
  id: string;
  label: string;
  color?: string;
  position?: [number, number, number];
}

export interface MindMapEdge {
  from: string;
  to: string;
}

export interface MindMap {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface DocItem {
  id: string;
  title: string;
  content: string;
}