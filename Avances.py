import datetime
import hashlib
from typing import List, Dict

class Nodo:
    def __init__(self,id,nickname,direccion_ip,puerto):
        self.id = id
        self.nickname = nickname
        self.direccion_ip = direccion_ip
        self.puerto = puerto
        self.nodos_conectados = []

    def conectar_nodo(self, nodo):
        if nodo not in self.nodos_conectados:
            self.nodos_conectados.append(nodo)
            print(f"{self.nickname} conectado con {nodo.nickname} ({nodo.direccion_ip}:{nodo.puerto})")

    def recibir_datos(self, datos):
        print(f"{self.nickname} recibió datos: {datos}")

    def enviar_datos(self, datos, nodo):
        print(f"{self.nickname} envió datos a {nodo.nickname}: {datos}")
        nodo.recibir_datos(datos)

    def validar_nodo(self):
        return True  # Simulación de validación

    def obtener_estado(self):
        return "Activo" if self.validar_nodo() else "Inactivo"


class Blockchain:
    def __init__(self):
        self.lista_bloques = []

    def añadir_bloque(self, bloque):
        self.lista_bloques.append(bloque)
        print(f"Bloque añadido a la cadena: {bloque.id}")

    def validar_cadena(self):
        for i in range(1, len(self.lista_bloques)):
            if self.lista_bloques[i].hash_anterior != self.lista_bloques[i - 1].hash_actual:
                return False
        return True

    def revisar_integridad(self):
        return all(bloque.verificar_integridad() for bloque in self.lista_bloques)


class Bloque:
    def __init__(self,id,hash_anterior,datos,transacciones):
        self.id = id
        self.hash_anterior = hash_anterior
        self.datos = datos
        self.transacciones = transacciones
        self.hash_actual = self.calcular_hash()

    def calcular_hash(self):
        contenido = f"{self.id}{self.hash_anterior}{self.datos}{[t.datos for t in self.transacciones]}"
        return hashlib.sha256(contenido.encode()).hexdigest()

    def verificar_integridad(self):
        return self.calcular_hash() == self.hash_actual


class Transaccion:
    def __init__(self, id, datos, timestamp):
        self.id = id
        self.datos = datos
        self.timestamp = timestamp

    def generar_hash(self):
        contenido = f"{self.id}{self.datos}{self.timestamp}"
        return hashlib.sha256(contenido.encode()).hexdigest()

    def verificar_firma_digital(self):
        return True  # Simulación de verificación


class Archivo:
    def __init__(self, nombre, tipo, contenido):
        self.nombre = nombre
        self.tipo = tipo
        self.contenido = contenido
        self.hash = self.calcular_hash()

    def calcular_hash(self):
        return hashlib.sha256(self.contenido).hexdigest()

    def obtener_metadatos(self):
        return {"nombre": self.nombre, "tipo": self.tipo, "hash": self.hash}


class RedP2P:
    def __init__(self):
        self.nodos = []

    def registrar_nodo(self, nodo):
        self.nodos.append(nodo)
        print(f"Nodo registrado en la red: {nodo.nickname} ({nodo.direccion_ip}:{nodo.puerto})")

    def obtener_nodos(self):
        return self.nodos

    def propagar_informacion(self, datos):
        for nodo in self.nodos:
            nodo.recibir_datos(datos)

    def desconectar_nodo(self, nodo):
        self.nodos.remove(nodo)
        print(f"Nodo desconectado: {nodo.nickname}")


class ProtocoloConsenso:
    def resolver_conflictos(self, nodos):
        print("Resolviendo conflictos...")
        return Blockchain()

    def verificar_transaccion(self, transaccion):
        return True  # Simulación de verificación

    def iniciar_proceso_consenso(self):
        print("Iniciando el proceso de consenso...")


# Instanciación y ejecución
if __name__ == "__main__":
    # Crear nodos
    nodo1 = Nodo(id="Nodo1", nickname="Usuario1", direccion_ip="192.168.1.1", puerto=8001)
    nodo2 = Nodo(id="Nodo2", nickname="Usuario2", direccion_ip="192.168.1.2", puerto=8002)
    nodo3 = Nodo(id="Nodo3", nickname="Usuario3", direccion_ip="192.168.1.3", puerto=8003)
    nodo4 = Nodo(id="Nodo4", nickname="Usuario4", direccion_ip="192.168.1.4", puerto=8004)
    nodo5 = Nodo(id="Nodo5", nickname="Usuario5", direccion_ip="192.168.1.5", puerto=8005)

    # Conectar nodos
    nodo1.conectar_nodo(nodo2)
    nodo2.conectar_nodo(nodo3)
    nodo3.conectar_nodo(nodo4)
    nodo4.conectar_nodo(nodo5)
    nodo5.conectar_nodo(nodo1)

    # Crear una red P2P y registrar los nodos
    red = RedP2P()
    red.registrar_nodo(nodo1)
    red.registrar_nodo(nodo2)
    red.registrar_nodo(nodo3)
    red.registrar_nodo(nodo4)
    red.registrar_nodo(nodo5)

    # Crear una transacción
    transaccion = Transaccion(
        id=1,
        datos="Primera transacción",
        timestamp=datetime.datetime.now()
    )

    # Crear un bloque
    bloque = Bloque(
        id=1,
        hash_anterior="0" * 64,
        datos="Bloque génesis",
        transacciones=[transaccion]
    )

    # Crear blockchain y añadir el bloque
    blockchain = Blockchain()
    blockchain.añadir_bloque(bloque)

    # Validar la blockchain
    print(f"¿La blockchain es válida? {blockchain.validar_cadena()}")

    # Propagar información en la red
    red.propagar_informacion("Actualización de la red desde Nodo1")

    # Iniciar un protocolo de consenso
    protocolo = ProtocoloConsenso()
    protocolo.iniciar_proceso_consenso()
