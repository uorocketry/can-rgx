import logging
import random
import time


class ErrorManager:
    """
    Class to help simplify the error logging and management

    The main feature of this class is that errors and warning are kept track of and will not be logged again until they
    are 'resolved'. The main use of this is to avoid spamming the laptop with a lot of the same error messages. Other
    features are supported like only sending allow sending an error again after a set amount of time passed.
    """

    def __init__(self, logger_name, debounce_time=0):
        """
        :param logger_name: The name under which the logger should be created
        :param debounce_time: Specifies the number of seconds to wait before allowing a message with the same
        error_id to be sent again, even if it has not been resolved. If this is set to 0, this functionality is
        disabled, i.e. the error must be solved before being allowed to be sent again.
        """

        # Stores the raised errors. The dictionary keys are the error_id, and the values are the last time the error was
        # raised
        self.errors = dict()

        self.logger = logging.getLogger(logger_name)
        self.debounce_time = debounce_time

        # Append this number to the error_id in the functions bellow.
        # This way, different error managers can use the same error_id and not have a collision
        self.id_append = str(random.randint(0, 100000))

    def __allow_logging(self, error_id):
        """
        Performs some checks to see if we should allow this error to be logged. If needed, it will also add the error_id
        to the self.errors to keep track of it.
        :param error_id: The unique id of the error
        :return: If error_id was already raised
        """
        if error_id not in self.errors:
            self.errors[error_id] = time.time()
            return True
        elif self.debounce_time != 0 and (time.time() - self.errors[error_id]) >= self.debounce_time:
            self.errors[error_id] = time.time()
            return True

        return False

    def error(self, message, error_id):
        """
        Logs an error. Multiple call to this function or warning() with the same error_id will only log the error again
        if the debounce_time is not 0. Resolving the error by calling resolve() resets the error state, i.e.
        calling this function again will resend the error.
        :param message: A simple message describing the error
        :param error_id: A unique id to identify this error
        """
        if self.__allow_logging(error_id):
            self.logger.error(message, extra={'errorID': error_id + self.id_append})

    def warning(self, message, error_id):
        """
        Logs an warning. Multiple call to this function or error() with the same error_id will only log the error
        again if the debounce_time is not 0. Resolving the error by calling resolve() resets the error state, i.e.
        calling this function again will resend the error.
        :param message: A simple message describing the error
        :param error_id: A unique id to identify this error
        """
        if self.__allow_logging(error_id):
            self.logger.warning(message, extra={'errorID': error_id + self.id_append})

    def resolve(self, message, error_id, always_send=True):
        """
        Marks an error as resolved. The message is sent as an informational message.
        :param message: A simple message describing the resolved error
        :param error_id: A unique id to identify this error
        :param always_send: If True, the message will be sent even if no error have been raised before
        """
        if error_id in self.errors:
            self.errors.pop(error_id)
            logging.info(message, extra={'errorID': error_id + self.id_append})
        elif always_send:
            logging.info(message, extra={'errorID': error_id + self.id_append})
