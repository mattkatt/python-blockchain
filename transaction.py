from collections import OrderedDict
from utility.printable import Printable


class Transaction(Printable):
    def __init__(self, sender, recipient, signature, amount):
        """
        A Transaction which can be added to a block in the blockchain

        :param sender: The sender of the coins
        :param recipient: The receiver of the coins
        :param signature: The signature of the transaction
        :param amount: The amount of coins sent
        """

        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

    def to_ordered_dict(self):
        """
        Convert Transaction to OrderedDict

        :return:
        """

        return OrderedDict([
            ('sender', self.sender),
            ('recipient', self.recipient),
            ('amount', self.amount)
        ])
