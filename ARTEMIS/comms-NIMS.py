#!/usr/bin/env python

"""
A simple data client
"""

from socket import socket, AF_INET, SOCK_STREAM
from time import sleep
import json
import os, sys
import select

_HOST = '192.168.5.100'
_PORT = 8001

def _reconnect(receive_socket=None):

    if receive_socket:
        receive_socket.shutdown(2)
        receive_socket.close()

    receive_socket = socket(AF_INET, SOCK_STREAM)
    receive_socket.connect((_HOST, _PORT))

    # set to nonblocking so we can use the select loop and
    # get a timeout
    receive_socket.setblocking(False)

    options = { "frequency" : 10, "host" : _HOST }
    ts = bytes(json.dumps(options), "utf-8")
    receive_socket.send(ts)

    return receive_socket

if __name__ == '__main__':

    receive_socket = _reconnect()

    data = ""

    #outfile = open("client-%d.txt" % (os.getpid()), "w")

    while 1:
        try:
            try:

                rtr, rtw, ie = select.select([receive_socket], [], [], 60.0)
                if len(rtr):
                    new_data = receive_socket.recv(4096)

                    # can this even happen, now that select it used?
                    if len(new_data) == 0:
                        sys.stderr.write("empty data returned from socket\n")
                        data = ""
                        receive_socket = _reconnect()

                    data += new_data.decode('utf-8')
                    comps = data.split("\0")
                    if len(comps):
                        for line in comps[0:-1]:
                            print(line)
                            msg = json.loads(line, encoding="utf-8")
                            #outfile.write("ping_num %d\n" % (msg["ping_num"]))
                        if len(comps[-1]) == 0:
                            # all components received
                            data = ""
                        else:
                            data = comps[-1]
                    else:
                        sys.stderr.write("not enough data yet\n")
                else:
                    sys.stderr.write("receive timed out; trying to reconnect\n")
                    data = ""
                    receive_socket = _reconnect(receive_socket)

            except select.error as e:
                receive_socket.shutdown(2)
                receive_socket.close()
                sys.stderr.write("select error; trying to reconnect\n")
                data = ""
                receive_socket = _reconnect(receive_socket)


        except KeyboardInterrupt as e:
            receive_socket.close()
            exit(0)
