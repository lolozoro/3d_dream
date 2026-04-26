import type { MindMap } from "./types";

/**
 * Force-directed-ish layered layout. Places nodes in 3D using
 * BFS layers from the first node, distributing them around spheres.
 */
export function computeLayout(mm: MindMap): Record<string, [number, number, number]> {
  const positions: Record<string, [number, number, number]> = {};
  if (mm.nodes.length === 0) return positions;

  // Build adjacency
  const adj: Record<string, string[]> = {};
  mm.nodes.forEach((n) => (adj[n.id] = []));
  mm.edges.forEach((e) => {
    if (adj[e.from] && adj[e.to]) {
      adj[e.from].push(e.to);
      adj[e.to].push(e.from);
    }
  });

  // BFS layers from first node
  const root = mm.nodes[0].id;
  const layer: Record<string, number> = { [root]: 0 };
  const queue: string[] = [root];
  while (queue.length) {
    const cur = queue.shift()!;
    for (const nb of adj[cur] ?? []) {
      if (layer[nb] === undefined) {
        layer[nb] = layer[cur] + 1;
        queue.push(nb);
      }
    }
  }
  // Disconnected nodes => own layer
  let maxLayer = Math.max(0, ...Object.values(layer));
  mm.nodes.forEach((n) => {
    if (layer[n.id] === undefined) {
      maxLayer += 1;
      layer[n.id] = maxLayer;
    }
  });

  // Group by layer
  const groups: Record<number, string[]> = {};
  Object.entries(layer).forEach(([id, l]) => {
    (groups[l] ||= []).push(id);
  });

  Object.entries(groups).forEach(([lStr, ids]) => {
    const l = Number(lStr);
    if (l === 0) {
      positions[ids[0]] = [0, 0, 0];
      return;
    }
    const radius = l * 3.2;
    const count = ids.length;
    ids.forEach((id, i) => {
      const phi = Math.acos(1 - (2 * (i + 0.5)) / count); // 0..pi
      const theta = Math.PI * (1 + Math.sqrt(5)) * i; // golden angle
      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);
      positions[id] = [x, y, z];
    });
  });

  return positions;
}