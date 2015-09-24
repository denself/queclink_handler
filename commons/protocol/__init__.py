from umsgpack import packb, unpackb
from base64 import b64encode, b64decode

def dump_msg(msg):
    return b64encode(packb(msg))

def load_msg(msg):
    return unpackb(b64decode(msg))