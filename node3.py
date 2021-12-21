import requests
from flask import Flask, jsonify, request
import json
import hashlib
import datetime
from uuid import uuid4
from urllib.parse import urlparse
name=input("enter your name")
class Blockchain:
    def __init__(self):
        self.chain =[]
        self.transactions=[]
        self.create_block(proof=1, previous_hash='0')
        self.nodes=set()
    def create_block(self, proof, previous_hash):
        block={
            'index': len(self.chain) + 1,
            'time_stamp':str(datetime.datetime.now()),
            'proof':proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }
        self.transactions=[]
        self.chain.append(block)
        return block
    def get_previous_block(self):
        return self.chain[-1]
    def get_proof(self, previous_proof):
        new_proof=1
        check_proof=False
        while check_proof is False:
            hash_function=hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_function[:4]=="0000":
                check_proof=True
            else:
                new_proof +=1
        return new_proof
    def hash(self, block):
        encoded_block= json.dumps(block, sort_keys= True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block= chain[0]
        block_index= 1
        while block_index<len(chain):
            block=chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof=previous_block['proof']
            proof=block['proof']
            hash_function = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_function[:4] != '0000':
                return False
            previous_block=block
            block_index+=1
        return True
    def add_transaction(self, sender, reciever, amount):
        self.transactions.append({'sender':sender,
                                  'receiver':reciever,
                                  'amount':amount})
        prev_block=self.get_previous_block()
        return prev_block['index'] + 1
    def add_node(self, address):
        parsed_address = urlparse(address)
        self.nodes.add(parsed_address.netloc)
    def replace_chain(self):
        longest_chain = None
        max_length = len(self.chain)
        for i in self.nodes:
            request = requests.get(f'http://{i}/get_chain')
            if request.status_code==200:
                length=request.json()['length']
                chain=request.json()['chain']
                if length>max_length and self.is_chain_valid(chain):
                    longest_chain = chain
                    max_length = length
        if longest_chain:
            self.chain = longest_chain
            return True
        return False




app= Flask(__name__)
node_address = str(uuid4()).replace('-','')
blockchain = Blockchain()

@app.route('/mine_block' ,methods=['GET'])
def mine_block():
    previous_block=blockchain.get_previous_block()
    previous_proof=previous_block['proof']
    proof=blockchain.get_proof(previous_proof)
    previous_hash=blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address,reciever="You", amount=1)
    block=blockchain.create_block(proof,previous_hash)
    response={'message':'Congfatulations you just mined a block',
              'index': block['index'],
              'transactions': block['transactions'],
              'time_stamp': block['time_stamp'],
              'proof': block['proof'],
              'previous_hash': block['previous_hash']
              }
    return jsonify(response), 200
@app.route('/get_chain' ,methods=['GET'])
def get_chain():
    response= {'chain':blockchain.chain,
               'length':len(blockchain.chain)}
    return jsonify(response), 200
@app.route('/is_valid' ,methods=['GET'])
def is_valid():
    is_valid= blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response={'message':"All Good, Its Valid"}
    else:
        response = {'message': "We have a problem"}
    jsonify(response), 200
@app.route('/add_transaction' ,methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_key = ['sender','receiver','amount']
    if not all (keys in json for keys in transaction_key):
        return 'Transaction elements are missing', 406
    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    response={'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201
@app.route('/connect_node' ,methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes= json.get('nodes')
    if nodes is None:
        return 'No Node',400
    for i in nodes:
        blockchain.add_node(i)
    response={'message':f'All nodes are now connected. Vcoin now contains {list(blockchain.nodes)}'}
    return jsonify(response), 201
@app.route('/replace_chain' ,methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': "The chain was replaced with the latest one",
                    'new_chain':blockchain.chain}
    else:
        response = {'message': "The chain was already up to date",
                    'actual_chain':blockchain.chain}
    jsonify(response), 200


app.run(host='0.0.0.0', port=5003)

