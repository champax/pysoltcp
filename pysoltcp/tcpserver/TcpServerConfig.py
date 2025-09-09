"""
# -*- coding: utf-8 -*-
# ===============================================================================
#
# Copyright (C) 2013/2025 Laurent Labatut / Laurent Champagnac
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
# ===============================================================================
"""

import logging

from pysolbase.FileUtility import FileUtility
from pysolbase.SolBase import SolBase

from pysoltcp.tcpserver.basefactory.TcpServerClientContextAbstractFactory import TcpServerClientContextAbstractFactory
from pysoltcp.tcpserver.clientcontext.TcpServerClientContextFactory import TcpServerClientContextFactory

SolBase.logging_init()
logger = logging.getLogger(__name__)


class TcpServerConfig(object):
    """
    tcpserver configuration.
    If ssl is NOT enable, it is better that calls to sslCertificate/ssl_key_file should not happen.
    """

    def __init__(self):
        """
        Constructor.
        """

        logger.debug("TcpServerConfig : Constructor called")

        # Default
        self._auto_start = False
        self._listen_addr = None
        self._listen_port = None
        self._client_factory = None
        self.client_factory = TcpServerClientContextFactory()

        # Ssl
        self._ssl_enable = False
        self._ssl_key_file = None
        self._ssl_certificate_file = None
        self._ssl_handshake_timeout_ms = 10000

        # Stop behavior
        self._onstop_callclient_stopsynch = False

        # Forking
        self._child_process_count = 0

        # Debug
        self._debug_waitinssl_ms = None

        # Socket control : Absolute default = 7 days (x 24 hours, x60 min, x60 sec, x1000 for ms)
        self._socket_absolute_timeout_ms = 7 * 24 * 60 * 60 * 1000

        # Socket control : Relative default = 1 days (x 24 hours, x60 min, x60 sec, x1000 for ms)
        self._socket_relative_timeout_ms = 1 * 24 * 60 * 60 * 1000

        # Socket control : minimal interval between 2 check = 60 sec
        self._socket_min_check_interval_ms = 60000

        # Timeout while stopping client
        self._stop_client_timeout_ms = 10000

        # Timeout while stopping server
        self._stop_server_timeout_ms = 30000

    def _set_client_factory(self, client_factory):
        """
        Setter. Raise exception if a problem occurs.
        :param client_factory : must be an instance of the factory, not the class itself.
        :type client_factory: pysoltcp.tcpserver.basefactory.TcpServerClientContextAbstractFactory.TcpServerClientContextAbstractFactory

        """
        if client_factory is None:
            logger.error("client_factory none")
            raise Exception("client_factory none")
        elif not isinstance(client_factory, TcpServerClientContextAbstractFactory):
            logger.error("client_factory is not a TcpServerClientContextAbstractFactory")
            raise Exception("client_factory is not a TcpServerClientContextAbstractFactory")
        else:
            self._client_factory = client_factory

    def _set_listen_addr(self, listen_addr):
        """
        Setter. Raise exception if a problem occurs.
        :param listen_addr: The listen address.
        :type listen_addr: str
        """

        self._listen_addr = listen_addr

    def _set_listen_port(self, listen_port):
        """
        Setter. Raise exception if a problem occurs.
        :param listen_port: The listen port.
        :type listen_port: int
        """

        listen_port = SolBase.to_int(listen_port)

        if not SolBase.is_int(listen_port):
            logger.error("not a int, class=%s", SolBase.get_classname(listen_port))
            raise Exception("not a int")
        elif listen_port == 0:
            logger.warning("newPort==0")
            raise Exception("newPort==0")
        else:
            self._listen_port = listen_port

    def _set_ssl_handshake_timeout_ms(self, ms):
        """
        Setter. Raise exception if a problem occurs.
        :param ms: Time out in ms.
        :type ms: int
        """
        cms = SolBase.to_int(ms)

        if not SolBase.is_int(cms):
            logger.error("not a int, class=%s", SolBase.get_classname(cms))
            raise Exception("not a int")
        else:
            self._ssl_handshake_timeout_ms = cms

    def _set_stop_client_timeout_ms(self, ms):
        """
        Setter. Raise exception if a problem occurs.
        :param ms: Time out in ms.
        :type ms: int
        """

        cms = SolBase.to_int(ms)

        if not SolBase.is_int(cms):
            logger.error("not a int, class=%s", SolBase.get_classname(cms))
            raise Exception("not a int")
        else:
            self._stop_client_timeout_ms = cms

    def _set_stop_server_timeout_ms(self, ms):
        """
        Setter. Raise exception if a problem occurs.
        :param ms: Time out in ms.
        :type ms: int
        """

        cms = SolBase.to_int(ms)
        if not SolBase.is_int(cms):
            logger.error("not a int, class=%s", SolBase.get_classname(cms))
            raise Exception("not a int")
        else:
            self._stop_server_timeout_ms = cms

    def _set_child_process_count(self, cpc):
        """
        Setter. Raise exception if a problem occurs.
        :param cpc: The number of child process count. If zero, no fork is performed (default).
        :type cpc: int
        """

        child_process_count = SolBase.to_int(cpc)

        if not SolBase.is_int(child_process_count):
            logger.error("not a int, class=%s", SolBase.get_classname(child_process_count))
            raise Exception("not a int")
        elif child_process_count < 0:
            logger.warning("child_process_count<0")
            raise Exception("child_process_count<0")
        else:
            self._child_process_count = child_process_count

    def _set_auto_start(self, b):
        """
        Getter
        :param b: A boolean.
        :type b: bool
        """

        mb = SolBase.to_bool(b)

        if not SolBase.is_bool(mb):
            logger.error("not a boolean, class=%s", SolBase.get_classname(mb))
            raise Exception("not a boolean")
        else:
            self._auto_start = mb

    def _set_onstop_call_client_stopsynch(self, b):
        """
        Getter
        :param b: A boolean.
        :type b: bool
        """

        mb = SolBase.to_bool(b)

        if not SolBase.is_bool(mb):
            logger.error("not a boolean, class=%s", SolBase.get_classname(mb))
            raise Exception("not a boolean")
        else:
            self._onstop_callclient_stopsynch = mb

    def _set_ssl_enable(self, b):
        """
        Enable or disable ssl.
        :param b: Boolean.
        :type b: bool
        """

        is_enable = SolBase.to_bool(b)

        if not SolBase.is_bool(is_enable):
            logger.error("not a boolean, class=%s", SolBase.get_classname(is_enable))
            raise Exception("not a boolean")
        else:
            self._ssl_enable = is_enable

    def _set_ssl_keyfile(self, key_file):
        """
        Set the ssl key file. Raise exception upon error.
        :param key_file: A valid key file. Must exist and be accessible.
        :type key_file: str
        :return: True upon success, false otherwise.
        :rtype bool
        """
        # Check
        if key_file is None or len(key_file) == 0:
            self._ssl_key_file = ""
            return

        if not FileUtility.is_file_exist(key_file):
            logger.warning("key_file do not exist or is not accessible, key_file=%s", key_file)

        # Set
        self._ssl_key_file = key_file

    def _set_ssl_certificate_file(self, cert_file):
        """
        Set the ssl certificate file. Raise exception upon error.
        :param cert_file: A valid certificate file. Must exist and be accessible.
        :type cert_file: str
        """

        # Check
        if cert_file is None or len(cert_file) == 0:
            self._ssl_certificate_file = ""
            return

        # Check
        if not FileUtility.is_file_exist(cert_file):
            logger.warning("cert_file do not exist or is not accessible, cert_file=%s", cert_file)

        # Set
        self._ssl_certificate_file = cert_file

    def _get_client_factory(self):
        """
        Getter
        :return The client factory.
        :rtype pysoltcp.tcpserver.basefactory.TcpServerClientContextAbstractFactory.TcpServerClientContextAbstractFactory
        """
        return self._client_factory

    def _get_listen_port(self):
        """
        Getter
        :return The listen port.
        :rtype int
        """
        return self._listen_port

    def _get_ssl_handshake_timeout_ms(self):
        """
        Getter
        :return The value.
        :rtype int
        """
        return self._ssl_handshake_timeout_ms

    def _get_stop_client_timeout_ms(self):
        """
        Getter
        :return The value.
        :rtype int
        """
        return self._stop_client_timeout_ms

    def _get_stop_server_timeout_ms(self):
        """
        Getter
        :return The value.
        :rtype int
        """
        return self._stop_server_timeout_ms

    def _get_child_process_count(self):
        """
        Getter
        :return The number of child process count.
        :rtype int
        """
        return self._child_process_count

    def _get_auto_start(self):
        """
        Getter
        :return The auto start boolean
        :rtype bool
        """
        return self._auto_start

    def _get_onstop_call_client_stopsynch(self):
        """
        Getter
        :return bool
        :rtype bool
        """
        return self._onstop_callclient_stopsynch

    def _get_listen_addr(self):
        """
        Getter
        :return The listen address.
        :rtype str
        """
        return self._listen_addr

    def _get_ssl_enable(self):
        """
        Getter.
        :return: A boolean.
        :rtype bool
        """
        return self._ssl_enable

    def _get_ssl_keyfile(self):
        """
        Getter.
        :return: A string or None
        :rtype None,str
        """

        return self._ssl_key_file

    def _get_ssl_certificate_file(self):
        """
        Getter.
        :return: A string or None
        :rtype None,str
        """

        return self._ssl_certificate_file

    def _get_socket_absolute_timeout_ms(self):
        """
        Getter
        :return Timeout in ms.
        :rtype int
        """
        return self._socket_absolute_timeout_ms

    def _get_socket_relative_timeout_ms(self):
        """
        Getter
        :return Timeout in ms.
        :rtype int
        """
        return self._socket_relative_timeout_ms

    def _get_socket_min_checkinterval_ms(self):
        """
        Getter
        :return Timeout in ms.
        :rtype int
        """
        return self._socket_min_check_interval_ms

    def _set_socket_min_checkinterval_ms(self, ms):
        """
        Setter. Raise exception if a problem occurs.
        :param ms: Timeout in ms.
        :type ms: int
        """

        cms = SolBase.to_int(ms)

        if not SolBase.is_int(cms):
            logger.error("not a int, class=%s", SolBase.get_classname(cms))
            raise Exception("not a int")
        else:
            self._socket_min_check_interval_ms = cms

    def _set_socket_absolute_timeout_ms(self, ms):
        """
        Setter. Raise exception if a problem occurs.
        :param ms: Timeout in ms.
        :type ms: int
        """

        cms = SolBase.to_int(ms)

        if not SolBase.is_int(cms):
            logger.error("not a int, class=%s", SolBase.get_classname(cms))
            raise Exception("not a int")
        else:
            self._socket_absolute_timeout_ms = cms

    def _set_socket_relative_timeout_ms(self, ms):
        """
        Setter. Raise exception if a problem occurs.
        :param ms: Timeout in ms.
        :type ms: int
        """

        cms = SolBase.to_int(ms)

        if not SolBase.is_int(cms):
            logger.error("not a int, class=%s", SolBase.get_classname(cms))
            raise Exception("not a int")
        else:
            self._socket_relative_timeout_ms = cms

    # ========================
    # Properties - configs
    # ========================

    # Auto-start on ?
    auto_start = property(_get_auto_start, _set_auto_start)
    # Listen address
    listen_addr = property(_get_listen_addr, _set_listen_addr)
    # Listen port
    listen_port = property(_get_listen_port, _set_listen_port)
    # Client factory
    client_factory = property(_get_client_factory, _set_client_factory)
    # Ssl on ?
    ssl_enable = property(_get_ssl_enable, _set_ssl_enable)
    # Ssl on ?
    onstop_call_client_stopsynch = property(_get_onstop_call_client_stopsynch, _set_onstop_call_client_stopsynch)
    # Ssl key file
    ssl_key_file = property(_get_ssl_keyfile, _set_ssl_keyfile)
    # Ssl certificate file
    ssl_certificate_file = property(_get_ssl_certificate_file, _set_ssl_certificate_file)

    # ========================
    # Properties - tuning
    # ========================

    # Child process count
    child_process_count = property(_get_child_process_count, _set_child_process_count)
    # Timeout in ms allowed for SSL handshake
    ssl_handshake_timeout_ms = property(_get_ssl_handshake_timeout_ms, _set_ssl_handshake_timeout_ms)
    # Per socket : absolute socket time out in ms. If lt or eq to 0 : no limit.
    socket_absolute_timeout_ms = property(_get_socket_absolute_timeout_ms, _set_socket_absolute_timeout_ms)
    # Per socket : relative socket time out in ms. If lt or eq to 0 : no limit.
    socket_relative_timeout_ms = property(_get_socket_relative_timeout_ms, _set_socket_relative_timeout_ms)
    # Socket : Minimum check interval in ms.
    socket_min_checkinterval_ms = property(_get_socket_min_checkinterval_ms, _set_socket_min_checkinterval_ms)
    # Stop timeout ms
    stop_client_timeout_ms = property(_get_stop_client_timeout_ms, _set_stop_client_timeout_ms)
    # Stop timeout ms
    stop_server_timeout_ms = property(_get_stop_server_timeout_ms, _set_stop_server_timeout_ms)

    # ========================
    # Properties - DEBUG ONLY - NEVER USE THEM IN PRODUCTION
    # ========================

    def _set_debug_waitinsslms(self, value):
        """
        Setter for debug only.
        :param value: Value.
        :type value: int
        """
        self._debug_waitinssl_ms = value

    def _get_debug_waitinsslms(self):
        """
        Getter for debug only.
        :return: Value.
        :rtype int
        """
        return self._debug_waitinssl_ms

    debug_waitinsslms = property(_get_debug_waitinsslms, _set_debug_waitinsslms)
