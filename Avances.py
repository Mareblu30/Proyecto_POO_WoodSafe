import hashlib
import datetime
from typing import List, Dict

class Nodo:
    def __init__(self, id: str, nickname: str, direccion_ip: str, puerto: int):
        self.id = id
        self.nickname = nickname
        self.direccion_ip = direccion_ip
        self.puerto = puerto

    def conectar_nodo(self, nodo: 'Nodo') -> None:
        print(f"Conectando con el nodo {nodo.nickname} ({nodo.direccion_ip}:{nodo.puerto})")

    def recibir_datos(self, datos: str) -> None:
        print(f"Datos recibidos: {datos}")

    def enviar_datos(self, datos: str, nodo: 'Nodo') -> None:
        print(f"Enviando datos a {nodo.nickname}: {datos}")

    def validar_nodo(self) -> bool:
        return bool(self.id and self.nickname and self.direccion_ip and self.puerto)

    def obtener_estado(self) -> str:
        return "Activo" if self.validar_nodo() else "Inactivo"


class Blockchain:
    def __init__(self):
        self.lista_bloques: List['Bloque'] = []

    def añadir_bloque(self, bloque: 'Bloque') -> None:
        self.lista_bloques.append(bloque)

    def validar_cadena(self) -> bool:
        for i in range(1, len(self.lista_bloques)):
            bloque_anterior = self.lista_bloques[i - 1]
            bloque_actual = self.lista_bloques[i]
            if bloque_actual.hash_anterior != bloque_anterior.calcular_hash():
                return False
        return True

    def revisar_integridad(self) -> bool:
        return self.validar_cadena()


class Bloque:
    def __init__(self, id: int, hash_anterior: str, datos: str, transacciones: List['Transaccion']):
        self.id = id
        self.hash_anterior = hash_anterior
        self.datos = datos
        self.transacciones = transacciones
        self.hash_actual = self.calcular_hash()

    def calcular_hash(self) -> str:
        contenido = f"{self.id}{self.hash_anterior}{self.datos}{[t.generar_hash() for t in self.transacciones]}"
        return hashlib.sha256(contenido.encode()).hexdigest()

    def verificar_integridad(self) -> bool:
        return self.hash_actual == self.calcular_hash()


class Transaccion:
    def __init__(self, id: int, datos: str, timestamp: datetime.datetime):
        self.id = id
        self.datos = datos
        self.timestamp = timestamp

    def generar_hash(self) -> str:
        contenido = f"{self.id}{self.datos}{self.timestamp.isoformat()}"
        return hashlib.sha256(contenido.encode()).hexdigest()

    def verificar_firma_digital(self) -> bool:
        # Simulación de verificación de firma
        return True


class Archivo:
    def __init__(self, nombre: str, tipo: str, contenido: bytes):
        self.nombre = nombre
        self.tipo = tipo
        self.contenido = contenido
        self.hash = self.calcular_hash()

    def calcular_hash(self) -> str:
        return hashlib.sha256(self.contenido).hexdigest()

    def obtener_metadatos(self) -> Dict[str, str]:
        return {"nombre": self.nombre, "tipo": self.tipo, "hash": self.hash}


class RedP2P:
    def __init__(self):
        self.nodos: List[Nodo] = []

    def registrar_nodo(self, nodo: Nodo) -> None:
        self.nodos.append(nodo)

    def obtener_nodos(self) -> List[Nodo]:
        return self.nodos

    def propagar_informacion(self, datos: str) -> None:
        for nodo in self.nodos:
            nodo.recibir_datos(datos)

    def desconectar_nodo(self, nodo: Nodo) -> None:
        self.nodos.remove(nodo)


class ProtocoloConsenso:
    def resolver_conflictos(self, nodos: List[Nodo]) -> Blockchain:
        # Implementación simulada del algoritmo de resolución de conflictos
        return Blockchain()

    def verificar_transaccion(self, transaccion: Transaccion) -> bool:
        return transaccion.verificar_firma_digital()

    def iniciar_proceso_consenso(self) -> None:
        print("Iniciando el proceso de consenso...")
        
