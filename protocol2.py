import json
import uuid

# Mensaje cuando el <nodo 1> se presenta ante sus vecinos
#aun falta poner sus vecions xd, pero puse lo que habia en el formato xd
def make_intro_msg():
    return make_msg("init", {
        "whoAmI": uuid.uuid4().hex,
        "neighbours": {
            uuid.uuid4().hex: 5,
            uuid.uuid4().hex: 10
        }
    })

# Mensaje enviado cuando el <nodo 1> necesita enviar un mensaje al <nodo 2>
def make_msg(type, payload):
    return {
        "type": type,
        "payload": payload
    }

# mensaje enviado cuando ya termino de calcular sus tablitas
def make_done_msg():
    return make_msg(
        "done", {
            "whoAmI": uuid.uuid4().hex
        }
    )