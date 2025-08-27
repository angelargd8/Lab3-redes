import uuid
from typing import Dict, Any

def make_base_msg(type_: str, from_: str, to: str, ttl: int, headers: list[str], payload: Any) -> dict:
    return {
        "proto": "lsr",
        "type": type_,
        "from": from_,
        "to": to,
        "ttl": ttl,
        "headers": headers,
        "payload": payload
    }

# HELLO -> equivalente a "init"
def make_hello_msg(who_am_i: str, ttl: int = 5) -> dict:
    return make_base_msg(
        "hello",
        from_=who_am_i,
        to="broadcast",
        ttl=ttl,
        headers=[],
        payload=""  # opcional: vecinos iniciales si quieres
    )

# INFO -> equivalente a "done"/tablas
def make_info_msg(who_am_i: str, routing_table: Dict[str, int], headers: list[str] | None = None, ttl: int = 5) -> dict:
    if headers is None:
        headers = []
    return make_base_msg(
        "info",
        from_=who_am_i,
        to="broadcast",
        ttl=ttl,
        headers=headers,
        payload=routing_table
    )

# MESSAGE -> equivalente a "message" de usuario
def make_message(origin: str, destination: str, content: str, headers: list[str] | None = None,
                 ttl: int = 5, msg_id: str | None = None) -> dict:
    if headers is None:
        headers = []
    if msg_id is None:
        msg_id = str(uuid.uuid4())
    return make_base_msg(
        "message",
        from_=origin,
        to=destination,
        ttl=ttl,
        headers=headers,
        payload={"msg_id": msg_id, "content": content}
    )

def channel_name(node_id: str) -> str:
    return f"channel:{node_id}"
