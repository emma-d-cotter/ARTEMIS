import socket

UDP_IP = "" # IP address of data stream
UDP_PORT = 8000 # port num
BUFF_SIZE = 1024 # bytes of data to read in each "chunk"

# create socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRM)
except socket.error,msg:
    # what to do if failed to create socket

try:
    sock.bind((UDP_IP,UDP_PORT))
except socket.error,msg:
    # what to do if failed to bind socket

# keep reading data
while True:

    data,addr = sock.recvfrom(BUFF_SIZE)

    if not data:
        # what to do if no data is present
    else:
        # what to do if data is present
        # confirmation message?
        reply = 'reply'
        sock.sendto(reply,addr)

sock.close()
