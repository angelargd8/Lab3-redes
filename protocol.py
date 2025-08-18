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
    return msg


def dumps(msg: dict) -> str:
    return json.dumps(msg, ensure_ascii=False)

def loads(text: str):
    return json.loads(text)

#helpers

def hdr_get(msg, key, default=None):
    try:
        return msg["headers"][0].get(key, default)
    except Exception:
        return default

def hdr_set(msg, key, value):
    if not msg.get("headers"):
        msg["headers"] = [{}]
    msg["headers"][0][key] = value


def pack(obj) -> str:
    """Codifica objetos como string JSON en payload (tu payload es string)."""
    return json.dumps(obj, ensure_ascii=False)

def unpack(s, default=None):
    try:
        return json.loads(s)
    except Exception:
        return default
    
def new_id():
    return str(uuid.uuid4())