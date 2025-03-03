import hashlib
import json
import time
import threading
import socket
import os
from flask import Flask, render_template, request, jsonify

# Clase para representar una transacción
class Transaction:
    def __init__(self, sender, receiver, amount, file_hash=None, timestamp=None):  # Cambio aquí
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.file_hash = file_hash
        self.timestamp = timestamp if timestamp is not None else time.time()  # Nueva lógica

    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "file_hash": self.file_hash,
            "timestamp": self.timestamp  # Asegurar que se incluya
        }

# Clase para representar un bloque
class Block:
    def __init__(self, index, previous_hash, transactions, nonce=0, timestamp=None):  # Cambio aquí
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp is not None else time.time()  # Nueva línea
        self.transactions = transactions
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def mine_block(self, difficulty):
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Bloque minado: {self.hash}")

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "hash": self.hash
        }

# Clase para representar la blockchain
class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 4
        self.mining_reward = 10
        self.mining_lock = threading.Lock()

    def create_genesis_block(self):
        return Block(0, "0", [])

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, transaction):
        if transaction not in self.pending_transactions:
            self.pending_transactions.append(transaction)   

    def mine_pending_transactions(self, miner_address):
        with self.mining_lock:
            if not self.pending_transactions:
                return

            block = Block(len(self.chain), self.get_last_block().hash, self.pending_transactions.copy())
            block.mine_block(self.difficulty)
            self.chain.append(block)
            self.pending_transactions = [Transaction("SYSTEM", miner_address, self.mining_reward)]

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

