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
from redis.asyncio.client import PubSub
import uuid
import json

from Algorithms.Flooding import Flooding

#configuracion del redis
HOST = "lab3.redesuvg.cloud"
PORT = 6379
PWD = "UVGRedis2025"

ALGORITHMS = {
    "flooding": Flooding,
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
    def __init__(self, node_id: str, neighbors: Dict[str, int], algo_name: str ="flooding"):
        self.node_id = node_id
        self.neighbors = neighbors
        self.seen : Set[str] = set()
        self.jid = node_id


        AlgoCls = ALGORITHMS[algo_name]
        self.algo = AlgoCls(self)

        #redis 
        self.r = redis.Redis(host=HOST, port=PORT, password=PWD)
        self.pubsub: PubSub | None = None   

    def log(self, *a):
        print(f"[{self.node_id}] ", *a)

    #punto de entrada asincrono del nodo
    async def start(self):
        self.pubsub = self.r.pubsub()
        await self.pubsub.subscribe(channel_name(self.node_id))

        # Enviar HELLO al inicio
        hello = make_hello_msg(self.node_id)
        await self.broadcast_to_neighbors(hello)

        await self.algo.on_start()
        await asyncio.gather(self.receiver_loop(), self.repl_loop())


    # Publica un mensaje a los vecinos
    async def broadcast_to_neighbors(self, msg: dict):
        payload = json.dumps(msg, ensure_ascii=False)
        for neighbor in self.neighbors.keys():
            await self.r.publish(channel_name(neighbor), payload)
            self.log(f"-> INIT/DONE publicado a  {neighbor}: {msg}")

    #reenvia un mensaje a un vecino ajustando meta.prev y extendido de meta.path
    async def send_to_neighbor(self, neighbor_id: str, msg: dict):
        out = copy.deepcopy(msg)

        # actualizar headers (detección de ciclos)
        out["headers"].append(self.node_id)
        if len(out["headers"]) > 3:
            out["headers"] = out["headers"][-3:]

        # reducir TTL
        out["ttl"] -= 1
        if out["ttl"] <= 0:
            self.log(f"Descartado TTL=0 {out}")
            return

        await self.r.publish(channel_name(neighbor_id), json.dumps(out, ensure_ascii=False))
        self.log(f"-> reenviado a {neighbor_id} {out}")

    

    #genera y difunde un mensaje de un usuario a un destino logico
    async def send_user_message(self, destination: str, content: str, ttl: int = 8):
        msg = make_message(
            origin=self.node_id,
            destination=destination,
            content=content,
            ttl=ttl,
            headers=[]
        )
        # primera salida usando el algoritmo
        next_hops = await self.algo.route_data(msg, self.node_id)
        print(next_hops)
        for nb in next_hops:
            await self.send_to_neighbor(nb, msg)



    # Maneja un mensaje de inicialización (HOLA!)
    async def handle_init(self, msg: dict, from_node: str):
        self.log(f"HELLO de {from_node}")
        await self.algo.on_control(msg, from_node)

    async def handle_info(self, msg: dict, from_node: str):
        self.log(f"INFO de {from_node} tabla={msg['payload']}")
        await self.algo.on_control(msg, from_node)

    async def forward_message(self, msg: dict, from_node: str):
        next_hops = await self.algo.route_data(msg, self.jid)
        for nb in next_hops:
            if nb == from_node:
                continue
            await self.send_to_neighbor(nb, msg)


    async def handle_message(self, msg: dict, from_node: str):
        self.log(f"MENSAJE de {from_node} payload={msg['payload']}")
        print()
        msg_id = msg["payload"]

        dest = msg["to"]
        origin = msg["from"]
        content = msg["payload"]

        if dest == self.node_id:
            self.log(f"RECIBIDO de {origin} id={msg_id} via={from_node} headers={msg['headers']} payload={content}")
            return

        await self.forward_message(msg, from_node)


    # aqui deberia de ser el bucle principal de recepcion
    # debe de leer los mensaje del canal propio via pub/sub
    # decodifica el json y lo procesa por type: init|done|message
    async def receiver_loop(self):
        self.log("Esperando mensajes en canal propio...")
        async for raw in self.pubsub.listen():
            if raw is None:
                continue
            if raw["type"] != "message":
                continue

            try:
                msg = json.loads(raw["data"])
            except Exception as e:
                self.log(f"Error decodificando JSON: {e}, raw={raw}")
                continue

            mtype = msg.get("type")
            from_node = msg.get("from", "?")

            if mtype == "hello":
                await self.handle_init(msg, from_node)
            elif mtype == "info":
                await self.handle_info(msg, from_node)
            elif mtype == "message":
                await self.handle_message(msg, from_node)
            else:
                self.log(f"Mensaje desconocido {msg}")

    #repl asincronica para pruebas
    #poner los comandos
    #como los argumentos xd
    async def repl_loop(self):
        loop = asyncio.get_event_loop()
        while True:
            # input en hilo separado para no bloquear asyncio
            cmdline = await loop.run_in_executor(None, sys.stdin.readline)
            if not cmdline:
                continue
            cmdline = cmdline.strip()

            if not cmdline:
                continue

            parts = cmdline.split()
            cmd = parts[0].lower()

            if cmd in ("quit", "exit"):
                self.log("Saliendo...")
                break

            elif cmd == "send":
                # uso: send <destino> <mensaje>
                if len(parts) < 3:
                    self.log("Uso: send <destino> <mensaje>")
                    continue
                dest = parts[1]
                content = " ".join(parts[2:])
                await self.send_user_message(dest, content)

            elif cmd == "neighbors":
                self.log(f"Vecinos: {self.neighbors}")

            elif cmd == "seen":
                self.log(f"Mensajes vistos: {len(self.seen)} ids")

            else:
                self.log(f"Comando desconocido: {cmd}")


# formato de los neighbors en diccionario
def parse_neighbors(s: str) -> Dict[str, int]:
    """
    'sec20.topologia2.nodo6:3,sec20.topologia2.nodo7:1'
    """
    neighbors: Dict[str, int] = {}
    if not s.strip():
        return neighbors

    parts = s.split(",")
    for part in parts:
        if not part.strip():
            continue
        try:
            node_id, cost = part.split(":")
            neighbors[node_id.strip()] = int(cost.strip())
        except ValueError:
            raise ValueError(f"Formato inválido en vecinos: '{part}', se esperaba nodo:coste")
    return neighbors


async def main():
    parser = argparse.ArgumentParser(description="Redis-PubSub Node")
    parser.add_argument("--id", required=True, help="ID del nodo (ej. sec20.topologia2.nodo1)")
    parser.add_argument("--neighbors", default="", help="Lista de vecinos con costo (ej. sec20.topologia2.nodo6:3,sec20.topologia2.nodo7:1)")
    parser.add_argument("--algo", default="link_state_routing", choices=ALGORITHMS.keys(), help="Algoritmo de ruteo")

    args = parser.parse_args()

    neighbors = parse_neighbors(args.neighbors)

    print(f"[BOOT] Nodo {args.id} iniciado con vecinos={neighbors} usando algoritmo={args.algo}")

    node = Node(node_id=args.id, neighbors=neighbors, algo_name=args.algo)

    await node.start()


if __name__ == "__main__":
    print("Starting Redis-PubSub node…")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
