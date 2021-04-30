import logging
import logging.handlers
import pickle
import select
import socketserver
import struct
import threading
import time

import shared.config as config
from shared.customlogging.errormanager import ErrorManager


class NetworkError(Exception):
    pass


error_manager = ErrorManager(__name__, 5)


class LogRecordConnector(threading.Thread):
    """
    Simple class that will check if a client has connected to the logging server.
    If no client connects after some time, an alert will be sent to the user.
    """

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        self._stop_event.clear()

        while True:
            time.sleep(5)

            if self._stop_event.is_set():
                break

            error_manager.escalate("RPI is not connecting to the logging server", "loggingConnection")

    def stop(self):
        self._stop_event.set()


logConnector = LogRecordConnector()


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def read_chunk(self, size):
        buf = b""

        while len(buf) != size:
            read, _, _ = select.select([self.request], [], [])  # Make sure we can read from client.

            if len(read) == 0:
                raise NetworkError()

            data = read[0].recv(size - len(buf))
            if not data:
                raise NetworkError()

            buf += data

        return buf

    def handle(self):
        global logConnector
        logger = logging.getLogger(__name__)
        error_manager.resolve("Got a connection from {}".format(self.client_address), "loggingConnection")

        logConnector.stop()  # Stop monitoring for connection

        self.request.setblocking(0)
        connected = True
        while connected:
            try:
                chunk = self.read_chunk(4)
                length = struct.unpack(">L", chunk)[0]

                body = self.read_chunk(length)
                obj = pickle.loads(body)

                record = logging.makeLogRecord(obj)
                self.handle_record(record)
                error_manager.resolve("Network error resolved", "loggingException", False)
            except (NetworkError, ConnectionResetError):
                error_manager.warning("Network error. Did the client close the connection?", "loggingException")
                connected = False
            except:
                error_manager.error("Error while receiving log from client", "loggingException")
                connected = False

        logConnector = LogRecordConnector()
        logConnector.start()  # Monitor for connection and send alert to user if necessary

    def handle_record(self, record):
        logger = logging.getLogger(record.name)

        # Check if this is for a sensor logs and that is has a handler. If not, raise an error
        if record.name.startswith('sensorlog') and len(logger.handlers) == 0:
            logging.getLogger(__name__).error("Unhandled sensor logger: " + record.name)

        logger.handle(record)


def logging_receive_forever():
    LaptopConfig = config.get_config('laptop')
    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer((LaptopConfig['laptop_listening_ip'], logging.handlers.DEFAULT_TCP_LOGGING_PORT),
                                    LogRecordStreamHandler) as server:
            logConnector.start()  # Monitor for connection and send alert to user if necessary
            server.serve_forever()
    except:
        logging.getLogger(__name__).exception("Error starting the laptop's TCP server! Please restart the whole GUI "
                                              "application")
