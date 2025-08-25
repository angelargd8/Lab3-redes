# nodo con redis
"""
todos los mismos nodos sintonizan en un canal
los canales son independientes, al igual que los pub y los subs
el publisher es el que transmite algo por el canal, envia algo por un canal
los que sintonizan el radio son los subscribers, están suscritos a un canal
cada nodo es un grupo
cada nodo tiene un canal, a se debe de subribir a b y c
a consulta la tabla de ruteo
en vez de usar sockets, suscribirnos a los canales

Notas importantes:
- Cada nodo solo se suscribe a su propio canal y publica a los canales de los vecinos
- no recupera los mensajes previos
"""
import asyncio
import argparse
import sys
from typing import Dict, Set
from protocolRedis import *
# from Algorithms.Flooding import Flooding
from Algorithms.LSR import LSR
# from Algorithms.Djikstra import Dijkstra
# from Algorithms.DVR import DVR
import copy
import redis.asyncio as redis
import uuid
import json

#configuracion del redis
HOST = "lab3.redesuvg.cloud"
PORT = 6379
PWD = "UVGRedis2025"

ALGORITHMS = {
    # "flooding": Flooding,
    "link_state_routing": LSR,
    # "dijkstra": Dijkstra,
    # "distance_vector_routing": DVR,
}

"""
representa un nodo en la red, este se suscribe a su propio canal (receiver_loop)
publica mensajes a los canales de vecinos
interactúa con el algoritmo de ruteo
"""
class Node:
    #crea un nodo con el algoritmo de ruteo y los vecinos iniciales
    def __init__(self, node_id: str, neighbors: Dict[str, int], algo_name: str ="link_state_routing"):
        self.node_id = node_id
        self.neighbors = neighbors
        self.seen : Set[str] = set()


        AlgoCls = ALGORITHMS[algo_name]
        self.algo = AlgoCls(self)

        #redis 
        self.r = redis.Redis(host=HOST, port=PORT, password=PWD)
        self.pubsub = redis.client.PubSub | None = None #self.r.pubsub()

    def log(self, *a):
        print(f"[{self.node_id}] ", *a)

    #punto de entrada asincrono del nodo
    async def start(self):
        #suscribirse a mi canal
        self.pubsub = self.r.pubsub()
        await self.pubsub.subscribe(channel_name(self.node_id))

        #avisar a los vecinos hola con init
        intro = make_intro_msg(self.node_id, self.neighbors)
        await self.broadcast_to_neighbors(intro)

        #iniciar algoritmo
        await self.algo.on_start()

        #correr los loops
        await asyncio.gather(self.receiver_loop(), self.repl_loop())

    # Publica un mensaje a los vecinos
    async def broadcast_to_neighbors(self, msg: dict):
        payload = json.dumps(msg, ensure_ascii=False)
        for neighbor in self.neighbors.keys():
            await self.r.publish(channel_name(neighbor), payload)
            self.log(f"-> INIT/DONE publicado a  {neighbor}: {msg}")

    #reenvia un mensaje a un vecino ajustando meta.prev y extendido de meta.path
    async def send_to_neighbor(self, neighbor_id: str, msg: dict, prev: str | None):
        
        out = copy.deepcopy(msg)

        #garantizar meta
        out.setdefault("meta", {})
        out["meta"].setdefault("msg_id", str(uuid.uuid4()))
        out["meta"].setdefault("path", [])
        out["meta"]["prev"] = prev

        #si es message anexar path
        if out.get("type") == "message":
            out["meta"]["path"].append(self.node_id)

        await self.r.publish(channel_name(neighbor_id), json.dumps(out, ensure_ascii=False))
        self.log(f"-> reenviado a {neighbor_id} msg_id={out['meta']['msg_id']}")
    

    #genera y difunde un mensaje de un usuario a un destino logico
    async def send_user_message(self, destination: str, content: str, ttl: int = 8):
        msg = make_user_message(origin = self.node_id, destination= destination, ttl=ttl, content=content)
        msg_id = msg["meta"]["msg_id"]
        self.log(f"Envío DATA -> {destination} ttl={ttl} id={msg_id}")

        #primera salida 
        next_hops = await self.algo.route_data(msg, from_node=self.id)
        for nb in next_hops:
            await self.send_to_neighbor(nb, msg, prev=self.id)


    # Maneja un mensaje de inicialización
    async def handle_init(self, msg: dict, from_node: str):
        self.log(f"INIT de {from_node}: vecinos={msg['payload'].get('neighbours', {})}")
        await self.algo.on_control(msg, from_node)
    
    #si ya termino de calcular sus tablitas, enviar done
    async def handle_done(self, msg: dict, from_node: str):
        self.log(f"DONE de {from_node}")
        await self.algo.on_control(msg, from_node)

    # Maneja un mensaje de usuario
    async def handle_message(self, msg: dict, from_node: str):
        meta = msg.setdefault("meta", {})
        msg_id= meta.setdefault("msg_id", str(uuid.uuid4()))
        if msg_id in self.seen:
            return
        self.seen.add(msg_id)

        #TTL
        payload = msg["payload"]
        ttl = int(payload.get("ttl", 0))

        dest = payload.get("destination")
        origin = payload.get("origin")
        content = payload.get("content")

        #actualizar path/prev
        meta.setdefault("path", [])
        meta["path"].append(self.node_id)
        meta["prev"] = from_node

        #verificar si llego
        if dest == self.node_id:
            self.log(f"RECIBIDO de {origin} id={msg_id} via={from_node} path={meta['path']} payload={content}")
            return
        
        #decrementar ttl y descartar si expira
        ttl -= 1
        if ttl < 0:
            self.log(f"DESCARTADO de {origin} id={msg_id} via={from_node} path={meta['path']} payload={content} (TTL expirado)")
            return
        payload["ttl"] = ttl

        #reenviar
        next_hops = await self.algo.route_data(msg, from_node=from_node)
        for nb in next_hops:
            await self.send_to_neighbor(nb, msg, prev=from_node)

    # aqui deberia de ser el bucle principal de recepcion
    # debe de leer los mensaje del canal propio via pub/sub
    # decodifica el json y lo procesa por type: init|done|message
    async def receiver_loop(self):
        pass

    #repl asincronica para pruebas
    #poner los comandos
    #como los argumentos xd
    async def repl_loop(self):
        pass


# lo mismo que node, alguien hagale ctrl+c y ctrl+v jaja
def parse_neighbors(s: str) -> Dict[str, int]:
    """
    'sec20.topologia2.nodo6:3,sec20.topologia2.nodo7:1'
    """
    pass

#logica del main xd
async def main():
    pass


if __name__ == "__main__":
    print("Starting Redis-PubSub node…")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
