import json
import uuid

from typing import Dict

# Mensaje cuando el <nodo 1> se presenta ante sus vecinos
def make_intro_msg(who_am_i: str, neighbours: Dict[str, int]) -> dict:
    return make_msg("init", {
        "whoAmI": who_am_i,
        "neighbours": neighbours
    })


# Mensaje enviado cuando el <nodo 1> necesita enviar un mensaje al <nodo 2>
def make_msg(type_: str, payload: dict, meta: dict | None = None) -> dict:
    out = {
        "type": type_,
        "payload": payload
    }
    if meta is not None:
        out["meta"] = meta
    return out

def make_user_message(origin: str, destination: str, ttl: int, content: str, msg_id: str | None = None) -> dict:
    if msg_id is None:
        msg_id = str(uuid.uuid4())
    payload = {
        "origin": origin,
        "destination": destination,
        "ttl": ttl,
        "content": content
    }
    meta = {
        "msg_id": msg_id,
        "path": [origin],
        "prev": None
    }
    return make_msg("message", payload, meta=meta)

# mensaje enviado cuando ya termino de calcular sus tablitas
def make_done_msg(who_am_i: str) -> dict:
    return make_msg(
        "done", {
            "whoAmI": who_am_i
        }
    )

def channel_name(node_id: str) -> str:
    # node_id = "sec20.topologia2.nodo9"
    return f"channel:{node_id}"

