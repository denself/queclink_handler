import csv
import os
import datetime

from settings import settings
from hot_redis.types import HotClient as PatchedRedis
settings['redis_conn'] = redis_conn = PatchedRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB)

import socket
import contextlib
import argparse
import functools
import signal
from tornado import ioloop, netutil, process, gen, iostream
from session import TerminalSession
from conn import QueclinkConnection
from logger import gen_log


@contextlib.contextmanager
def handle_conn_error():
    try:
        yield
    except Exception, e:
        raise e


class RawServer(object):

    def __init__(self, io_loop=None, max_buffer_size=None, **kwargs):
        self.io_loop = io_loop
        self._sockets = {}      # fd -> socket object
        self._pending_sockets = []
        self._started = False
        self.ipaddr = kwargs.get('ipaddr', '0.0.0.0')
        self.port = kwargs.get('port')
        self.max_buffer_size = max_buffer_size

    def listen(self, port, address="", backlog=128, family=0):
        r"""Starts accepting connections on the given port."""
        sockets = netutil.bind_sockets(port, address=address,
                                       family=family, backlog=backlog)

        def f(conn, addr):
            self.io_loop.add_future(
                self.on_connect(conn, addr),
                lambda future: future.result())

        self.add_sockets(sockets, callback=f)

    def add_sockets(self, sockets, callback=None):
        r"""Makes this server start accepting connections on the given
        sockets.

        The `sockets` parameter is a list of socket objects such as
        those returned by `tornado.netutil.bind_sockets`"""

        if self.io_loop is None:
            self.io_loop = ioloop.IOLoop.current()
        for sock in sockets:
            self._sockets[sock.fileno()] = sock
            netutil.add_accept_handler(sock, callback, io_loop=self.io_loop)

    def add_socket(self, socket):
        self.add_sockets([socket])

    def bind(self, port, address=None, family=socket.AF_UNSPEC, backlog=128):
        r"""Binds this server to the given port on the given address.
        To start the server call `start`. If you want to run this
        server in a single process, you can call `listen` as a
        shortcut to the sequence of `bind` and `start` calls."""
        sockets = netutil.bind_sockets(port,
                                       address=address,
                                       family=family,
                                       backlog=backlog)
        if self._started:
            self.add_sockets(sockets)
        else:
            self._pending_sockets.extend(sockets)

    def start(self, num_processes=1):
        r"""Starts the server in IOLoop."""
        assert not self._started
        self._started = True
        if num_processes != 1:
            process.fork_processes(num_processes)
        sockets, self._pending_sockets = self._pending_sockets, []
        self.add_sockets(sockets)

    def stop(self):
        for fd, sock in self._sockets.items():
            self.io_loop.remove_handler(fd)
            sock.close()

    @gen.coroutine
    def on_connect(self, socket, address):
        yield self.handle_stream(socket, address)


class QueclinkServer(RawServer):

    def __init__(self, *a, **kw):
        super(QueclinkServer, self).__init__(*a, **kw)
        self.dongles = {}
        self.io_loop.add_future(self.init_workflow(),
                                lambda future: future.result())

    @gen.coroutine
    def on_connect(self, sock, address):
        super(QueclinkServer, self).on_connect(sock, address)
        stream = iostream.IOStream(sock, io_loop=self.io_loop,
                                   max_buffer_size=self.max_buffer_size)
        yield self.create_session(stream)

    @gen.coroutine
    def create_session(self, stream):
        session = TerminalSession(
            server=self,
            conn=QueclinkConnection,
            stream=stream,
            io_loop=self.io_loop)
        unique_id = yield session.open()
        if unique_id in self.dongles:
            sess = self.dongles.pop(unique_id)
            sess.close()
            sess = None
            # TODO. warning
        self.dongles[unique_id] = session

    @gen.coroutine
    def init_workflow(self):
        self.io_loop.add_future(self._command_watchdog(),
                                lambda future: future.result())

    @gen.coroutine
    def _command_watchdog(self):
        path = os.path.join('/tmp', 'queclink_commands')
        while True:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        f_csv = csv.reader(f)
                        for imei, msg in f_csv:
                            self.send_command(imei, msg)
                    os.remove(path)
                except Exception as ex:
                    gen_log.warning("Error during sending command %s", ex)

            yield gen.Task(self.io_loop.add_timeout, datetime.timedelta(seconds=1))

    def close_session(self, unique_id):
        self.dongles.pop(unique_id, None)

    def send_command(self, imei, msg):
        session = self.dongles.get(imei)
        if session:
            callback = lambda *args, **kwars: gen_log.info('SENT MESSAGE TO %s: %s', imei, msg)
            session.stream.write(msg, callback)
        else:
            gen_log.info('NO SESSION WITH IMEI %s', imei)


def handle_stop(io_loop, obd_server, signum, stack):
    r"""Properly kills the process by interrupting it first."""
    obd_server.stop()
    io_loop.stop()
    io_loop.close()
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    os.kill(os.getpid(), signal.SIGTERM)


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.instance()
    port = int(os.getenv('VCAP_APP_PORT', 9002))
    server = QueclinkServer(io_loop=io_loop, ipaddr='0.0.0.0',
                            port=port)
    server.listen(port)
    # register signal handlers
    handle_stop = functools.partial(handle_stop, io_loop, server)
    signal.signal(signal.SIGTERM, handle_stop)
    gen_log.info("Queclink Server is UP.")
    io_loop.start()



"""+RESP:GTOBD,1F0106,864251020002568,,gv500,0,70FFFF,,1,11814,983A8140,836,0,88,Inf,,1,0,1,0300,12,27,,0,0.0,316,843.0,76.862894,43.226609,20141120134941,0401,0001,08DE,9707,00,0.0,20141120194942,4DA1$"""
