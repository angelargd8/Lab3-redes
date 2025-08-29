# Algorithms/LSR.py
from Algorithms.Base import Base
from Algorithms.Flooding import Flooding
from Algorithms.Djikstra import Dijkstra 

from typing import Dict, Set, List, Optional


class LSR(Base):
    name = "Link state routing"

    def __init__(self, *args, fallback_data_flood: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.seq_local: int = 0
        self.topology: Dict[str, Dict[str, float]] = {}   
        self.seen_lsa: Dict[str, int] = {}                
        self.fallback_data_flood = fallback_data_flood

        self.flood = Flooding(*args, **kwargs)
        self.flood.node = self.node

        self.dijkstra = Dijkstra(*args, **kwargs)
        self.dijkstra.node = self.node  

    async def on_start(self):
        self.node.log("[LSR] listo (control=flooding, datos=dijkstra)")
        self._update_own_links()
        await self._announce_own_lsa()
        self._run_dijkstra()

    async def on_control(self, msg: dict, from_jid: str):
        if not isinstance(msg, dict) or msg.get("type") != "LSA":
            self.node.log(f"[LSR] control desconocido de {from_jid}: {msg}")
            return

        origin = msg.get("origin")
        seq = msg.get("seq", -1)
        neighbors = msg.get("neighbors", {})

        if origin is None or not isinstance(neighbors, dict):
            self.node.log(f"[LSR] LSA mal formado de {from_jid}: {msg}")
            return

        if seq <= self.seen_lsa.get(origin, -1):
            return

        self.seen_lsa[origin] = seq
        self._apply_lsa(origin, neighbors)
        self._run_dijkstra()

        await self._flood_control(msg, exclude={from_jid})

    async def route_data(self, msg: dict, from_jid: str) -> List[str]:

        dst = (msg or {}).get("to")
        if not dst:
            return await self._maybe_fallback_data_flood(msg, from_jid)
        if dst == self.node.jid:
            return []

        self._update_own_links()
        self._run_dijkstra()

        hops: List[str] = []
        try:
            nh = self.dijkstra.next_hops(dst)
            hops = [h for h in nh if h != from_jid and h in self.node.neighbors]
        except Exception as e:
            self.node.log(f"[LSR] error next_hops Dijkstra: {e}")
            hops = []

        if hops:
            return hops

        return await self._maybe_fallback_data_flood(msg, from_jid)

    def _neighbor_costs_local(self) -> Dict[str, float]:
        costs = {}
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
        return costs

    def _update_own_links(self) -> None:
        self._apply_lsa(self.node.jid, self._neighbor_costs_local())

    def _apply_lsa(self, origin: str, neighbors: Dict[str, float]) -> None:
        self.topology.setdefault(origin, {})
        self.topology[origin] = {}
        for v, w in neighbors.items():
            try:
                w = float(w)
            except Exception:
                continue
            if w <= 0:
                continue
            self.topology[origin][v] = w
            self.topology.setdefault(v, {})
            if origin not in self.topology[v] or w < self.topology[v][origin]:
                self.topology[v][origin] = w

    async def _announce_own_lsa(self) -> None:
        self.seq_local += 1
        lsa = {
            "type": "LSA",
            "origin": self.node.jid,
            "seq": self.seq_local,
            "neighbors": self._neighbor_costs_local(),
        }
        self.seen_lsa[self.node.jid] = self.seq_local 
        await self._flood_control(lsa)

    async def _flood_control(self, msg: dict, exclude: Optional[Set[str]] = None) -> None:

        exclude = exclude or set()
        fake_from = next(iter(exclude)) if exclude else "__none__"
        targets = await self.flood.route_data(msg, fake_from)
        for nbr in targets:
            if nbr in exclude:
                continue
            try:
                await self.node.send_to_neighbor(nbr, msg)
            except Exception as e:
                self.node.log(f"[LSR] error al enviar LSA a {nbr}: {e}")

    async def _maybe_fallback_data_flood(self, msg: dict, from_jid: str) -> List[str]:
        return await self.flood.route_data(msg, from_jid) if self.fallback_data_flood else []

    def _run_dijkstra(self) -> None:

        try:
            if hasattr(self.dijkstra, "set_topology"):
                self.dijkstra.set_topology(self.topology)
            if hasattr(self.dijkstra, "compute"):
                self.dijkstra.compute(self.node.jid)
        except Exception as e:
            self.node.log(f"[LSR] Dijkstra falló: {e}")
