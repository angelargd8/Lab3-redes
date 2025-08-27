# Lab3-redes

Enlace al vídeo de como correrlo: https://youtu.be/-70DT0xZ5ss

crear el entorno:

```
python3 -m venv .venv
```

activarlo:

```
source .venv/bin/activate
```

instalar depedencias:

```
pip install slixmpp aiodns pycares redis
```

correr el archivo de redis:

```
python NodeRedis.py --id sec20.topologia2.nodo5 --neighbors sec20.topologia2.nodo2:1

```

```
python NodeRedis.py --id sec20.topologia2.nodo2 --neighbors sec20.topologia2.nodo5:1
```

correr el archivo:

```
python3 server.py
```

Crear nodos:
Nota: importante que primero este corriengo el server

```
python3 Node.py --jid A --neighbors B:1
```

```
python3 Node.py --jid B --neighbors A:1,C:2
```

```
python3 Node.py --jid C --neighbors B:2
```

Enviar mensajes:

```
send A hola desde C
```
