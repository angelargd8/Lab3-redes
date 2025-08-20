from typing import Dict, List, Optional

class Base:
    name = "Base"

    def __init__(self, node):
        self.node = node


    #tareas periodicas, anuncioss
    async def on_start(self):
        pass

    async def on_control(self, msg: dict, from_jid: str):
        """Procesa mensajes no-data (hello, lsa, dv…)."""
        pass

    async def route_data(self, msg: dict, from_jid: str) -> List[str]:
        """Devuelve la lista de JIDs a los que reenviar un DATA."""
        return []