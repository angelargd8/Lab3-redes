import json
import uuid

def make_msg(*, proto, type, from_addr, to, ttl, headers=None, payload=None):
    msg = {
        "proto": proto,
        "type": type,
        "from": from_addr,
        "to": to,
        "ttl": ttl,
        "headers": headers or [{}],
        "payload": payload or ""
    }

    #asignar msg_id si falta
    msg.setdefault("headers", [{}])
    msg["headers"][0].setdefault("msg_id", str(uuid.uuid4()))
    return msg


def dumps(msg: dict) -> str:
    return json.dumps(msg, ensure_ascii=False)

def loads(text: str):
    return json.loads(text)
