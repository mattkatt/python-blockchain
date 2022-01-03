from utility.hash_util import hash_block, hash_string_256
from wallet import Wallet


class Verification:
    """
    Provides verification helper methods
    """

    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        """
        Validates proof algorithm to solve hash

        :param transactions: Open transactions
        :param last_hash: Hash of last block in blockchain
        :param proof: Current guess
        :return: result of proof validation
        """

        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        guess_hash = hash_string_256(guess)
        print(guess_hash)

        return guess_hash[0:2] == '00'

    @classmethod
    def verify_chain(cls, blockchain):
        """
        Verify the current blockchain

        :return: result of chain validation
        """

        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print('Proof of work is invalid')
                return False

        return True

    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds=True):
        """
        Verify if sender can make supplied transaction

        :param transaction: Transaction to verify
        :param get_balance: Method to get balance from transaction
        :param check_funds: Boolean to trigger checking if funds available
        :return: result of transaction verification
        """

        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)
        else:
            return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        """
        Verify all transactions at once

        :param open_transactions: All transactions to verify
        :param get_balance: Method to get balance from transaction
        :return: True if all transactions are valid, else False
        """

        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])
