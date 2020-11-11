import logging
import random
import time


class ErrorData:
    def __init__(self, error_level):
        self.first_raised = time.time()
        self.last_raised = time.time()
        self.error_level = error_level


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

        # Stores the raised errors. The dictionary keys are the error_id, and the values is an object of type ErrorData
        self.errors = dict()

        self.logger = logging.getLogger(logger_name)
        self.debounce_time = debounce_time

        # Append this number to the error_id in the functions bellow.
        # This way, different error managers can use the same error_id and not have a collision
        self.id_append = str(random.randint(0, 100000))

    def __allow_logging(self, error_id):
        """
        Performs some checks to see if we should allow this error to be logged.
        :param error_id: The unique id of the error
        :return: If error_id was already raised
        """
        if error_id not in self.errors:
            return True
        elif self.debounce_time != 0 and (time.time() - self.errors[error_id].last_raised) >= self.debounce_time:
            return True

        return False

    def __send_error(self, message, error_id, error_level):
        if error_id not in self.errors:
            self.errors[error_id] = ErrorData(error_level)
        else:
            self.errors[error_id].error_level = error_level
            self.errors[error_id].last_raised = time.time()

        if error_level == logging.WARNING:
            self.logger.warning(message, extra={'errorID': error_id + self.id_append})
        else:
            self.logger.error(message, extra={'errorID': error_id + self.id_append})

    def escalate(self, message, error_id, seconds_between_escalation=10):
        """
        Logs an error. First time, the message is sent as a warning. Calling the function again after the specified
        seconds_between_escalation will resend the message as an error. If debounce_time is 0, calling this function any
        other times will do nothing. If debounce_time is greater than 0, the message will be allowed to be sent again.

        Resolving the error anytime during this process will reset the error state.

        Using this function along with error() and warning() with the same error_id will result in undefined behavior.
        :param message: A simple message describing the error
        :param error_id: A unique id to identify this error
        :param seconds_between_escalation: The number of seconds before escalating this error
        :return:
        """

        if error_id not in self.errors:
            self.__send_error(message, error_id, logging.WARNING)
        elif self.errors[error_id].error_level == logging.WARNING \
                and (time.time() - self.errors[error_id].first_raised) >= seconds_between_escalation:
            self.__send_error(message, error_id, logging.ERROR)
        elif (time.time() - self.errors[error_id].last_raised) >= self.debounce_time:
            self.__send_error(message, error_id, self.errors[error_id].error_level)

    def error(self, message, error_id):
        """
        Logs an error. Multiple call to this function or warning() with the same error_id will only log the error again
        if the debounce_time is not 0. Resolving the error by calling resolve() resets the error state, i.e.
        calling this function again will resend the error.
        :param message: A simple message describing the error
        :param error_id: A unique id to identify this error
        """
        if self.__allow_logging(error_id):
            self.__send_error(message, error_id, logging.ERROR)

    def warning(self, message, error_id):
        """
        Logs an warning. Multiple call to this function or error() with the same error_id will only log the error
        again if the debounce_time is not 0. Resolving the error by calling resolve() resets the error state, i.e.
        calling this function again will resend the error.
        :param message: A simple message describing the error
        :param error_id: A unique id to identify this error
        """
        if self.__allow_logging(error_id):
            self.__send_error(message, error_id, logging.WARNING)

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
