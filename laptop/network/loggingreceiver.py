import logging
import logging.handlers
import pickle
import select
import socketserver
import struct
import threading
import time

import shared.config as config
from shared.customlogging.formatter import CSVFormatter
from shared.customlogging.handler import MakeFileHandler


class NetworkError(Exception):
    pass


class LogRecordConnector(threading.Thread):
    '''
    Simple class that will check if a client has connected to the logging server.
    If no client connects after some time, an alert will be sent to the user.
    '''

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()

    def run(self):
        self._stop_event.clear()
        logger = logging.getLogger(__name__)

        timeChecked = 0
        while True:
            time.sleep(5)

            if self._stop_event.is_set():
                break

            if timeChecked >= 3:
                logger.error("RPI is not connecting to the logging server", extra={'errorID': 'loggingConnection'})
            else:
                logger.warning("RPI did not connect to the server. Waiting....", extra={'errorID': 'loggingConnection'})

            timeChecked += 1

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
        logger.info("Got a connection from {}".format(self.client_address), extra={'errorID': 'loggingConnection'})

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
            except (NetworkError, ConnectionResetError):
                logger.warning("Network error. Did the client close the connection?",
                               extra={'errorID': 'loggingConnection'})
                connected = False
            except:
                logger.exception("Error while receiving log from client", extra={'errorID': 'loggingConnection'})
                connected = False

        logConnector = LogRecordConnector()
        logConnector.start()  # Monitor for connection and send alert to user if necessary

    def handle_record(self, record):
        logger = logging.getLogger(record.name)
        if record.name.startswith('sensorlog') and len(
                logger.handlers) == 0:  # Check if we are logging to a sensor and that this sensor has a handler
            self.create_sensorlog_handler(record.name)

        logger.handle(record)

    @staticmethod
    def create_sensorlog_handler(name):
        logging.getLogger(__name__).debug(f"Adding handler {name} for sensor logging")
        sensorlogger = logging.getLogger(name)

        splitName = name.split('.')

        csvHandler = MakeFileHandler('laptop', 'sensor', splitName[1], 'csv')
        csvHandler.setFormatter(CSVFormatter())
        sensorlogger.addHandler(csvHandler)
        sensorlogger.setLevel(logging.INFO)


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
