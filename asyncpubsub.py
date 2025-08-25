import asyncio
import redis.asyncio as redis

STOPWORD = "STOP"

'''
    Algoritmos a probar:

        1. Flooding: no es necesario conocer la topologia, solo los vecinos directos
        2. Link State Routing: intercambio previo de mensajes HELLO con los costos de los vecinos

    La definicion de los canales de los nodos debe seguir este formato:
    OFICIAL = SECCION.TOPOLOGIA.NODO
    PRUEBA = SECCION.TOPOLOGIA.NODO.PRUEBA

    sec20.topologia1.nodo1.prueba1
    sec20.topologia1.nodo1.prueba2
    sec20.topologia1.nodo1.prueba3
    sec20.topologia1.nodo1.prueba4
    sec20.topologia1.nodo1.prueba5

    sec20.topologia1.nodo1
    sec20.topologia1.nodo2
    sec20.topologia1.nodo3
    sec20.topologia1.nodo4
    sec20.topologia1.nodo5

    sec20.topologia2.nodo6
    sec20.topologia2.nodo7
    sec20.topologia2.nodo8
    sec20.topologia2.nodo9
    sec20.topologia2.nodo10
'''


async def reader(channel: redis.client.PubSub):
    while True:
        message = await channel.get_message(ignore_subscribe_messages=True, timeout=None)
        if message is not None:
            print(f"(Reader) Message Received: {message}")
            if message["data"].decode() == STOPWORD:
                print("(Reader) STOP")
                break

HOST = "lab3.redesuvg.cloud"
PORT = 6379
PWD = "UVGRedis2025"

async def main():
    """The main asynchronous function."""
    r = redis.Redis(host=HOST, port=PORT, password=PWD)
    async with r.pubsub() as pubsub:
        await pubsub.subscribe("channel:canal1")

        message = input("Enter the message to send to node B \n")
        await r.publish("channel:nodeB", message)

if __name__ == "__main__":
    print("Starting asyncio and redis test...")
    print("This is node A")
    asyncio.run(main())
    print("DONE!")