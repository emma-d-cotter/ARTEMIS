"""
Reads json data stream over socket from NIMS simulator.

Format is in ../NIMS-track-simulator/ex.json
"""

from struct import *
from pprint import pprint as pp
import socket
import json
import datetime


def unpacker(fmt, buff):
    """
    Unpack buffer from nims simulator
    """
    size = calcsize(fmt)
    return unpack(fmt, buff[:size]), buff[size:]


def get_tracks(stage_instance, buffer):
    """
    Get track information from json buffer, and send to stage.
    """

    while len(buffer):
        msg, buffer = unpacker("=%ds" % len(buffer), buffer)
        nims_data = json.loads(msg[0].decode("utf-8"))

        #print('ping no: ', nims_data['ping_num'])
        #print(nims_data['num_tracks'], ' tracks detected')

        # TODO - ask NIMS to send timestamp with ping number
        timestamp = datetime.datetime.utcnow()
        stage_instance.addDataToPrestage('nims',
                                      [timestamp, nims_data['tracks']])

def read_tracks(stage_instance):
    """
    Function to read data from NIMS simulator, and send to stage.
    """

    s = socket.socket()         # Create a socket object
    host = 'localhost'  # Get local machine name
    port = 5000                # Reserve a port for your service.

    s.connect((host, port))

    while True:
        buf = s.recv(4096)
        get_tracks(stage_instance, buf)

    s.close
