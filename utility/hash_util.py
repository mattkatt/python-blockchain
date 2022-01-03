import hashlib as _hl
import json


# __all__ = ['hash_string_256', 'hash_block']


def hash_string_256(string):
    """
    Hash a string using SHA256

    :param string:
    :return:
    """

    return _hl.sha256(string).hexdigest()


def hash_block(block):
    """
    Hashes provided block

    :param block: Block to be hashed
    :return: Hashed string
    """

    hashable_block = block.__dict__.copy()
    hashable_block['transactions'] = [
        tx.to_ordered_dict() for tx in hashable_block['transactions']
    ]

    return hash_string_256(json.dumps(hashable_block, sort_keys=True).encode())
