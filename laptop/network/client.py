import socket
import struct
import json
import select
import logging

serverIp = ("127.0.0.1", 65432)

class NetworkError(Exception):
    pass

class NetworkTimeoutError(Exception):
    pass

def receive_from_socket(sock, size):
    buf = b""

    while len(buf) != size:
        read, _, _ = select.select([sock], [], [], 1) #Make sure we can read from client. If not, we wait up to 1 sec before timing out

        if len(read) == 0:
            raise NetworkTimeoutError()

        data = read[0].recv(size-len(buf))
        if not data:
            raise NetworkError()
    
        buf += data

    return buf

def send_message(message):
    '''
    Sends the request message to the server. Message should be a dictionary (it will be converted to JSON)
    Return True if the sending was successful
    '''
    logger = logging.getLogger(__name__)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(serverIp)

            payload = json.dumps(message).encode("utf-8")
            sock.sendall(struct.pack("!L", len(payload))) #Send length of the payload
            sock.sendall(payload) #Send the payload itself
            logger.debug("Sent payload. Now waiting for confirmation.")
            data = receive_from_socket(sock, len("OK".encode("utf-8"))) #Receive the confirmation. We read for the exact amount of bytes we expect

            confirmation = data.decode("utf-8")
            logger.debug("Received {}".format(confirmation))
            if confirmation != "OK":
                raise NetworkError
    except:
        return False

    return True