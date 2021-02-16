import logging.handlers
import pickle
import struct
from collections import deque


class BufferedSocketHandler(logging.handlers.SocketHandler):
    def __init__(self, host, port):
        super().__init__(host, port)

        self.buffer = deque(maxlen=1000)  # TODO: Review if this maximum length is the ideal one

    def emit(self, record):
        """
        This method is called when the handler should emit the record. By default,
        SocketHandler will silently drop a message if it cannot send it. Because this
        is not desired in our case, we will use a queue that will act as a buffer if
        the message is not sent
        """
        self.buffer.append(record)
        while len(self.buffer) != 0:
            nextRecord = self.buffer.popleft()

            super().emit(nextRecord)

            if self.sock is None:  # If we failed to send the record
                self.buffer.appendleft(nextRecord)
                break

    def makePickle(self, record):
        """
        The following code is copied from the SocketHandler implementation.
        One line is changed to prevent all messages from being converted to strings.
        """
        ei = record.exc_info
        if ei:
            # just to get traceback text into record.exc_text ...
            dummy = self.format(record)
        # See issue #14436: If msg or args are objects, they may not be
        # available on the receiving end. So we convert the msg % args
        # to a string, save it as msg and zap the args.
        d = dict(record.__dict__)
        d['msg'] = record.msg  # This line has been changed
        d['args'] = None
        d['exc_info'] = None
        # Issue #25685: delete 'message' if present: redundant with 'msg'
        d.pop('message', None)
        s = pickle.dumps(d, 1)
        slen = struct.pack(">L", len(s))
        return slen + s
