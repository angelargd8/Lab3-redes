import asyncio
from protocol import loads, dumps


CLIENTS = {} # jid -> (reader, writer)

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


# manejar la conexion del cliente
async def handle_client(reader: asyncio.StreamReader, writer:asyncio.StreamWriter ):

    peer = writer.get_extra_info('peername')
    jid = None
    try:
        while True:
            raw = await reader.readline()
            if not raw:
                break
            try:
                msg = loads(raw.decode().strip())
            except Exception:
                continue

            if msg.get("type") == "REGISTER":
                jid = msg.get("from")
                CLIENTS[jid] = (reader, writer)
                print(f"[SERVER] {jid} registrado desde {peer}")
                continue

            # mandar cualquier cosa con un 'to'
            target = msg.get("to")
            if target in CLIENTS:
                # anotar el ultimo paso del receptor
                msg.setdefault("headers", {})
                msg = loads(raw.decode().strip())
                h = _headers_dict_inplace(msg)
                h["via"] = jid # quien envio esto
                out = dumps(msg) + "\n"
                _, t_writer = CLIENTS[target]
                t_writer.write(out.encode())
                await t_writer.drain()
            else:
                # destino no disponible
                pass
    except Exception as e:
        print(f"[SERVER] error con {jid or peer}: {e}")
    finally:
        if jid and CLIENTS.get(jid, (None, None))[1] is writer:
            CLIENTS.pop(jid, None)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        print(f"[SERVER] desconectado: {jid or peer}")


async def main(host= '127.0.0.1', port= 8765):
    server = await asyncio.start_server(handle_client, host, port)
    addr = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"[SERVER] escuchando en {addr}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[SERVER] chao")