import json
import logging

from shared.network.requesttypes import RequestTypes

def process_message(json_string, client_adr):
    logger = logging.getLogger(__name__)

    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        logger.error("Cannot decode JSON string")
        return

    if data['type'] == RequestTypes.CONNECTLOGGING:
        logger.info("Received a logging connection request from {}".format(client_adr[0]))
        connect_logging_to_client(client_adr)
    elif data['type'] == RequestTypes.PING:
        logger.debug("Received a ping from {}".format(client_adr[0]))
    else:
        logger.error("Received an unknown message type")



def connect_logging_to_client(client_adr):
    raise NotImplementedError()