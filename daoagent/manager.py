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
import socket
import re
import time
import traceback
from daoagent import log
from daoagent import rpc

logger = log.get_logger()
bind_url = 'tcp://0.0.0.0:5555'


class Manager(rpc.RPCServer):
    def __init__(self):
        super(Manager, self).__init__(bind_url)


    @staticmethod
    def validate(server_dict, code):
        g_dict = {'server': server_dict, 'RESULT': None,
                  '__name__': '__main__'}
        code = compile(code, '/tmp/validation_script.pyc', 'exec')
        exec(code, g_dict)
        return g_dict['RESULT']

    @staticmethod
    def _get_local_ip(worker_url):
        ip, port = re.findall('[a-z]://+([0-9,\.]+):([0-9]+)', worker_url)[0]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.connect((ip, int(port)))
            return s.getsockname()[0]
        finally:
            s.close()


def run():
    logger.info('Started')
    try:
        with open('/tmp/started_%s' % time.time(), 'w'):
            pass
        manager = Manager()
        manager.do_main()
    except:
        logger.warning(traceback.format_exc())
        raise
