import logging.handlers
import pickle
import struct

class LoggingSocketHandler(logging.handlers.SocketHandler):
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
        d['msg'] = record.msg #This line has been changed
        d['args'] = None
        d['exc_info'] = None
        # Issue #25685: delete 'message' if present: redundant with 'msg'
        d.pop('message', None)
        s = pickle.dumps(d, 1)
        slen = struct.pack(">L", len(s))
        return slen + s