# Clase para representar un nodo P2P
class P2PNode:
    nodes = {}

    def __init__(self, node_id, port):
        self.node_id = node_id
        self.port = port
        self.peers = {}
        self.files = {}
        self.blockchain = Blockchain()
        self.storage_dir = f"node_{node_id}_files"
        os.makedirs(self.storage_dir, exist_ok=True)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("127.0.0.1", self.port))
        self.server.listen(5)
        P2PNode.nodes[node_id] = self
        self.connect_to_network()
        self.sync_with_network()
        print(f"Nodo {node_id} creado en puerto {port}")
        print(f"Directorio de almacenamiento: {self.storage_dir}")

        threading.Thread(target=self.start_server, daemon=True).start()

    def sync_with_network(self):
        """Sincroniza con la blockchain más larga al iniciar"""
        if len(P2PNode.nodes) > 1:
            longest_chain = []
            for node in P2PNode.nodes.values():
                if len(node.blockchain.chain) > len(longest_chain):
                    longest_chain = node.blockchain.chain
            if longest_chain:
                self.receive_blockchain([block.to_dict() for block in longest_chain])

    def connect_to_network(self):
        for node_id, node in P2PNode.nodes.items():
            if node_id != self.node_id:
                self.peers[node_id] = node.port
                node.peers[self.node_id] = self.port
        print(f"🔗 Nodo {self.node_id} conectado a {len(self.peers)} peers")

    def start_server(self):
        print(f"[Nodo {self.node_id}] Servidor iniciado en puerto {self.port}")
        while True:
            client_socket, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()

    def handle_client(self, client_socket, addr):
        print(f"[Nodo {self.node_id}] Conectado con {addr}")
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                return

            command, *args = data.split("::")
            if command == "REQUEST_FILE":
                requested_hash = args[0]
                if requested_hash in self.files:
                    filepath = self.files[requested_hash]
                    if os.path.exists(filepath):
                        self.send_file(client_socket, requested_hash)
                    else:
                        client_socket.sendall("FILE_NOT_FOUND".encode())
                else:
                    client_socket.sendall("FILE_NOT_FOUND".encode())
        except Exception as e:
            print(f"[Nodo {self.node_id}] Error en handle_client: {e}")
        finally:
            client_socket.close()

    def send_file(self, client_socket, file_hash):
        filepath = self.files[file_hash]
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        header = f"FILE::{filename}::{filesize}::{file_hash}"
        client_socket.sendall(header.encode())

        confirmation = client_socket.recv(1024).decode()
        if confirmation != "READY":
            return

        with open(filepath, "rb") as f:
            while chunk := f.read(4096):
                client_socket.sendall(chunk)

    def propagate_transactions(self):
        chain_data = [block.to_dict() for block in self.blockchain.chain]
        for peer_id in self.peers:
            if peer_id in P2PNode.nodes:
                peer_node = P2PNode.nodes[peer_id]
                try:
                    peer_node.receive_blockchain(chain_data)
                except Exception as e:
                    print(f"Error propagando a {peer_id}: {str(e)}")

    def propagate_blockchain(self):
        print(f"🔄 Propagando blockchain desde {self.node_id}")
        chain_data = [block.to_dict() for block in self.blockchain.chain]
        
        for peer_id in self.peers:
            if peer_id in P2PNode.nodes:
                peer_node = P2PNode.nodes[peer_id]
                print(f"📤 Enviando blockchain a {peer_id}")
                try:
                    peer_node.receive_blockchain(chain_data)
                except Exception as e:
                    print(f"Error propagando a {peer_id}: {str(e)}")

    def upload_file(self, filepath):
        if not os.path.exists(filepath):
            return None

        file_hash = self.hash_file(filepath)
        if file_hash in self.files:
            return file_hash

        # Copiar archivo al nodo
        dest_path = os.path.join(self.storage_dir, os.path.basename(filepath))
        with open(filepath, "rb") as src_file, open(dest_path, "wb") as dest_file:
            dest_file.write(src_file.read())

        self.files[file_hash] = dest_path

        # Crear transacción y minar bloque
        transaction = Transaction(self.node_id, "NETWORK", 1, file_hash)
        self.blockchain.pending_transactions = [
            tx for tx in self.blockchain.pending_transactions 
            if tx.sender != "SYSTEM"
        ]
        self.blockchain.add_transaction(transaction)
        self.blockchain.mine_pending_transactions(self.node_id)
        time.sleep(1)  # Esperar 1 segundo para sincronizar
        # Propagar blockchain y transacciones pendientes
        self.propagate_blockchain()
        self.propagate_pending_transactions()  # Nuevo método para propagar transacciones

        return file_hash

    def propagate_pending_transactions(self):
        """Envía transacciones pendientes a todos los peers"""
        transactions_data = [tx.to_dict() for tx in self.blockchain.pending_transactions]
        for peer_id in self.peers:
            if peer_id in P2PNode.nodes:
                peer_node = P2PNode.nodes[peer_id]
                peer_node.receive_pending_transactions(transactions_data)

    def receive_pending_transactions(self, transactions_data):
        """Agrega transacciones recibidas a las pendientes"""
        for tx_data in transactions_data:
            tx = Transaction(
                tx_data["sender"],
                tx_data["receiver"],
                tx_data["amount"],
                tx_data.get("file_hash")
            )
            if tx not in self.blockchain.pending_transactions:
                self.blockchain.pending_transactions.append(tx)

    def request_file(self, peer_id, file_hash):
        if peer_id not in self.peers:
            print(f"[Nodo {self.node_id}] Error: Peer {peer_id} no encontrado en la lista de peers: {self.peers}")
            return False
        if file_hash in self.files:
            print(f"[Nodo {self.node_id}] El archivo con hash {file_hash} ya existe en este nodo.")
            return False

        peer_port = self.peers[peer_id]
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            print(f"[Nodo {self.node_id}] Conectando con peer {peer_id} en puerto {peer_port}...")
            client.connect(("127.0.0.1", peer_port))
            print(f"[Nodo {self.node_id}] Solicitando archivo con hash: {file_hash}")
            client.sendall(f"REQUEST_FILE::{file_hash}".encode())

            response = client.recv(4096).decode()
            print(f"[Nodo {self.node_id}] Respuesta recibida: {response}")
            if response == "FILE_NOT_FOUND":
                print(f"[Nodo {self.node_id}] Archivo no encontrado en el nodo {peer_id}")
                return False

            if response.startswith("FILE"):
                _, filename, filesize, recv_hash = response.split("::")
                filesize = int(filesize)
                print(f"[Nodo {self.node_id}] Preparando para recibir {filename} ({filesize} bytes)")

                client.sendall("READY".encode())

                filepath = os.path.join(self.storage_dir, filename)
                print(f"[Nodo {self.node_id}] Guardando en: {filepath}")
                with open(filepath, "wb") as f:
                    received_bytes = 0
                    while received_bytes < filesize:
                        chunk = client.recv(min(4096, filesize - received_bytes))
                        if not chunk:
                            break
                        f.write(chunk)
                        received_bytes += len(chunk)
                        print(f"[Nodo {self.node_id}] Progreso: {received_bytes}/{filesize} bytes")
                print(f"[Nodo {self.node_id}] Verificando hash...")        

                with open(filepath, "rb") as f:
                    content = f.read()
                    received_hash = hashlib.sha256(content).hexdigest()

                if received_hash == file_hash:
                    self.files[received_hash] = filepath
                    transaction = Transaction(peer_id, self.node_id, 1, file_hash)
                    self.blockchain.add_transaction(transaction)
                    self.propagate_blockchain()  # Asegúrate de propagar
                    return True
                else:
                    print(f"[Nodo {self.node_id}] Error: Hash no coincide")
                    os.remove(filepath)
                    return False
        except Exception as e:
            print(f"[Nodo {self.node_id}] Error en la transferencia: {e}")
            return False
        finally:
            client.close()

    def receive_blockchain(self, blockchain_data):
        print(f"📥 Nodo {self.node_id} recibiendo blockchain")
        try:
            received_chain = []
            for block_dict in blockchain_data:
                transactions = [
                    Transaction(
                        tx["sender"],
                        tx["receiver"],
                        tx["amount"],
                        tx.get("file_hash"),
                        tx["timestamp"]  # ¡Este es el cambio clave!
                    ) for tx in block_dict["transactions"]
                ]
                block = Block(
                    block_dict["index"],
                    block_dict["previous_hash"],
                    transactions,
                    block_dict["nonce"],
                    block_dict["timestamp"]  # ¡Nuevo parámetro!
                )
                block.hash = block_dict["hash"]
                received_chain.append(block)

            if self.validate_chain(received_chain):
                if len(received_chain) > len(self.blockchain.chain) or (
                    len(received_chain) == len(self.blockchain.chain) and 
                    received_chain[-1].timestamp > self.blockchain.chain[-1].timestamp
                ):
                    print(f"✅ Blockchain actualizada en {self.node_id}")
                    self.blockchain.chain = received_chain
                    # Sincronizar transacciones pendientes
                    self.blockchain.pending_transactions = [
                        tx for tx in self.blockchain.pending_transactions
                        if not any(tx.file_hash == block_tx.file_hash for block in received_chain for block_tx in block.transactions)
                    ]
                    return True
                else:
                    print("ℹ️ La cadena recibida no es más larga o actual")
            else:
                print("🚫 Cadena recibida no válida")
                
        except Exception as e:
            print(f"Error al recibir blockchain: {str(e)}")
        return False

    def validate_chain(self, chain):
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    @staticmethod
    def hash_file(filepath):
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def check_blockchain_integrity(self):
        # Verificar cada bloque individualmente
        for i, block in enumerate(self.blockchain.chain):
            calculated_hash = block.calculate_hash()
            if calculated_hash != block.hash:
                return {
                    "valid": False,
                    "tampered_block": i,
                    "stored_hash": block.hash,
                    "calculated_hash": calculated_hash
                }
        for i in range(1, len(self.blockchain.chain)):
            if self.blockchain.chain[i].previous_hash != self.blockchain.chain[i-1].hash:
                return {
                    "valid": False,
                    "tampered_block": i,
                    "issue": "previous_hash_mismatch"
                }
    
        return {"valid": True}
    
    def simulate_hack(self, block_index):
        if block_index >= len(self.blockchain.chain):
            return {"success": False, "message": "Índice de bloque fuera de rango"}
    
        block = self.blockchain.chain[block_index]
    
        # Verificar si hay transacciones en el bloque
        if not block.transactions:
            return {"success": False, "message": "No hay transacciones en este bloque para hackear"}
    
        # Verificar si alguna transacción tiene un hash de archivo
        file_transactions = [tx for tx in block.transactions if tx.file_hash]
        if not file_transactions:
            return {"success": False, "message": "No hay archivos en este bloque para hackear"}
    
        # Verificar si el nodo tiene el archivo localmente
        for tx in file_transactions:
            file_hash = tx.file_hash
            if file_hash and file_hash not in self.files:
                return {
                    "success": False, 
                    "message": f"Este nodo no tiene el archivo con hash {file_hash} localmente. No puede hackear bloques de archivos que no posee."
                }
    
        # Guardar hash original para referencia
        original_hash = block.hash
    
        # Modificar la primera transacción que tenga un archivo
        target_tx = next((tx for tx in block.transactions if tx.file_hash), None)
        if target_tx:
            original_receiver = target_tx.receiver
            target_tx.receiver = "HACKER"
        
            # Actualizar timestamp pero NO ACTUALIZAR el hash almacenado
            block.timestamp = time.time()
        
            # Calcular nuevo hash pero solo para mostrar
            new_calculated_hash = block.calculate_hash()
        
            return {
                "success": True,
                "message": f"Hackeo simulado en bloque {block_index}",
                "original_hash": original_hash,
                "new_calculated_hash": new_calculated_hash,
                "original_receiver": original_receiver,
                "new_receiver": "HACKER"
            }
    
        return {"success": False, "message": "No se pudo simular el hackeo"}

