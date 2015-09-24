import functools

from toro import JoinableQueue
from tornado.log import app_log
from tornado.concurrent import Future
from tornado import gen

from commons.async import schedule_at_loop
from protocol import QueclinkProtocol
import conf
from utils import generate_random_hex
from logger import gen_log
from commons.exceptions import MessageNotImplemented, StreamClosedError

CONNECTING = 0
OPEN = 1
CLOSING = 2
CLOSED = 3


class RTOManager(object):

    def __init__(self, *a, **kw):
        self.rto_cmds = {}
        super(RTOManager, self).__init__()

    def make_rto(self, body):
        r"""It makes real time request to current connection.
        It waits for ack, then waits for real response and returned
        the result back. Result could be any:
            log - depending on RTO
            exc - MessageNotImplemented
        Returns:
            future promise
        """

        def callback(promise, f_rto_ack):
            rto_ack = f_rto_ack.result()
            if isinstance(rto_ack, str) and rto_ack == conf.DISCONN_RESULT:
                return
            _f = self.rto_cmds[rto_ack.sub_cmd] = promise
            return _f

        f_rto_ack = self.exec_command(conf.COMMAND, conf.RTO_CMD, body)
        f_rto_response = Future()
        cb = functools.partial(callback, f_rto_response)
        self.io_loop.add_future(f_rto_ack, cb)
        return f_rto_response

    def is_pending_rto(self, header):
        r"""Determines whether this header is pending rto request."""
        if header in self.rto_cmds:
            return True
        return False

    def make_rto_response(self, log):
        r"""Make registered rto finished by setting response to future."""
        f = self.rto_cmds.pop(log.header)
        if f._done:
            return f
        if isinstance(log, Exception):
            f.set_exception(log)
        else:
            f.set_result(log.log)
        return f


