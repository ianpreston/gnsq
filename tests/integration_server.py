import random
import time
import shutil
import subprocess
import tempfile
import os.path
import urllib3


class IntegrationNsqdServer(object):
    tls_cert = os.path.join(os.path.dirname(__file__), 'cert.pem')
    tls_key = os.path.join(os.path.dirname(__file__), 'key.pem')
    http = urllib3.PoolManager()

    def __init__(self, address=None, tcp_port=None, http_port=None):
        if address is None:
            address = '127.0.0.1'

        if tcp_port is None:
            tcp_port = random.randint(10000, 65535)
            tcp_port = 1234

        if http_port is None:
            http_port = tcp_port + 1

        self.address = address
        self.tcp_port = tcp_port
        self.http_port = http_port
        self.data_path = tempfile.mkdtemp()

    @property
    def tcp_address(self):
        return '%s:%d' % (self.address, self.tcp_port)

    @property
    def http_address(self):
        return '%s:%d' % (self.address, self.http_port)

    def is_running(self):
        try:
            url = 'http://%s/ping' % self.http_address
            return self.http.request('GET', url).data == 'OK'
        except urllib3.exceptions.HTTPError:
            return False

    def wait(self):
        for attempt in xrange(10):
            if self.is_running():
                return
            time.sleep(0.01 * pow(2, attempt))
        raise RuntimeError('unable to start nsqd')

    def cmd(self):
        return [
            'nsqd',
            '--tcp-address', self.tcp_address,
            '--http-address', self.http_address,
            '--data-path', self.data_path,
            '--tls-cert', self.tls_cert,
            '--tls-key', self.tls_key,
        ]

    def __enter__(self):
        self.nsqd = subprocess.Popen(self.cmd())
        self.wait()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.nsqd.terminate()
        self.nsqd.wait()
        shutil.rmtree(self.data_path)
