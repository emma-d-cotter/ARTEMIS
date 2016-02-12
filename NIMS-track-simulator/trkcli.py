from struct import *
from pprint import pprint as pp
import socket               # Import socket module
import json


def unpacker(fmt, buff):
    size = calcsize(fmt)
    return unpack(fmt, buff[:size]), buff[size:]


def get_tracks(buffer):
    while len(buffer):
        msg, buffer = unpacker("=%ds" % len(buffer), buffer)
        tracks = json.loads(msg[0].decode("utf-8"))

if __name__ == "__main__":

    s = socket.socket()         # Create a socket object
    host = 'localhost'  # Get local machine name
    port = 5000                # Reserve a port for your service.

    s.connect((host, port))
    while True:
        buf = s.recv(4096)
        get_tracks(buf)
    s.close
