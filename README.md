# Lab3-redes

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
pip install slixmpp aiodns pycares 
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
