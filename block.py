from time import time

from utility.printable import Printable


class Block(Printable):
    def __init__(self, index, previous_hash, transactions, proof, timestamp=None):
        """
        Create a block for the blockchain

        :param index: The index of the block
        :param previous_hash: The hash of the previous block
        :param transactions: List of transactions
        :param proof: Proof of block solution
        :param timestamp: Time of block creation
        """

        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = time() if timestamp is None else timestamp
        self.transactions = transactions
        self.proof = proof
