from typing import List, Dict, Any, Tuple, Set
import math


def compute_bounding_box(nodes: List[Dict[str, Any]]) -> Dict[str, float]:
    """计算节点集合的3D包围盒"""
    if not nodes:
        return {"xmin": 0, "xmax": 0, "ymin": 0, "ymax": 0, "zmin": 0, "zmax": 0}

    xs = [n.get("pos_x", n.get("pos", {}).get("x", 0)) for n in nodes]
    ys = [n.get("pos_y", n.get("pos", {}).get("y", 0)) for n in nodes]
    zs = [n.get("pos_z", n.get("pos", {}).get("z", 0)) for n in nodes]

    return {
        "xmin": min(xs), "xmax": max(xs),
        "ymin": min(ys), "ymax": max(ys),
        "zmin": min(zs), "zmax": max(zs),
    }


def compute_center_of_gravity(nodes: List[Dict[str, Any]]) -> Tuple[float, float, float]:
    """计算重心"""
    if not nodes:
        return (0.0, 0.0, 0.0)
    xs = [n.get("pos_x", n.get("pos", {}).get("x", 0)) for n in nodes]
    ys = [n.get("pos_y", n.get("pos", {}).get("y", 0)) for n in nodes]
    zs = [n.get("pos_z", n.get("pos", {}).get("z", 0)) for n in nodes]
    return (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))


def euclidean_distance(n1: Dict[str, Any], n2: Dict[str, Any]) -> float:
    """计算两个节点之间的3D欧氏距离"""
    def get_pos(n):
        if "pos_x" in n:
            return (n["pos_x"], n["pos_y"], n["pos_z"])
        p = n.get("pos", {})
        return (p.get("x", 0), p.get("y", 0), p.get("z", 0))

    x1, y1, z1 = get_pos(n1)
    x2, y2, z2 = get_pos(n2)
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)


def build_adjacency_list(edges: List[Dict[str, Any]], directed: bool = False) -> Dict[int, Set[int]]:
    """从边列表构建邻接表"""
    adj = {}
    for e in edges:
        src = e.get("source_id")
        tgt = e.get("target_id")
        adj.setdefault(src, set()).add(tgt)
        if not directed:
            adj.setdefault(tgt, set()).add(src)
    return adj


def find_connected_components(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[List[int]]:
    """查找图中的连通分量"""
    node_ids = {n["id"] for n in nodes}
    adj = build_adjacency_list(edges, directed=False)
    visited = set()
    components = []

    def dfs(start, component):
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            component.append(cur)
            for neighbor in adj.get(cur, set()):
                if neighbor not in visited and neighbor in node_ids:
                    stack.append(neighbor)

    for nid in node_ids:
        if nid not in visited:
            comp = []
            dfs(nid, comp)
            components.append(comp)

    return components


def compute_spatial_clusters(nodes: List[Dict[str, Any]], radius: float = 5.0) -> Dict[int, int]:
    """基于3D距离的简单空间聚类（每个节点分配到距离最近的簇中心）"""
    if not nodes:
        return {}

    clusters = []
    node_to_cluster = {}

    for n in nodes:
        nid = n["id"]
        assigned = False
        for idx, center_id in enumerate(clusters):
            center = next((x for x in nodes if x["id"] == center_id), None)
            if center and euclidean_distance(n, center) <= radius:
                node_to_cluster[nid] = idx
                assigned = True
                break
        if not assigned:
            node_to_cluster[nid] = len(clusters)
            clusters.append(nid)

    return node_to_cluster
