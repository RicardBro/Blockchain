import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any


class Block:
    """
    Representa un bloque en la blockchain.
    
    Atributos:
        index: Posición del bloque en la cadena
        timestamp: Momento de creación del bloque
        transactions: Lista de transacciones incluidas en el bloque
        previous_hash: Hash del bloque anterior
        nonce: Número usado para la prueba de trabajo (mining)
        hash: Hash del bloque actual
    """
    
    def __init__(self, index: int, transactions: List[Dict[str, Any]], 
                 previous_hash: str, nonce: int = 0):
        self.index = index
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calcula el hash SHA-256 del bloque basado en sus atributos.
        """
        block_string = f"{self.index}{self.timestamp}{self.transactions}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int) -> None:
        """
        Mina el bloque encontrando un hash que cumple con la dificultad especificada.
        
        Args:
            difficulty: Número de ceros que debe tener el hash al inicio
        """
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el bloque a un diccionario para facilitar la visualización.
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }


class Blockchain:
    """
    Representa la cadena de bloques completa.
    
    Atributos:
        chain: Lista de bloques que conforman la blockchain
        difficulty: Dificultad de minado (número de ceros al inicio del hash)
        mempool: Lista de transacciones pendientes (no minadas)
    """
    
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.mempool: List[Dict[str, Any]] = []
        self._create_genesis_block()
    
    def _create_genesis_block(self) -> None:
        """
        Crea el bloque génesis (primer bloque de la cadena).
        """
        genesis_block = Block(0, [{"type": "genesis", "data": "Bloque Génesis"}], "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        """
        Obtiene el último bloque de la cadena.
        """
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict[str, Any]) -> None:
        """
        Añade una transacción al mempool.
        
        Args:
            transaction: Diccionario con los datos de la transacción
        """
        self.mempool.append(transaction)
    
    def mine_pending_transactions(self) -> Block:
        """
        Mina un nuevo bloque con las transacciones pendientes del mempool.
        
        Returns:
            El bloque recién minado
        """
        if not self.mempool:
            return None
        
        new_block = Block(
            index=len(self.chain),
            transactions=self.mempool.copy(),
            previous_hash=self.get_latest_block().hash
        )
        
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.mempool = []  # Limpiar el mempool después de minar
        
        return new_block
    
    def is_chain_valid(self) -> tuple[bool, str]:
        """
        Valida la integridad de toda la blockchain.
        
        Returns:
            Tupla (es_válida, mensaje_error)
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Verificar que el hash del bloque actual es correcto
            if current_block.hash != current_block.calculate_hash():
                return False, f"Bloque {i}: Hash inválido"
            
            # Verificar que el bloque apunta correctamente al bloque anterior
            if current_block.previous_hash != previous_block.hash:
                return False, f"Bloque {i}: Cadena rota - previous_hash no coincide"
            
            # Verificar que el hash cumple con la dificultad
            if not current_block.hash.startswith("0" * self.difficulty):
                return False, f"Bloque {i}: No cumple con la dificultad requerida"
        
        return True, "Blockchain válida"
    
    def hack_block(self, block_index: int, new_data: Dict[str, Any]) -> None:
        """
        Modifica un bloque existente (simula un hack) para demostrar la inmutabilidad.
        
        Args:
            block_index: Índice del bloque a modificar
            new_data: Nueva transacción a agregar al bloque
        """
        if 0 < block_index < len(self.chain):
            self.chain[block_index].transactions.append(new_data)
            self.chain[block_index].hash = self.chain[block_index].calculate_hash()
    
    def get_chain_as_list(self) -> List[Dict[str, Any]]:
        """
        Retorna la cadena completa como lista de diccionarios.
        """
        return [block.to_dict() for block in self.chain]
