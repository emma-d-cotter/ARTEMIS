from struct import *
from pprint import pprint as pp
import socket               # Import socket module


def unpacker(fmt, buff):
    size = calcsize(fmt)
    return unpack(fmt, buff[:size]), buff[size:]


def get_tracks(buffer):
    print('###NEW PING###')
    while len(buffer):
        track, buffer = unpacker('ffiffffffffffH', buffer)

        print('speed_mps', track[0])
        print('min_angle', track[1])
        print('first_ping', track[2])
        print('min_range_m', track[3])
        print('target_strength', track[4])
        print('last_pos_angle', track[5])
        print('max_angle_m', track[6])
        print('max_range_m', track[7])
        print('last_pos_range', track[8])
        print('width', track[9])
        print('size_sq_m', track[10])
        print('pings_visible', track[11])
        print('height', track[12])
        print('id', track[13])
        print('')


if __name__ == "__main__":

    s = socket.socket()         # Create a socket object
    host = 'localhost'  # Get local machine name
    port = 5000                # Reserve a port for your service.

    s.connect((host, port))
    while True:
        buf = s.recv(4096)
        get_tracks(buf)
    s.close
