import socket
from message import WireMessage
import logging


class AcceptConnection(object):

    """Facilitates creation of new socket when
       peers connect to an existing socket.
    """
    def __init__(self, parent, bind_to=6881):
        self.logger = logging.getLogger('bt.conn.AcceptConnection')
        self.parent = parent
        self.socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
                )
        self.socket.bind(('localhost', bind_to))
        self.socket.listen(5)

    def recv_msg(self, msg):
        msg_type, msg_contents = WireMessage.decode(msg)
        if msg_type == 'handshake':
            new_conn, addr = self.socket.accept()
            func = getattr(self.parent, msg_type)
            assert callable(func)
            func(new_conn, addr, msg_contents)
            return True
        raise Exception('Non-handshake message received.')

    def fileno(self):
        return self.socket.fileno()


class MsgConnection(object):

    """Helps receive, queue and send messages.
       Wraps socket.socket.
    """
    def __init__(self, parent, socket=None):
        self.parent = parent
        self._outbound = []
        if socket:
            self.socket = socket

    def mark_bad(self):
        self.parent.mark_bad()

    def connect(self, ip, port, timeout=2):
        self.ip = ip
        self.port = port
        """Connect to address:port via TCP
            and return a file descriptor
            representing the new connection.
        """
        self.socket = socket.create_connection((ip, port), timeout)

    def has_next_msg(self):
        return len(self._outbound) > 0

    def send_next_msg(self):
        """Send next msg in queue.
        """
        try:
            msg = self._outbound.pop()
        except IndexError:
            return False
        try:
            bytes_sent = self.socket.send(msg)
        except socket.error, e:
            err = 'Failed to send message to {}:{}. Msg was {}.'.format(
                    self.ip, self.port, repr(msg))
            self.logger.error(e)
            raise Exception(err)
        assert len(msg) == bytes_sent

    def recv_msg(self):
        """Receive all complete messages currently on wire.
        """
        buf = ""
        while True:
            try:
                msg = self.socket.recv(4096)
            except Exception, e:
                self.parent.mark_bad()
                self.logger.warning(
                        'recv() on {}:{}: {}'.format(
                            self.ip, self.port, e))
                #self.close()
                break
            else:
                if len(msg) == 0: break
                buf += msg
        if len(buf) == 0: return False
        messages = WireMessage.decode_all(buf)
        for msg in messages:
            func = getattr(self.parent, msg[0])
            assert callable(func)
            try:
                if msg[1]:
                    func(*msg[1])
                else:
                    func()
            except AttributeError, e:
                # Todo - make sure AttributeError actually relates to func()
                self.logger.error('Error: Invalid msg type {}'.format(msg[0]))
                raise Exception(e)
    def enqueue_msg(self, msg):
        self._outbound.append(msg)
    def close(self):
        self.parent.client.notify_closed(self._parent.peer_id)
        self.socket.close()
    def fileno(self):
        return self.socket.fileno()
