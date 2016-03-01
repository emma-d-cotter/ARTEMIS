import socket
import random

def send_triggers(sock, udp_IP, udp_port, triggers, instruments):
    """
    send triggers to save data to AMP interface.

    Inputs:
    sock - socket over which to send data (create with socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
    udp_IP - IP address to send data over (typically "localhost")
    udp_port - port to send data over (typically 61500)
    triggers - dictionary containing boolean trigger values for each instrument
        i.e. {'M3': True,'BlueView': False,'PAM': True,'Cameras': False}
    instruments - instruments included in triggers. This is the order that trigger boolean values will be sent.
        i.e. ['M3', 'BlueView', 'PAM', 'Cameras']

    Outputs:
    bytes_sent = number of bytes sent, should be 17 for 4 instruments.

    Data is sent in the following format:
        "AAAA 1 1 1 1 ZZZZ" where "AAAA" and "ZZZZZ" are always the header and footer, and the "1" values are
        zero or 1 if that instrument should offload data (in the order of the instruments list)
    """


    msg = "AAAA "

    for instrument in instruments:
        if triggers[instrument]:
            msg += '1 '
        else:
            msg += '0 '

    msg += 'ZZZZ'
    msg = bytes(msg, 'utf-8')

    bytes_sent = sock.sendto(msg, (udp_IP, udp_port))

    return bytes_sent
