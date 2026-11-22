# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read capped byte ranges of the authorized ESA 187 AIR1 original."""

from ftplib import FTP, FTP_TLS, all_errors
from netrc import netrc
import socket
import ssl
from time import monotonic


HOST = 'tpm-if.eo.esa.int'
REMOTE = '/lvl0/187/air1/air10706a.23o'
SOURCE_BYTES = 363_446_705
GIRAFE_REMOTE = '/lvl0/187/girafe/LOGXIO_06_07_2023 _01.Asc'
GIRAFE_SOURCE_BYTES = 1_860_304_779
MAXIMUM_BYTES = 1024*1024


def read_exact(connection, count, deadline):
    payload = bytearray()
    while len(payload) < count:
        remaining = deadline-monotonic()
        if remaining <= 0:
            raise TimeoutError('FTP range delivery deadline')
        connection.settimeout(remaining)
        block = connection.recv(min(65_536, count-len(payload)))
        if not block:
            raise ValueError('short FTP byte range')
        payload.extend(block)
    return bytes(payload)


class _ImplicitFTPS(FTP_TLS):
    def start(self):
        self.host = HOST
        connection = socket.create_connection((HOST, 990), timeout=self.timeout)
        try:
            self.sock = self.context.wrap_socket(connection, server_hostname=HOST)
        except OSError:
            connection.close()
            raise
        self.af = self.sock.family
        self.file = self.sock.makefile('r', encoding=self.encoding)
        self.welcome = self.getresp()

    def sendcmd(self, command):
        answer = super().sendcmd(command)
        if command.startswith('REST ') and not answer.startswith('350'):
            raise ValueError('FTP server did not acknowledge the exact restart command')
        return answer

    def ntransfercmd(self, cmd, rest=None):
        connection, size = FTP.ntransfercmd(self, cmd, rest)
        try:
            secure = self.context.wrap_socket(connection, server_hostname=self.host,
                                              session=self.sock.session)
        except OSError:
            connection.close()
            raise
        return secure, size


def read_esa_range(remote, source_bytes, offset, count, certificate, credentials):
    if (remote, source_bytes) not in ((REMOTE, SOURCE_BYTES), (GIRAFE_REMOTE, GIRAFE_SOURCE_BYTES)):
        raise ValueError('only an explicit opened ESA 187 source is eligible')
    if not 0 <= offset < offset+count <= source_bytes or count > MAXIMUM_BYTES:
        raise ValueError('bounded ESA 187 file span required')
    auth = netrc(str(credentials)).authenticators(HOST)
    if auth is None:
        raise ValueError('private authorization for the ESA archive is required')
    user, _, password = auth
    ssl_context = ssl.create_default_context(cafile=str(certificate))
    deadline = monotonic()+45.
    ftp = _ImplicitFTPS(context=ssl_context, timeout=15)
    try:
        ftp.start()
        ftp.login(user=user, passwd=password)
        ftp.prot_p()
        ftp.voidcmd('TYPE I')
        if ftp.size(remote) != source_bytes:
            raise ValueError('archived ESA source size changed')
        with ftp.transfercmd('RETR '+remote, rest=offset) as connection:
            return read_exact(connection, count, deadline)
    except all_errors:
        raise ValueError('authenticated ESA byte range failed during delivery') from None
    finally:
        ftp.close()


def read_air1_range(offset, count, certificate, credentials):
    return read_esa_range(REMOTE, SOURCE_BYTES, offset, count, certificate, credentials)
