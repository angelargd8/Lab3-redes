from Algorithms.Base import Base
from protocol import make_msg
from typing import Dict, List
import math

class DVR(Base):
    name = "distance_vector"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.routing_table: Dict[str, Dict[str, float]] = {}
        self.distance_vector: Dict[str, float] = {}

    async def on_start(self):
        self.node.log("[DVR] listo")
        self._init_table()
        await self._send_vector()

    def _init_table(self):
        self.routing_table[self.node.jid] = {"cost": 0, "next_hop": self.node.jid}
        for nb, cost in self.node.neighbors.items():
            self.routing_table[nb] = {"cost": float(cost), "next_hop": nb}
        self._update_distance_vector()

    def _update_distance_vector(self):
        self.distance_vector = {dst: info["cost"] for dst, info in self.routing_table.items()}

    async def _send_vector(self):
        """Envía el vector de distancias a todos los vecinos"""
        msg = make_msg(
            proto="dvr",
            type="DV",
            from_addr=self.node.jid,
            to="",
            ttl=8,
            payload=self.distance_vector
        )
        for nb in self.node.neighbors.keys():
            out = dict(msg)
            out["to"] = nb
            await self.node.send_to_neighbor(nb, out)

    async def on_control(self, msg: dict, from_jid: str):
        if msg.get("type") != "DV":
            return
        vector = msg.get("payload", {})
        updated = False

        # Bellman-Ford
        cost_to_nb = self.node.neighbors.get(from_jid, math.inf)
        for dst, nb_cost in vector.items():
            new_cost = cost_to_nb + float(nb_cost)
            if dst not in self.routing_table or new_cost < self.routing_table[dst]["cost"]:
                self.routing_table[dst] = {"cost": new_cost, "next_hop": from_jid}
                updated = True

        if updated:
            self._update_distance_vector()
            await self._send_vector()

    async def route_data(self, msg: dict, from_jid: str) -> List[str]:
        dst = (msg.get("headers") or {}).get("dst") or msg.get("to")
        if not dst or dst == self.node.jid:
            return []
        if dst not in self.routing_table:
            return []  # no sabemos a dónde
        next_hop = self.routing_table[dst]["next_hop"]
        return [next_hop] if next_hop != from_jid else []
