from time import time
import hashlib
import json
from flask import Flask, jsonify, request
from uuid import uuid4
from urllib.parse import urlparse

# {
#     "index": 0,
#     "timestamp": "",
#     "transactions": [
#         {
#             "sender": "",
#             "recipient": "",
#             "amount": 5,
#         }
#     ],
#     "proof":"",
#     "previous_hash":""
# }

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(proof=100, previous_hash=1)
        self.difficult = 3
        self.nodes = set()

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


    def new_block(self, proof, previous_hash = None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.current_transactions,
            "proof":proof,
            "previous_hash": previous_hash or self.hash(self.last_block())
        }

        self.current_transactions = []
        self.chain.append(block)

        return block
        
    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append(
            {
                'sender': sender,
                'recipient': recipient,
                'amount': amount
            }
        )
        return self.last_block()['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        print(proof)

        return proof

    def valid_proof(self, last_proof: int, proof: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        # print(guess_hash)
        return guess_hash[0:self.difficult] == '0' * self.difficult

# testPow = Blockchain()
# testPow.proof_of_work(100)

app = Flask(__name__)
blockchain = Blockchain()

node_identifier = str(uuid4()).replace('-', '')


@app.route("/index", methods=['GET'])
def index():
    return "Hello Blockchain"

@app.route("/transactions", methods=['post'])
def new_transaction():
    # values = request.get_json()
    # required = ['sender', 'recipient', 'amount']
    # if not all(k in values for k in required) or values is None:
    #     return "Missing values", 400

    values = request.get_json()

    # 检查POST数据
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    index = blockchain.new_transaction( values['sender'],
                                values['recipient'],
                                values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}

    return jsonify(response), 201

@app.route("/mine", methods=['get'])
def mine():
    last_block = blockchain.last_block()
    last_proof = last_block["proof"]
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(sender = "0", 
                                recipient="node_identifier",
                                amount="1")
    block = blockchain.new_block(proof, previous_hash = None)
    response = {
        "message": "New Block Forged",
        "index": block['index'],
        "transactions": block['transactions'],
        "proof": block['proof'],
        "previous_hash": block['previous_hash']
    }
    return jsonify(response), 200


@app.route("/chain", methods=['get'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    } 
    return jsonify(response), 200

@app.route("/nodes/register", methods=['post'])
def register_node():
    values = request.get_json()
    nodes = values.get("nodes")
    if nodes is None:
        return "Error: please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        "message": "New nodes have been added",
        "total_nodes": list(blockchain.nodes)
    }
    return jsonify(response), 201

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)