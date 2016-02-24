# Copyright 2016 Symantec, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import traceback
import zmq
from daoagent import log

RCV_TIMEOUT = 2000
SEND_TIMEOUT = 5000

context = zmq.Context()
logger = log.get_logger(__name__)


class ZMQSocket(object):

    def __init__(self, sock_type):
        self.sock_type = sock_type
        self.sock = None

    def __enter__(self):
        self.sock = context.socket(self.sock_type)
        self.sock.setsockopt(zmq.LINGER, SEND_TIMEOUT)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sock is not None:
            self.sock.close()

    def connect(self, connect_url):
        self.sock.connect(connect_url)

    def bind_random(self, reply_addr):
        reply_port = self.sock.bind_to_random_port(reply_addr)
        return ':'.join((reply_addr, str(reply_port)))

    def recv_pyobj(self):
        if self.sock.poll(RCV_TIMEOUT):
            return self.sock.recv_pyobj()
        else:
            raise RuntimeWarning('RCV timeout')


class RPCApi(object):

    def __init__(self, connect_url, reply_addr=None):
        self.connect_url = connect_url
        self.reply_addr = reply_addr

    def call(self, func, *args, **kwargs):
        with ZMQSocket(zmq.PUSH) as push:
            with ZMQSocket(zmq.PULL) as pull:
                push.connect(self.connect_url)
                reply_url = pull.bind_random(self.reply_addr)
                push.sock.send_pyobj({'reply_addr': reply_url,
                                      'function': func,
                                      'args': args,
                                      'kwargs': kwargs})
                return pull.recv_pyobj()

    def send(self, func, *args, **kwargs):
        with ZMQSocket(zmq.PUSH) as push:
            push.connect(self.connect_url)
            push.sock.send_pyobj({'function': func,
                                  'args': args,
                                  'kwargs': kwargs})


class RPCServer(object):
    def __init__(self, bind_url):
        self.socket = context.socket(zmq.PULL)
        self.socket.bind(bind_url)

    def do_main(self):
        while True:
            try:
                logger.debug('Waiting RPC request')
                request = self.socket.recv_pyobj()
                try:
                    reply_addr = request.get('reply_addr', None)
                    func_name = request['function']
                    args = request['args']
                    kwargs = request['kwargs']
                    logger.debug('Spawning new thread for %s', func_name)
                    self._call(reply_addr, func_name, args, kwargs)
                except IndexError:
                    logger.warning(traceback.format_exc())
            except Exception:
                logger.warning(traceback.format_exc())

    def _call(self, reply_addr, func_name, args, kwargs):
        try:
            logger.debug('Request is: %r', repr(locals()))
            response = getattr(self, func_name)(*args, **kwargs)
            logger.debug('Response is: %r', repr(response))
        except Exception, exc:
            response = exc
            logger.warning(traceback.format_exc())

        if reply_addr is not None:
            with ZMQSocket(zmq.PUSH) as socket:
                socket.connect(reply_addr)
                socket.sock.send_pyobj(response)
