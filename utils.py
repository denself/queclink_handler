import random
import string
import functools
from voluptuous import Any


def rsrvd():
    chars = string.ascii_uppercase + string.digits
    return 'reserved_' + ''.join(random.choice(chars) for _ in range(4))


def protocol_validator(default_value, *validators):
    """Sets a value to default_value if none provided.

    >>> s = Schema(qq(42))
    >>> s(None)
    42
    """
    @functools.wraps(protocol_validator)
    def f(v):
        if not v:
            v = default_value
        fn = Any(*validators)
        return fn(v)
    return f


def generate_random_hex(strlen=4):
    return ''.join(random.choice(string.hexdigits)
                   for _ in xrange(strlen)).upper()


def process_supported_pids(data):
    if not data:
        return []
    r = []
    bit_mask = bin(int(data, 16)).replace('0b', '')
    for i, mask in enumerate(bit_mask):
        pid = "%0.2X" % (i + 1)
        if (int(mask) & 1):
            r.append('01' + pid)
    return r
