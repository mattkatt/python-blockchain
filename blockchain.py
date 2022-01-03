# Initialising blockchain list
import json
import requests

from functools import reduce

from block import Block
from transaction import Transaction
from utility.verification import Verification
from utility.hash_util import hash_block
from wallet import Wallet

MINING_REWARD = 10


class Blockchain:
    def __init__(self, public_key, node_id):
        """
        Create a blockchain with open transactions and a genesis block, then loads data

        :param public_key: The public_key of the hosting node
        :param node_id: the id of the node initiating the Blockchain
        """

        genesis_block = Block(0, '', [], 100, 0)
        self.chain = [genesis_block]
        self.__open_transactions = []
        self.public_key = public_key
        self.node_id = node_id
        self.__peer_nodes = set()
        self.resolve_conflicts = False
        self.load_data()

    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_chain(self):
        return self.chain[:]

    def get_open_transactions(self):
        return self.__open_transactions[:]

    def load_data(self):
        """
        Load blockchain and open transactions
        """

        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as file:
                # file_content = pickle.loads(file.read())
                file_content = file.readlines()

                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [
                        Transaction(tx['sender'],
                                    tx['recipient'],
                                    tx['signature'],
                                    tx['amount']) for tx in block['transactions']
                    ]

                    updated_block = Block(block['index'],
                                          block['previous_hash'],
                                          converted_tx, block['proof'],
                                          block['timestamp'])

                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain

                open_transactions = json.loads(file_content[1][:-1])
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(tx['sender'],
                                                      tx['recipient'],
                                                      tx['signature'],
                                                      tx['amount'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions

                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            pass
        finally:
            print('Cleanup!')

    def save_data(self):
        """
        Saves current blockchain and open transactions
        """

        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as file:
                chain = [
                    block.__dict__ for block in [
                        Block(block_el.index,
                              block_el.previous_hash,
                              [tx.__dict__ for tx in block_el.transactions],
                              block_el.proof,
                              block_el.timestamp) for block_el in self.__chain
                    ]
                ]
                file.write(json.dumps(chain))
                file.write('\n')
                transactions = [
                    tx.__dict__ for tx in self.__open_transactions
                ]
                file.write(json.dumps(transactions))
                file.write('\n')
                file.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving Failed')

    def proof_of_work(self):
        """
        Determine proof of work

        :return: proof number
        """

        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0

        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, sender=None):
        """
        Get balance for specific blockchain participant

        :return: balance amount
        """

        if sender is None:
            if self.public_key is None:
                return None

            participant = self.public_key
        else:
            participant = sender

        sender_tx = [
            [tx.amount for tx in block.transactions if tx.sender == participant] for block in self.__chain
        ]
        sender_open_tx = [
            tx.amount for tx in self.__open_transactions if tx.sender == participant
        ]
        sender_tx.append(sender_open_tx)
        amount_sent = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, sender_tx, 0
        )
        recipient_tx = [
            [tx.amount for tx in block.transactions if tx.recipient == participant] for block in self.__chain
        ]
        amount_received = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, recipient_tx, 0
        )

        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        """
        Returns the last block of the current blockchain

        :return: block
        """

        if len(self.__chain) < 1:
            return None

        return self.__chain[-1]

    def add_transaction(self, recipient: str, sender, signature, amount=1.0, is_receiving=False):
        """
        Append a new value as well as the last blockchain value

        :param sender: The sender of the coins
        :param recipient: The receiver of the coins
        :param signature: The signature of the transaction
        :param amount: The amount of coins sent (default = 1.0)
        :param is_receiving: Boolean to determine if node is receiving data from peer node
        :return: boolean
        """

        transaction = Transaction(sender, recipient, signature, amount)

        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()

            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url, json={
                            'sender': sender,
                            'recipient': recipient,
                            'amount': amount,
                            'signature': signature
                        })
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving')
                            return False
                        return True
                    except requests.exceptions.ConnectionError:
                        continue

            return True

        return False

    def mine_block(self):
        """
        Mine new block and add to existing blockchain with open trans.

        :return: block|None
        """

        if self.public_key is None:
            return None

        last_block = self.__chain[-1]
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()

        reward_transaction = Transaction('MINING', self.public_key, '', MINING_REWARD)

        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None

        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain),
                      hashed_block,
                      copied_transactions,
                      proof)

        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()

        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [
                tx.__dict__ for tx in converted_block['transactions']
            ]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        """
        Add block directly to chain

        :param block: The block to add
        :return: Boolean
        """
        transactions = [
            Transaction(tx['sender'],
                        tx['recipient'],
                        tx['signature'],
                        tx['amount']) for tx in block['transactions']
        ]
        proof_is_valid = Verification.valid_proof(transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False

        converted_block = Block(block['index'],
                                block['previous_hash'],
                                transactions,
                                block['proof'],
                                block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        for itx in block['transactions']:
            for open_tx in stored_transactions:
                if (open_tx.sender == itx['sender']
                        and open_tx.recipient == itx['recipient']
                        and open_tx.amount == itx['amount']
                        and open_tx.signature == itx['signature']):
                    try:
                        self.__open_transactions.remove(open_tx)
                    except ValueError:
                        print('Item was already removed')

        self.save_data()
        return True

    def resolve(self):
        winner_chain = self.chain
        replace = False

        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [
                    Block(block['index'],
                          block['previous_hash'],
                          [Transaction(tx['sender'],
                                       tx['recipient'],
                                       tx['signature'],
                                       tx['amount']
                                       ) for tx in block['transactions']],
                          block['proof'],
                          block['timestamp']
                          ) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue

        self.resolve_conflicts = False
        self.chain = winner_chain

        if replace:
            self.__open_transactions = []

        self.save_data()
        return replace

    def add_peer_node(self, node):
        """
        Adds a new node to the peer node set

        :param node: The node URL to add
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """
        Removes a node from the peer node set

        :param node: The node URL to remove
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        """
        Get list of all connected peer nodes

        :return: node list
        """
        return list(self.__peer_nodes)
