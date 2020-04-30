import json
import logging, logging.handlers

from shared.network.requesttypes import RequestTypes
from rpi.network.bufferedsockethandler import BufferedSocketHandler

def process_message(json_string, client_adr):
    logger = logging.getLogger(__name__)

    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        logger.error("Cannot decode JSON string")
        return

    if data['type'] == RequestTypes.PING:
        logger.debug("Received a ping from {}".format(client_adr[0]))
    else:
        logger.error("Received an unknown message type")
