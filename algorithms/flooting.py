# Flooding

# implementar algoritmos de enrutamiento y probarlo en una red simulada sobre un protocolo de capa superior

# lo que requiere el algoritmo de flooding es el conocimiento de sus vecinos

#este al igual que djstra usa LSR

#cada nodo pertenece a un usuario/recurso en la red

from base import Base

class Flooding(Base):
    name = "flooding"

    async def on_start(self):
        self.node.log("flooding listo")

    async def on_control(self, msg: dict, from_jid: str):
        #flooding no necesita de control plane
        pass


    async def route_data(self, msg: dict, from_jid: str):
        #enviar todos los vecinos excepto el que lo envio
        # return [jid for jid in self.node.get_neighbors(from_jid) if jid != from_jid]
        return [jid for jid in self.node.neighbors.keys() if jid != from_jid]