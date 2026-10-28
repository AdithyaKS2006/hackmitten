from typing import Any
import networkx as nx


def build_graph(graph_json: dict[str, Any]) -> nx.DiGraph:
    """
    Build directed dependency graph from JSON specification.
    Nodes: list of service names.
    Edges: list of [caller, callee] pairs (caller depends on callee).
    """
    g = nx.DiGraph()
    if not graph_json:
        return g

    nodes = graph_json.get("nodes", [])
    for node in nodes:
        g.add_node(str(node))

    edges = graph_json.get("edges", [])
    for edge in edges:
        if len(edge) >= 2:
            caller, callee = str(edge[0]), str(edge[1])
            g.add_edge(caller, callee)

    return g


def ensure_node_exists(g: nx.DiGraph, service: str) -> None:
    if service and not g.has_node(service):
        g.add_node(service)


def callers_of(g: nx.DiGraph, service: str) -> list[str]:
    """Direct callers of service (services with edges caller -> service)."""
    if not g.has_node(service):
        return []
    return list(g.predecessors(service))


def callees_of(g: nx.DiGraph, service: str) -> list[str]:
    """Direct callees of service (services that this service calls)."""
    if not g.has_node(service):
        return []
    return list(g.successors(service))


def upstream_dependents(g: nx.DiGraph, service: str) -> set[str]:
    """
    All services that directly or transitively depend on this service.
    Since an edge is (caller, callee), a caller depends on callee.
    Upstream dependents of callee S are all nodes that have a directed path to S (ancestors).
    If S degrades, all its upstream dependents are vulnerable to cascades.
    """
    if not g.has_node(service):
        return set()
    try:
        return set(nx.ancestors(g, service))
    except Exception:
        # Fallback BFS backward traversal handling cycles
        visited = set()
        queue = list(callers_of(g, service))
        while queue:
            curr = queue.pop(0)
            if curr not in visited and curr != service:
                visited.add(curr)
                queue.extend(callers_of(g, curr))
        return visited


def downstream_dependencies(g: nx.DiGraph, service: str) -> set[str]:
    """
    All services that this service depends on (directly or transitively).
    These are descendants in the (caller, callee) graph.
    """
    if not g.has_node(service):
        return set()
    try:
        return set(nx.descendants(g, service))
    except Exception:
        visited = set()
        queue = list(callees_of(g, service))
        while queue:
            curr = queue.pop(0)
            if curr not in visited and curr != service:
                visited.add(curr)
                queue.extend(callees_of(g, curr))
        return visited


def depth(g: nx.DiGraph, service: str) -> int:
    """
    Topological depth of a service from roots (entrypoint services with 0 callers).
    Root services have depth 0. Deeper services (like payment, db) have higher depth.
    """
    if not g.has_node(service):
        return 0

    roots = [n for n in g.nodes() if g.in_degree(n) == 0]
    if not roots:
        return 0

    max_dist = 0
    for root in roots:
        if root == service:
            continue
        try:
            if nx.has_path(g, root, service):
                d = nx.shortest_path_length(g, root, service)
                if d > max_dist:
                    max_dist = d
        except Exception:
            pass

    return max_dist
