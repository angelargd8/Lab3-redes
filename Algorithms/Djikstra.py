# Algorithms/Dijkstra.py
from Algorithms.Base import Base
import heapq
from typing import Dict, Set, List


class Dijkstra(Base):

    name = "dijkstra"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.topology: Dict[str, Dict[str, float]] = {}
        self.dist: Dict[str, float] = {}
        self.first_hops: Dict[str, Set[str]] = {}

    async def on_start(self):
        self.node.log("[Dijkstra] listo")
        self._seed_local()
        self.compute(self.node.jid)

    async def on_control(self, msg: dict, from_jid: str):
        if isinstance(msg, dict) and msg.get("type") == "TOPO":
            topo = msg.get("topology", {})
            if isinstance(topo, dict):
                self.set_topology(topo)
                self.compute(self.node.jid)

    async def route_data(self, msg: dict, from_jid: str) -> List[str]:
        h = (msg or {}).get("headers", {}) or {}
        dst = h.get("dst") or msg.get("to")

        if not dst or dst == self.node.jid:
            return []

        self.compute(self.node.jid)

        hops = [h for h in self.next_hops(dst) if h != from_jid]
        return hops

    def set_topology(self, topo: Dict[str, Dict[str, float]]) -> None:
        
        clean: Dict[str, Dict[str, float]] = {}
        for u, adj in (topo or {}).items():
            if not isinstance(adj, dict):
                continue
            cu = clean.setdefault(u, {})
            for v, w in adj.items():
                try:
                    w = float(w)
                except Exception:
                    continue
                if w > 0:
                    cu[v] = w
        self.topology = clean

    def compute(self, src: str) -> None:

        if src not in self.topology:
            self.topology.setdefault(src, {})

        dist: Dict[str, float] = {src: 0.0}
        first_hops: Dict[str, Set[str]] = {src: set()}
        visited: Set[str] = set()
        pq: List[tuple] = [(0.0, src)]

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)

            for v, w in self.topology.get(u, {}).items():
                nd = d + float(w)
                if v not in dist or nd < dist[v] - 1e-12:
                    dist[v] = nd
                    first_hops[v] = {v} if u == src else set(first_hops.get(u, {u}))
                    heapq.heappush(pq, (nd, v))
                elif v in dist and abs(nd - dist[v]) <= 1e-12:
                    extra = {v} if u == src else set(first_hops.get(u, {u}))
                    cur = first_hops.get(v, set())
                    merged = cur.union(extra)
                    if merged != cur:
                        first_hops[v] = merged

        self.dist = dist
        self.first_hops = first_hops

    def next_hops(self, dst: str) -> List[str]:

        hops = set(self.first_hops.get(dst, set()))
        if hasattr(self, "node") and self.node is not None:
            hops = {h for h in hops if h in self.node.neighbors}
        return sorted(hops)

    def _seed_local(self) -> None:

        if not hasattr(self, "node") or self.node is None:
            return
        src = self.node.jid
        costs: Dict[str, float] = {}
        for jid, info in self.node.neighbors.items():
            if isinstance(info, (int, float)):
                costs[jid] = float(info)
            elif isinstance(info, dict) and "cost" in info:
                try:
                    costs[jid] = float(info["cost"])
                except Exception:
                    costs[jid] = 1.0
            else:
                costs[jid] = 1.0

        if costs:
            self.topology.setdefault(src, {})
            self.topology[src].update(costs)
            for v, w in costs.items():
                self.topology.setdefault(v, {})
                if src not in self.topology[v] or w < self.topology[v][src]:
                    self.topology[v][src] = w