# Clase para gestionar la red P2P
class P2PNetwork:
    def __init__(self):
        self.nodes = {}

    def add_node(self, node_id, port):
        try:
            node = P2PNode(node_id, port)
            self.nodes[node_id] = node
            print(f"Nodo {node_id} añadido a la red en puerto {port}")
            return node
        except Exception as e:
            print(f"Error añadiendo nodo: {e}")
            return None

    def list_nodes(self):
        result = {}
        for node_id, node in self.nodes.items():
            result[node_id] = {
                "puerto": node.port,
                "peers": node.peers,
                "archivos": {hash: os.path.basename(path) for hash, path in node.files.items()}
            }
        return result

# Inicialización de la aplicación Flask
app = Flask(__name__)
network = P2PNetwork()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/add_node', methods=['POST'])
def add_node():
    try:
        node_id = request.form.get('node_id')
        port = int(request.form.get('port'))

        if node_id in network.nodes:
            return jsonify({"success": False, "message": f"El nodo {node_id} ya existe"}), 400

        for existing_node in network.nodes.values():
            if existing_node.port == port:
                return jsonify({"success": False, "message": f"El puerto {port} ya está en uso"}), 400

        node = network.add_node(node_id, port)
        if node:
            return jsonify({"success": True, "message": f"Nodo {node_id} creado en puerto {port}"})
        else:
            return jsonify({"success": False, "message": "Error al crear el nodo"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/upload_file', methods=['POST'])
def upload_file():
    try:
        node_id = request.form.get('node_id')

        if node_id not in network.nodes:
            return jsonify({"success": False, "message": f"El nodo {node_id} no existe"}), 400

        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No se envió ningún archivo"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "Nombre de archivo vacío"}), 400

        temp_path = os.path.join('temp', file.filename)
        os.makedirs('temp', exist_ok=True)
        file.save(temp_path)

        file_hash = network.nodes[node_id].upload_file(temp_path)
        os.remove(temp_path)

        if file_hash:
            return jsonify({"success": True, "message": "Archivo subido correctamente", "hash": file_hash})
        else:
            return jsonify({"success": False, "message": "Error al subir el archivo"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/request_file', methods=['POST'])
def request_file():
    try:
        node_id = request.form.get('node_id')
        peer_id = request.form.get('peer_id')
        file_hash = request.form.get('file_hash')

        if node_id not in network.nodes:
            return jsonify({"success": False, "message": f"El nodo solicitante {node_id} no existe"}), 400

        success = network.nodes[node_id].request_file(peer_id, file_hash)
        if success:
            return jsonify({"success": True, "message": "Archivo transferido correctamente"})
        else:
            return jsonify({"success": False, "message": "La transferencia falló"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/list_nodes', methods=['GET'])
def list_nodes():
    try:
        return jsonify({"success": True, "nodes": network.list_nodes()})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/verify_blockchain', methods=['GET'])
def verify_blockchain():
    try:
        node_id = request.args.get('node_id')
        if node_id not in network.nodes:
            return jsonify({"success": False, "message": f"El nodo {node_id} no existe"}), 400

        node = network.nodes[node_id]
        is_valid = node.blockchain.is_chain_valid()
        blockchain_data = [block.to_dict() for block in node.blockchain.chain]

        return jsonify({
            "success": True,
            "node_id": node_id,
            "blockchain_valid": is_valid,
            "blockchain_length": len(node.blockchain.chain),
            "blockchain": blockchain_data
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/check_integrity', methods=['GET'])
def check_integrity():
    try:
        node_id = request.args.get('node_id')
        if node_id not in network.nodes:
            return jsonify({"success": False, "message": f"El nodo {node_id} no existe"}), 400

        node = network.nodes[node_id]
        integrity_result = node.check_blockchain_integrity()
        
        return jsonify({
            "success": True,
            "node_id": node_id,
            "integrity": integrity_result
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/simulate_hack', methods=['POST'])
def simulate_hack():
    try:
        node_id = request.form.get('node_id')
        block_index = int(request.form.get('block_index', 1))
        
        if node_id not in network.nodes:
            return jsonify({"success": False, "message": f"El nodo {node_id} no existe"}), 400

        node = network.nodes[node_id]
        hack_result = node.simulate_hack(block_index)
        
        return jsonify({
            "success": True,
            "node_id": node_id,
            "hack_result": hack_result
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/blockchain_notifications', methods=['GET'])
def blockchain_notifications():
    try:
        notifications = []
        for node_id, node in network.nodes.items():
            integrity_result = node.check_blockchain_integrity()
            if not integrity_result["valid"]:
                notifications.append({
                    "node_id": node_id,
                    "type": "integrity_violation",
                    "details": integrity_result
                })
            
            file_alerts = node.verify_file_integrity()
            for alert in file_alerts:
                notifications.append({
                    "node_id": node_id,
                    "type": "file_modification",
                    "details": alert
                })
        
        return jsonify({
            "success": True,
            "has_notifications": len(notifications) > 0,
            "notifications": notifications
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/verify_files', methods=['GET'])
def verify_files():
    try:
        node_id = request.args.get('node_id')
        if node_id not in network.nodes:
            return jsonify({"success": False, "message": f"El nodo {node_id} no existe"}), 400

        node = network.nodes[node_id]
        file_alerts = node.verify_file_integrity()
        
        return jsonify({
            "success": True,
            "node_id": node_id,
            "has_alerts": len(file_alerts) > 0,
            "alerts": file_alerts
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
               
if __name__ == '__main__':
    os.makedirs('temp', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
