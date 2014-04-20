# Copyright (C) 2014, Stefan Schwarzer

"""
Session factory factory (the two "factory" are intential :-) )
for ftputil.
"""

import ftplib

import ftputil.tool

try:
    import M2Crypto
    import M2Crypto.ftpslib
except ImportError:
    M2Crypto = None


def session_factory(base_class=ftplib.FTP, port=21, use_passive_mode=None,
                    encrypt_data_channel=None):
    """
    Create and return a session factory according to the keyword
    arguments.

    base_class: Base class to use for the session class (e. g.
    `ftplib.FTP_TLS` or `M2Crypto.ftpslib.FTP_TLS`, default is
    `ftplib.FTP`).

    port: Port number (integer) for the command channel (default 21).
    If you don't know what "command channel" means, use the default or
    use what the provider gave you as "the FTP port".

    use_passive_mode: If `True`, explicitly use passive mode. If
    `False`, explicitly don't use passive mode. If `None` (default),
    let the `base_class` decide whether it wants to use active or
    passive mode.

    encrypt_data_channel: If `True`, call the `prot_p` method of the
    base class. If `False` or `None` (`None` is the default), don't
    call the method.

    This function should work the base classes for `ftplib.FTP`,
    `ftplib.FTP_TLS` and `M2Crypto.ftpslib.FTP_TLS` with TLS security.
    Other base classes should work if they use the same API as
    `ftplib.FTP`.

    Usage example:

      my_session_factory = session_factory(
                             base_class=M2Crypto.ftpslib.FTP_TLS,
                             use_passive_mode=True,
                             encrypt_data_channel=True)
      with ftputil.FTPHost(host, user, password,
                           session_factory=my_session_factory) as host:
        ...
    """
    class Session(base_class):
        """Session factory class created by `session_factory`."""

        def __init__(self, host, user, password):
            base_class.__init__(self)
            self.connect(host, port)
            if self._use_m2crypto_ftpslib():
                self.auth_tls()
                self._fix_socket()
            self.login(user, password)
            if use_passive_mode is not None:
                self.set_pasv(use_passive_mode)
            if encrypt_data_channel:
                self.prot_p()

        def _use_m2crypto_ftpslib(self):
            """
            Return `True` if the base class to use is
            `M2Crypto.ftpslib.FTP_TLS`, else return `False`.
            """
            return (M2Crypto is not None and
                    issubclass(base_class, M2Crypto.ftpslib.FTP_TLS))

        def _fix_socket(self):
            """
            Change the socket object so that arguments to `sendall`
            are converted to byte strings before being used.

            See the ftputil ticket #78 for details:
            http://ftputil.sschwarzer.net/trac/ticket/78
            """
            original_sendall = self.sock.sendall
            # Bound method, therefore no `self` argument.
            def sendall(data):
                data = ftputil.tool.as_bytes(data)
                return original_sendall(data)
            self.sock.sendall = sendall

    return Session