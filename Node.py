
import asyncio
import argparse
import sys
from typing import Dict, Set
from protocol import make_msg, loads, dumps
from Algorithms.Flooding import Flooding
from Algorithms.LSR import LSR
from Algorithms.Djikstra import Dijkstra
from Algorithms.DVR import DVR
import copy
import random


ALGORITHMS = {
    "flooding": Flooding,
    "link_state_routing": LSR,
    "dijkstra": Dijkstra,
    "distance_vector_routing": DVR

}

#convierte el valor de headers en un diccionario 
def _headers_dict_inplace(msg: dict) -> dict:
    h = msg.get("headers")
    if isinstance(h, list):
        h = h[0] if h else {}
        msg["headers"] = h
    elif h is None:
        h = {}
        msg["headers"] = h
    return h

class Node:
    def __init__(self, jid: str, neighbors: Dict[str, int], algo_name: str, host: str, port: int):
        self.jid = jid
        self.neighbors = neighbors  # Dict of JID to port
        # self.algo = ALGORITHMS[algo_name](self)
        if algo_name is None or algo_name == "random":
            
            algo_name = random.choice(list(ALGORITHMS.keys()))
        self.algo = ALGORITHMS[algo_name](self)
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.seen: Set[str] = set()


    #logts ss
    def log(self, *a):
        print(f"[{self.jid}] ", *a)
    
    #conectar el nodo al servidor
    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        reg = {"type": "REGISTER", "from": self.jid, "to": "server"}
        self.writer.write((dumps(reg) + "\n").encode())
        await self.writer.drain()
        await self.algo.on_start()

    
    async def _send_raw(self, msg: dict):
        # asume headers ya normalizados
        self.writer.write((dumps(msg) + "\n").encode())
        await self.writer.drain()

    #enviar al vecino
    async def send_to_neighbor(self, neighbor_jid: str, msg: dict):
        out = copy.deepcopy(msg)
        h = _headers_dict_inplace(out)
        h.setdefault("dst", msg.get("to"))  # conserva destino final si es DATA
        out["to"] = neighbor_jid
        out["headers"]["prev"] = self.jid
        # h["prev"] = self.jid
        await self._send_raw(out)

    #enviar la data
    async def send_data(self, to: str, payload: str, ttl: int = 8):
        msg = make_msg(proto="xmpp-sim", type="DATA",
                    from_addr=self.jid, to=to, ttl=ttl, payload=payload)
        h = _headers_dict_inplace(msg)
        h["path"] = [self.jid]
        h.setdefault("dst", to)
        self.log(f"envio data -> {to} ttl={ttl} id={msg['headers']['msg_id']}")
        for neighbor in self.neighbors:
            await self.send_to_neighbor(neighbor, msg)


    async def handle_data(self, msg: dict, from_jid: str):
        h = _headers_dict_inplace(msg)
        msg_id = h.get("msg_id")
        if msg_id in self.seen:
            return
        self.seen.add(msg_id)

        path = h.setdefault("path", [])
        path.append(self.jid)

        final_dst = h.get("dst") or msg.get("to")
        if final_dst == self.jid:
            self.log(f"RECIBIDO de {msg.get('from')} id={msg_id} via={from_jid} path={path} payload={msg.get('payload')}")
            return

        msg["ttl"] = int(msg.get("ttl", 0)) - 1
        if msg["ttl"] < 0:
            self.log(f"DESCARTADO id={msg_id} desde {from_jid} en {self.jid}: TTL agotado (path={path})")
            return

        next_hops = await self.algo.route_data(msg, from_jid)
        for nb in next_hops:
            await self.send_to_neighbor(nb, msg)


    async def handle_control(self, msg: dict, from_jid: str):
        await self.algo.on_control(msg, from_jid)

    
    async def receiver(self):
        while True:
            raw = await self.reader.readline()
            if not raw:
                break
            try:
                msg = loads(raw.decode().strip())
                _headers_dict_inplace(msg)
            except Exception:
                continue
            t = msg.get("type")
            from_jid = msg.get("headers", {}).get("via") or msg.get("headers", {}).get("prev") or msg.get("from")
            if t == "DATA":
                await self.handle_data(msg, from_jid)
            else:
                await self.handle_control(msg, from_jid)


    async def repl(self):
        loop = asyncio.get_running_loop()
        self.log("REPL: 'send <dest> <Mensaje...>' | 'neigh' | 'quit'")
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                await asyncio.sleep(0.05)
                continue
            line = line.strip()
            if line == "quit":
                break
            if line == "neigh":
                self.log(f"vecinos: {list(self.neighbors.keys())}")
                continue
            if line.startswith("send "):
                try:
                    _, dest, *txt = line.split()
                    text = " ".join(txt)
                    await self.send_data(dest, text)
                except ValueError:
                    self.log("uso: send <dest> <texto>")


    async def run(self):
        await self.connect()
        await asyncio.gather(self.receiver(), self.repl())


def parse_neighbors(s: str):

    if not s:
        return {}
    out = {}
    for token in s.split(','):
        token = token.strip()
        if not token:
            continue
        if ':' in token:
            jid, cost = token.split(':', 1)
            out[jid.strip()] = int(cost.strip())
        else:
            out[token] = 1
    return out


if __name__ == "__main__":
    ALGO_CHOICES = list(ALGORITHMS.keys())

    ap = argparse.ArgumentParser()
    ap.add_argument("--jid", required=True)
    ap.add_argument("--neighbors", default="", help="csv de JIDs vecinos")
    ap.add_argument("--algo", choices=ALGO_CHOICES, default=None, help="Algoritmo a usar; si se omite, se elige uno al azar.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()


    node = Node(args.jid, parse_neighbors(args.neighbors), args.algo, args.host, args.port)
    try:
        asyncio.run(node.run())
    except KeyboardInterrupt:
        pass