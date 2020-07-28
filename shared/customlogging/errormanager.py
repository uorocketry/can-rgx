import logging
import random


class ErrorManager:
    """
    Class to help simplify the error logging and management

    The main feature of this class is that errors and warning are kept track of and will not be logged again until they
    are 'resolved'. The main use of this is to avoid spamming the laptop with a lot of the same error messages.
    """

    def __init__(self, logger_name):
        """
        :param logger_name: The name under which the logger should be created
        """
        self.errors = set()
        self.logger = logging.getLogger(logger_name)

        # Append this number to the error_id in the functions bellow.
        # This way, different error managers can use the same error_id and not have a collision
        self.id_append = str(random.randint(0, 100000))

    def __check_error(self, error_id):
        """
        Checks if the error_id was already, and if not, track it by adding it to the self.errors set
        :param error_id: The unique id of the error
        :return: If error_id was already raised
        """
        if error_id not in self.errors:
            self.errors.add(error_id)
            return False

        return True

    def error(self, message, error_id):
        """
        Logs an error. Multiple call to this function or warning() with the same error_id will not log the error again
        until the error is resolved by calling the function resolve().
        :param message: A simple message describing the error
        :param error_id: A unique id to identify this error
        """
        if not self.__check_error(error_id):
            self.logger.error(message, extra={'errorID': error_id + self.id_append})

    def warning(self, message, error_id):
        """
        Logs an warning. Multiple call to this function or error() with the same error_id will not log the error again
        until the error is resolved by calling the function resolve().
        :param message: A simple message describing the error
        :param error_id: A unique id to identify this error
        """
        if not self.__check_error(error_id):
            self.logger.warning(message, extra={'errorID': error_id + self.id_append})

    def resolve(self, message, error_id, always_send=True):
        """
        Marks an error as resolved. The message is sent as an informational message.
        :param message: A simple message describing the resolved error
        :param error_id: A unique id to identify this error
        :param always_send: If True, the message will be sent even if no error have been raised before
        """
        if error_id in self.errors:
            self.errors.remove(error_id)
            logging.info(message, extra={'errorID': error_id + self.id_append})
        elif always_send:
            logging.info(message, extra={'errorID': error_id + self.id_append})
