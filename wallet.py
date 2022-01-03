from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii


class Wallet:
    def __init__(self, node_id):
        """
        Creates and manages public and private keys
        """

        self.private_key = None
        self.public_key = None
        self.node_id = node_id

    def create_keys(self):
        """
        Create public and private keys
        """

        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

    def save_keys(self):
        """
        Save keys to file
        """

        if self.public_key is not None and self.private_key is not None:
            try:
                with open('wallet-{}.txt'.format(self.node_id), mode='w') as f:
                    f.write(self.public_key)
                    f.write('\n')
                    f.write(self.private_key)
                return True
            except (IOError, IndexError):
                print('Saving wallet failed...')
                return False

    def load_keys(self):
        """
        Load keys from file

        :return: boolean
        """

        try:
            with open('wallet-{}.txt'.format(self.node_id), mode='r') as f:
                keys = f.readlines()
                public_key = keys[0][:-1]
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except (IOError, IndexError):
            print('Loading wallet failed...')
            return False

    def generate_keys(self):
        """
        Generates public and private keys

        :return: tuple containing private key and public key
        """

        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.public_key()

        return (
            binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
            binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
        )

    def sign_transaction(self, sender, recipient, amount):
        """
        Create signature for a transaction

        :param sender: The transaction sender
        :param recipient: The transaction recipient
        :param amount: The transaction amount
        :return: signature string
        """

        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        h = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(h)

        return binascii.hexlify(signature).decode('ascii')

    @staticmethod
    def verify_transaction(transaction):
        """
        Verify the signature of a transaction

        :param transaction:
        :return: result of verification
        """

        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new(
            (str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)).encode('utf8')
        )

        return verifier.verify(h, binascii.unhexlify(transaction.signature))
