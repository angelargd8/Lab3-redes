
import asyncio
from typing import Dict
from slixmpp import ClientXMPP
from protocol import make_msg, loads, dumps, new_id, hdr_get, hdr_set
from algorithms import get_algo


class RoutingNode(ClientXMPP):
    def __init__(self, jid: str, password: str, node_id, proto, type, from_addr, to, ttl, headers, payload):
        super().__init__(jid, password)
        self.jid = jid
        self.node_id = node_id
        
        self.proto = proto
        self.type = type
        self.from_addr = from_addr
        self.to = to
        self.ttl = ttl
        self.headers = headers
        self.payload = payload
        

        self.seen = set()

        #pluggins

        self.register_plugin('xep_0030')
        self.register_plugin('xep_0199')

        #handler
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.on_message)

        #cargar el algoritmo
        Algoritm = get_algo(self.proto)
        self.proto = Algoritm(self)


    #utils
    async def send_msg(self, msg: dict):
        self.send_message(mto=msg["to"], mtype="chat", mbody=dumps(msg))

    def jid_for(self, neighbor_id: str):
        for jid, nid in self.neighbors.items():
            if nid == neighbor_id:
                return jid
        return None

    def log(self, *args):
        print(f"[{self.node_id}|{self.algo_name}]", *args)

    def new_msg_id(self):
        return new_id()
    

    def forward(self, msg: dict, to_jid: str):
        """Clona un mensaje para reenvío, bajando TTL y subiendo hop."""
        fwd = dict(msg)  # copia superficial
        fwd["to"] = to_jid
        fwd["from"] = self.jid
        fwd["ttl"] = int(msg.get("ttl", self.ttl)) - 1
        hop = int(hdr_get(fwd, "hop", 0)) + 1
        hdr_set(fwd, "hop", hop)
        return fwd
    