class TerminalSession(RTOManager, QueclinkProtocol):

    r"""Base session implementation class.
    Session is shared object and low-level code for connection.

        Parameters
        ----------
            session_key - IMEI of device
    """

    STOP_FLAG = False

    def __init__(self, server, conn, stream, io_loop=None, *args, **kwargs):
        self.server = server
        self.stream = stream
        self.conn = conn(self,
                         main_server_ip=self.server.ipaddr,
                         main_server_port=self.server.port,)
        self.session_key = None

        self.state = CONNECTING
        self.io_loop = io_loop
        self.stream.set_close_callback(self.socket_closed)
        self.job_queue = JoinableQueue()
        self.registered_cmds = {}
        self.cnt_number = '0000'
        self.io_loop.add_future(self.init_workflow(),
                                lambda future: future.result())
        super(TerminalSession, self).__init__(*args, **kwargs)

    def is_open(self):
        return self.state == OPEN

    def is_closed(self):
        return self.state == CLOSED

    @gen.coroutine
    def open(self):
        """Opens the connect. According to the protocol,
        we should first configure the device and after than
        connection should be flagged as opened."""
        # unique_id = yield self.conn.configure()
        log = yield self.conn.verify_conn()
        unique_id = log.unique_id
        gen_log.info('CONNECTION OPENED WITH: %s' % unique_id)
        if unique_id:
            self.session_key = unique_id
            self.state = OPEN
            self.conn.on_open(unique_id)
            raise gen.Return(unique_id)
        raise gen.Return(conf.DISCONN_RESULT)

    @gen.coroutine
    def read_message(self):
        r"""Callbacks takes two arguments: binary data and job code."""
        if self.stream.closed():
            raise StreamClosedError("Stream is closed")
        message = yield gen.Task(self.stream.read_until, conf.END_SIGN)
        raise gen.Return(message)

    @gen.coroutine
    def terminal_message_flow(self, msg):
        r"""Sets message flow"""
        try:
            log, sack, from_buffer = super(
                TerminalSession, self).terminal_message_flow(msg)
        except MessageNotImplemented as e:  # silence exc
            gen_log.exception(e)
            return
        count_num = log.log.count_number
        if log.type == conf.ACK:
            if not log.header == conf.HEARTBEAT_ACK:
                self.unregister_command_on_ack(log.log)
            yield self.conn.on_ack(msg, log, sack)
        else:
            if self.is_pending_rto(log.header):
                self.make_rto_response(log)
            # bad accuracy of gps
            # may be warn by email our guys that gps accuracy is weak
            # skip message logic
            if log.header == conf.FIXED_REPORT:
                gps_accuracy = int(log.log.gps_accuracy)
                if not gps_accuracy:    # or (20 < gps_accuracy <= 50):
                    self.skip_message = True
                else:
                    self.skip_message = False
            if getattr(self, 'skip_message', False):
                gen_log.info("Hey, GPS ACCURACY IS BAD")
                return
            yield self.conn.on_report(msg, log, sack, from_buffer=from_buffer)
        if not self.session_key and hasattr(log.log, 'unique_id'):
            self.session_key = log.log.unique_id
            self.state = OPEN
        raise gen.Return(count_num)

    def exec_command(self, msg_tp, header, body):
        r"""Sends message to the end-point. Returns promiseable future."""
        if not msg_tp == conf.COMMAND:
            raise
        serial_number, cmd_future = self.register_command_for_ack()
        body.update({'serial_number': serial_number})
        self.send_message(self.build_cmd(header, **body))
        return cmd_future

    def send_message(self, msg):
        self.stream.write(msg)
        gen_log.info("SACK: %s", msg)

    def should_stop(self):
        return self.STOP_FLAG

    @gen.coroutine
    def init_workflow(self):
        schedule_at_loop(self.io_loop, self._tail_messagebus,
                         callback=self._handle_message_flow)
        schedule_at_loop(self.io_loop, self._tail_stream_buffer,
                         callback=self._handle_message_flow)

    @gen.coroutine
    def _tail_messagebus(self):

        def job_complete(f):
            self.cnt_number = f.result()

        while True:
            if self.should_stop():
                break
            message = yield self.job_queue.get()
            schedule_at_loop(self.io_loop, self.terminal_message_flow(message),
                             job_complete)
            self.job_queue.task_done()
            gen_log.info("INCOMING MSG: %s", message)

    @gen.coroutine
    def _tail_stream_buffer(self):
        while True:
            if self.should_stop():
                break
            message = yield self.read_message()
            yield self.job_queue.put(message)

    def _handle_message_flow(self, future):
        # some other errors that I do not know yet that can
        # lead to memory leaks due to file descriptor will no be closed
        try:
            future.result()
        except Exception as e:
            app_log.exception(e)
        finally:
            self.STOP_FLAG = True
            self.close()

    def register_command_for_ack(self):
        r"""Returns serial number and future promise"""
        serial_number = ''
        while not serial_number or serial_number in self.registered_cmds:
            serial_number = generate_random_hex()
        f = self.registered_cmds[serial_number] = Future()
        return serial_number, f

    def unregister_command_on_ack(self, log):
        serial_number = log.serial_number
        future = self.registered_cmds.pop(serial_number, None)
        if not future:
            return
        if future._done:
            return future
        if not isinstance(log, Exception):
            future.set_result(log)
        else:
            future.set_exception(log)

    def unregister_commands(self):
        if not self.is_open():
            for evt in self.registered_cmds.keys():
                f = self.registered_cmds.pop(evt)
                f.set_result(conf.DISCONN_RESULT)
            while self.registered_cmds:
                self.registered_cmds

    def socket_closed(self):
        self.state = CLOSING
        self.close()

    def close(self):
        self.unregister_commands()
        self.server.close_session(self.session_key)
        self.conn.on_close()
        self.stream.close()
        self.state = CLOSED
        gen_log.info("CONNECTION CLOSED: %s", self.session_key)
