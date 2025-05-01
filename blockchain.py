from pymongo import MongoClient
from datetime import datetime
import hashlib
import json
import sys
from dotenv import load_dotenv
import os

load_dotenv()

URI = os.environ.get("MONGO_URI")  # Seguro contra None
client = MongoClient(URI)

# Configuração do MongoDB
URI = "mongodb+srv://blockchain_user:senha123@cluster0.n8aio4h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(URI)
    db = client['blockchain_db']
    collection = db['blockchain']
    
    # Reset inicial (executar apenas na primeira vez)
    collection.delete_many({})
    print("✅ Coleção blockchain resetada com sucesso!")
    
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    sys.exit()

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = self._clean_transactions(transactions)
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self._calculate_hash()

    def _calculate_hash(self):
        block_data = {
            "index": self.index,
            "timestamp": self._format_timestamp(self.timestamp),
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True, separators=(',', ':')).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def _format_timestamp(ts):
        return ts.isoformat(timespec='milliseconds') if isinstance(ts, datetime) else ts

    @staticmethod
    def _clean_transactions(txs):
        return [dict(sorted({k: v for k, v in tx.items() if k != '_id'}.items())) for tx in txs]

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self._format_timestamp(self.timestamp),
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain = self._load_chain()
        print(f"\n📦 Blockchain carregada | Blocos: {len(self.chain)}")

    def _load_chain(self):
        return [Block(
            index=b['index'],
            timestamp=b['timestamp'],
            transactions=b['transactions'],
            previous_hash=b['previous_hash'],
            nonce=b['nonce']
        ) for b in collection.find().sort("index", 1)]

    def create_genesis(self):
        genesis = Block(0, datetime.now(), [], "0")
        collection.insert_one(genesis.to_dict())
        self.chain = [genesis]
        print("\n🧬 Bloco gênese criado com hash:", genesis.hash)

    def add_block(self, transactions):
        last_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now(),
            transactions=transactions,
            previous_hash=last_block.hash
        )
        self._mine_block(new_block)
        collection.insert_one(new_block.to_dict())
        self.chain = self._load_chain()
        print(f"\n✨ Bloco #{new_block.index} adicionado!")

    def _mine_block(self, block, difficulty=4):
        print(f"\n⛏️  Minerando bloco #{block.index}...")
        prefix = '0' * difficulty
        while not block.hash.startswith(prefix):
            block.nonce += 1
            block.hash = block._calculate_hash()
        print(f"🎉 Bloco minerado! Nonce: {block.nonce}")

    def validate_chain(self):
        """Valida a integridade da blockchain"""
        if not self.chain:
            return False
            
        # Verifica o bloco gênese
        genesis = self.chain[0]
        if (genesis.index != 0 or
            genesis.previous_hash != "0" or
            genesis.hash != genesis._calculate_hash() or
            len(genesis.transactions) != 0):
            return False

        # Verifica os blocos subsequentes
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # Valida hash atual
            if current_block.hash != current_block._calculate_hash():
                return False

            # Valida ligação com bloco anterior
            if current_block.previous_hash != previous_block.hash:
                return False

            # Valida proof-of-work
            if not current_block.hash.startswith('0000'):
                return False

        return True

def main():
    # Inicializa a blockchain
    blockchain = Blockchain()
    
    # Cria o bloco gênese se necessário
    if not blockchain.chain:
        blockchain.create_genesis()
    
    # Adiciona blocos de exemplo
    for i in range(1, 5):
        blockchain.add_block([{
            'estabelecimento': f'Loja {i}',
            'tipo': 'Ativação',
            'detalhes': f'Ativação da Loja {i}'
        }])
    
    # Valida a blockchain
    print("\n=== VALIDAÇÃO INICIAL ===")
    if blockchain.validate_chain():
        print("✅ Blockchain válida!")
    else:
        print("❌ Blockchain inválida!")

if __name__ == "__main__":
    main()

# ... (todo o código anterior permanece igual até a função main)

def main():
    # Inicializa a blockchain
    blockchain = Blockchain()
    
    # Cria o bloco gênese se necessário
    if not blockchain.chain:
        blockchain.create_genesis()
    
    # Adiciona blocos de exemplo
    for i in range(1, 5):
        blockchain.add_block([{
            'estabelecimento': f'Loja {i}',
            'tipo': 'Ativação',
            'detalhes': f'Ativação da Loja {i}'
        }])
    
    # Validação inicial
    print("\n=== VALIDAÇÃO INICIAL ===")
    if blockchain.validate_chain():
        print("✅ Blockchain válida!")
    else:
        print("❌ Blockchain inválida!")

    # ==============================================
    # ADULTERAÇÃO MANUAL DE UM BLOCO
    # ==============================================
    print("\n🔥 Realizando adulteração manual no Bloco #1...")
    
    # Altera um dado no MongoDB
    collection.update_one(
        {"index": 1},
        {"$set": {"transactions.0.detalhes": "DADO CORROMPIDO!"}}
    )
    
    # Recarrega a blockchain com o bloco adulterado
    blockchain.chain = blockchain._load_chain()
    
    # Nova validação
    print("\n=== VALIDAÇÃO APÓS ADULTERAÇÃO ===")
    if blockchain.validate_chain():
        print("✅ Blockchain válida!")
    else:
        print("❌ Blockchain inválida!")

if __name__ == "__main__":
    main()