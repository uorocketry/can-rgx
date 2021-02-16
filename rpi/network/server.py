import logging
import multiprocessing
import select
import socketserver
import struct

import shared.config as config
from rpi.network.messagehandler import MessageHandler


class NetworkError(Exception):
    pass


class NetworkReadingTimeoutError(Exception):
    pass


class NetworkWritingTimeoutError(Exception):
    pass


message_handler = None


class RequestHandler(socketserver.StreamRequestHandler):
    """
    Handles an incoming request. It expects the request to have a header of type
    unsigned long indicating the size of the following body. Body should be in JSON with
    utf-8 encoding. If the message can successfully be parsed (but not necessarily processed),
    a "OK" will be sent back to the client. If there is an error while parsing the message,
    the connection will be closed without anything being sent.
    """

    def read_chunk(self, size):
        buf = b""

        while len(buf) != size:
            read, _, _ = select.select([self.request], [], [],
                                       1)  # Make sure we can read from client. If not, we wait up to 1 sec before timing out

            if len(read) == 0:
                raise NetworkReadingTimeoutError()

            data = read[0].recv(size - len(buf))
            if not data:
                raise NetworkError()

            buf += data

        return buf

    def send_data(self, data):
        _, write, _ = select.select([], [self.request], [],
                                    1)  # Make sure we can write to client. If not, we wait up to 1 sec before timing out

        if len(write) == 0:
            raise NetworkWritingTimeoutError()

        write[0].sendall(data)

    def handle(self):
        logger = logging.getLogger(__name__)

        self.request.setblocking(0)
        try:
            header = self.read_chunk(struct.calcsize("L"))
            bodySize = struct.unpack("!L", header)[0]
            body = self.read_chunk(bodySize).decode("utf-8")

            logger.debug("Received {} from {}".format(body, self.client_address))

            self.send_data("OK".encode("utf-8"))
        except NetworkReadingTimeoutError:
            logger.error("Timed out while reading from client")
        except NetworkWritingTimeoutError:
            logger.error("Timed out while writing to client")
        except NetworkError:
            logger.error("Error while reading from client. Is the message in the correct format?")
        except:
            logger.exception("Major error while handling client connection")
        else:
            # noinspection PyUnresolvedReferences
            message_handler.process_message(body, self.client_address)


class Server(multiprocessing.Process):
    def run(self):
        """
        Starts a server to listen and handle incoming requests. This will run until the heat
        death of the universe, or until the program is interrupted, whichever comes first.
        """
        logger = logging.getLogger(__name__)
        logger.info("Starting server and listening to incoming connections")

        RPIConfig = config.get_config('rpi')
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer((RPIConfig['rpi_listening_ip'], RPIConfig.getint('rpi_port')),
                                    RequestHandler) as server:
            global message_handler
            message_handler = MessageHandler()
            server.serve_forever()
