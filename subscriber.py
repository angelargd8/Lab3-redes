#aqui escuchamos

import asyncio
import redis.asyncio as redis

STOPWORD = "STOP"


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
        #solo me suscribo al de mi nodo
        await pubsub.subscribe("channel:sec20.topologia2.nodo9.prueba")

        future = asyncio.create_task(reader(pubsub))
        await future

if __name__ == "__main__":
    print("Starting asyncio and redis test...")
    print("This is node sec20.topologia2.nodo9.prueba")
    asyncio.run(main())
    print("DONE!")