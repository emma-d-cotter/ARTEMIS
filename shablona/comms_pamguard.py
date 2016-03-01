import socket
import datetime

def PAMGuard_read(stage_instance, udp_IP = "",udp_port = 8000,buff_size = 1024,timeout = 0.1):
    """
    Reads ADCP data continously from the specified port.

    Inputs:
    udp_ip: "" for local host, otherwise "XXX.XXX.XXX.XXX"
    udp_port: port for UDP communication (8000 = PAM Default)
    buff_size: Each read iteration will read buff_size bytes of data, or until
    the end of a packet is reached.
    timeout: socket timeout (0.1 default)
    """
    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_IP,udp_port))
    sock.settimeout(timeout)

    while True:
        try:
            data, addr = sock.recvfrom(buff_size)
        except socket.timeout:
            pass
        except socket.error:
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((udp_IP, udp_port))
            sock.settimeout(timeout)

        try:
            data
        except NameError:
            pass
        else:
            data = data.decode("utf-8")
            if data.endswith('ZZZZ') and data.startswith('AAAA'):
                detection = data[4:-4]
                timestamp = datetime.datetime.now()

                pamguard_data = [timestamp, detection]
                stage_instance.addDataToStage('pamguard', pamguard_data)

                print("PAMGuard Detection of type: ", detection)
                
                del data
            else:
                del data
