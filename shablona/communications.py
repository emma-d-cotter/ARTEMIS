import socket
import numpy as np

def UDP_read(udp_IP,udp_port,buff_size,timeout,datasource):
    """
    Reads data continously from the specified port, and parses data in specified format.

    Inputs:
    udp_ip: "" for local host, otherwise "XXX.XXX.XXX.XXX"
    udp_port: port for UDP communication (61557 = ADCP Default)
    buff_size: Each read iteration will read buff_size bytes of data, or until the end of a packet is reached.
    datasource: specify source of data to parse. Currently implemented: "ADCP"
    """

    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, server.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) | 1)
    sock.bind((udp_IP,udp_port))
    sock.settimeout(timeout)

    # read one data packet

    while True:

        # read data. Continue reading if timeout error, attempt to reconnect if there is a different
        # socekt error.
        try:
            data,addr = sock.recvfrom(buff_size)
        except socket.timeout:
            pass
        except socket.error:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((udp_IP, udp_port))
            sock.settimeout(timeout)

        # decode data, if present
        try:
            data
        except NameError:
            pass
        else:
            decode_UDP_data(data,datasource)
            del data

    sock.close()

def decode_UDP_data(data,datasource):

    if datasource == 'ADCP':
        decode_ADCP(data)
    if datasource == 'NIMS':
        decode_NIMS(data)
    if datasource == 'PAMGuard':
        decode_PAMGuard(data)

def decode_NIMS(data):
    NIMS = []

    return NIMS

def decode_PAMGuard(data):
    PAMGuard = []

    return PAMGuard

def ADCP_read(udp_IP,udp_port,buff_size,timeout):
    """
    Reads ADCP data continously from the specified port.
    **EDITING NOTE - break added after timeout**

    Inputs:
    udp_ip: "" for local host, otherwise "XXX.XXX.XXX.XXX"
    udp_port: port for UDP communication (61557 = ADCP Default)
    buff_size: Each read iteration will read buff_size bytes of data, or until
    the end of a packet is reached.
    """

    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_IP,udp_port))
    sock.settimeout(timeout)

    # read one data packet
    currents = [];
    headers = [];
    while True:

        # read data. Continue reading if timeout error, attempt to reconnect if there is a different
        # socket error.
        try:
            data,addr = sock.recvfrom(buff_size)
        except socket.timeout:
            if len(currents):
                process_ADCP(currents,header)
                currents = []

                # temporary exit after burst
                sock.close()
                break
            else:
                pass

        except socket.error:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((udp_IP,udp_port))
            sock.settimeout(timeout)

        # decode data, if present
        try:
            data
        except NameError:
            pass
        else:
            current, header = decode_ADCP(data)
            currents.append(current)
            headers.append(header)
            del data


    sock.close()


def decode_ADCP(data):
    """
    Decodes ADCP data read in over UDP. Returns list with elements
    [timestamp, nCells, nBeams, current].

    Timestamp is in unix format, and current values are in m/s. array of current
    values is size nBeams x nCells.
    """
    data = data.decode("utf-8")

    if data.endswith('ZZZZ') and data.startswith('AAAA'):
        data = data.split(' ')
        timestamp = float(data[1]) + float(data[2])/1000
        nCells = int(data[3])
        nBeams = int(data[4])
        current = np.array(list(map(float,list(data[5:-2]))))/1000
        current = np.resize(current, (nBeams,nCells))
        current = current.round(3)

        header = [timestamp,nCells,nBeams]
    else:
        header = []
        current = []

    return current, header


def process_ADCP(currents,header):
    currents = np.array(currents)
    bin_avg = np.mean(currents,axis=0)

    # save to database

    print(bin_avg)
    return bin_avg
