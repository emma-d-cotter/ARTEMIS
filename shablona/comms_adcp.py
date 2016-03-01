# to do:
# - read in tidal predictions (if file exists) to validate data
import socket
import numpy as np


def ADCP_read(udp_IP = "", udp_port = 61557, buff_size = 1024, timeout = 5):
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
    sock.bind((udp_IP, udp_port))
    sock.settimeout(timeout)

    # read one data packet
    currents = []
    headers = []
    while True:

        # read data. Continue reading if timeout error, attempt to reconnect if
        # there is a different socket error.
        try:
            data, addr = sock.recvfrom(buff_size)
        except socket.timeout:
            if len(currents):
                process_ADCP(currents, header)
                currents = []

                # ***temporary exit after burst***
                sock.close()
                break
            else:
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
            current, header = decode_ADCP(data)
            currents.append(current)
            headers.append(header)
            del data

    sock.close()


def decode_ADCP(data):
    """
    Decodes ADCP data read in over UDP. Returns two lists: header and current.

    input: Raw data string from ADCP UDP stream

    Output:
    header: [timestamp, nCells, nBeams, pressure]
        - timestamp in unix format
        - nBeams x nCells gives dimensions of current data
        - pressure is hydrostatic pressure in dBar

    current: nBeams x nCells current values in m/s
    """
    data = data.decode("utf-8")

    if data.endswith('ZZZZ') and data.startswith('AAAA'):
        data = data.split(' ')
        timestamp = float(data[1]) + float(data[2])/1000
        nCells = int(data[3])
        nBeams = int(data[4])
        pressure = int(data[5])
        current = np.array(list(map(float, list(data[6:-2]))))/1000
        current = np.resize(current, (nBeams, nCells)).round(3)

        header = [timestamp, nCells, nBeams, pressure]
    else:
        header = []
        current = []

    return current, header


def process_ADCP(currents, header):
    """
    Calculates velocity magnitude and direction after a burst has finished.

    Inputs:
    Currents = raw data from ADCP [nPings x nBeams x nCells]
    Header = header data from ADCP

    Outputs:
    Heading = velocity direction (in radians from magnetic north)
    Speed = magintude of horizontal velocity (East and North)
    Depth = water depth above ADCP, in m
    """
    timestamp = header[0]

    currents = np.array(currents)
    bin_avg = np.mean(currents, axis=0)
    bins = bin_avg[:, 1:4]
    avg = np.mean(bins, axis=1).round(3)

    heading = np.arctan(avg[1]/avg[0]).round(3)
    speed = (avg[1]**2 + avg[0]**2)**0.5

    pressure = header[3]/0.0001   # dBar to Pa
    # depth = pressure/(g*rho)   # fix this correction!

    vel = [timestamp, speed, heading]
