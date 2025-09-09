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

# Logger
import logging

from pysolbase.SolBase import SolBase

SolBase.logging_init()
logger = logging.getLogger(__name__)


class TcpClientConfig(object):
    """
    Tcp client configuration.
    """

    def __init__(self):
        """
        Constructor.
        """

        # Default
        self._target_addr = None
        self._target_port = None

        # Ssl
        self._ssl_enable = False

        # Timeout
        self._timeout_ms = 10000

        # Debug logs
        self._debug_log = False

        # Socks5 proxy
        self._proxy_enable = False
        self._proxy_addr = None
        self._proxy_port = None

        # Tcp keep alive on by default
        self._tcp_keepalive_enabled = True
        self._tcp_keepalive_probes_senddelayms = 60000
        self._tcp_keepalive_probes_failedcount = 5
        self._tcp_keepalive_probes_sendintervalms = 60000

    def _set_targetaddr(self, target_addr):
        """
        Setter. Raise exception if a problem occurs.
        :param target_addr: The target address.
        :type target_addr: str
        """

        self._target_addr = target_addr

    def _get_targetaddr(self):
        """
        Getter
        :return: The target address.
        :rtype str
        """
        return self._target_addr

    def _set_target_port(self, target_port):
        """
        Setter. Raise exception if a problem occurs.
        :param target_port: The target port.
        :type target_port: int
        """
        if not SolBase.is_int(target_port):
            logger.error("TcpClientConfig : _set_target_port : not a int, class=%s", SolBase.get_classname(target_port))
            raise Exception("TcpClientConfig : _set_target_port : not a int")
        elif target_port == 0:
            logger.warning("TcpClientConfig : _set_target_port : newPort==0")
            raise Exception("TcpClientConfig : _set_target_port : newPort==0")
        else:
            self._target_port = target_port

    def _set_timeout_ms(self, ms):
        """
        Setter. Raise exception if a problem occurs.
        :param ms: The timeout in millis or None.
        :type ms: int,None
        """
        self._timeout_ms = ms

    def _get_target_port(self):
        """
        Getter
        :return The target port.
        :rtype int
        """
        return self._target_port

    def _set_ssl_enable(self, b):
        """
        Enable or disable ssl.
        :param b: bool.
        :type b: bool
        """
        self._ssl_enable = b

    def _set_debug_log(self, b):
        """
        Enable or disable debug log.
        :param b: bool.
        :type b: bool
        """
        self._debug_log = b

    def _get_ssl_enable(self):
        """
        Getter.
        :return: A boolean.
        :rtype bool
        """
        return self._ssl_enable

    def _get_timeout_ms(self):
        """
        Getter.
        :return: An integer or None.
        :rtype int,None
        """
        return self._timeout_ms

    def _get_debug_log(self):
        """
        Getter.
        :return: An integer or None.
        :rtype int,None
        """
        return self._debug_log

    def _set_proxy_addr(self, proxy_addr):
        """
        Setter. Raise exception if a problem occurs.
        :param proxy_addr: The proxy target address.
        :type proxy_addr: str
        """

        self._proxy_addr = proxy_addr

    def _get_proxy_addr(self):
        """
        Getter
        :return: The proxy target address.
        :rtype str
        """
        return self._proxy_addr

    def _set_proxy_port(self, proxy_port):
        """
        Setter. Raise exception if a problem occurs.
        :param proxy_port: The target proxy port.
        :type proxy_port: int
        """
        if not SolBase.is_int(proxy_port):
            logger.error("TcpClientConfig : _set_proxy_port : not a int, class=%s", SolBase.get_classname(proxy_port))
            raise Exception("TcpClientConfig : _set_proxy_port : not a int")
        elif proxy_port == 0:
            logger.warning("TcpClientConfig : _set_proxy_port : newPort==0")
            raise Exception("TcpClientConfig : _set_proxy_port : newPort==0")
        else:
            self._proxy_port = proxy_port

    def _get_proxy_port(self):
        """
        Getter
        :return The target port.
        :rtype int
        """
        return self._proxy_port

    def _set_proxy_enable(self, is_enable):
        """
        Enable or disable proxy.
        :param is_enable: Boolean.
        :type is_enable: bool
        """
        self._proxy_enable = is_enable

    def _get_proxy_enable(self):
        """
        Getter.
        :return: A boolean.
        :rtype bool
        """
        return self._proxy_enable

    # =======================
    # TCP KEEP ALIVE
    # =======================

    def _set_tcp_keepalive_enabled(self, is_enable):
        """
        Enable or disable tcp keep alive.
        :param is_enable: Boolean.
        :type is_enable: bool
        :return: Nothing.
        """
        self._tcp_keepalive_enabled = is_enable

    def _get_tcp_keepalive_enabled(self):
        """
        Getter.
        :return: A boolean.
        :rtype bool
        """
        return self._tcp_keepalive_enabled

    def _set_tcp_keepalive_probes_senddelayms(self, value):
        """
        Setter. Raise exception if a problem occurs.
        :param value: Value.
        :type value: int
        
        """
        if not SolBase.is_int(value):
            logger.error("TcpClientConfig : _set_tcp_keepalive_probes_senddelayms : not a int, class=%s", SolBase.get_classname(value))
            raise Exception("TcpClientConfig : _set_tcp_keepalive_probes_senddelayms : not a int")
        elif value == 0:
            logger.warning("TcpClientConfig : _set_tcp_keepalive_probes_senddelayms : newPort==0")
            raise Exception("TcpClientConfig : _set_tcp_keepalive_probes_senddelayms : newPort==0")
        else:
            self._tcp_keepalive_probes_senddelayms = value

    def _get_tcp_keepalive_probes_senddelayms(self):
        """
        Getter
        :return Value
        :rtype int
        """
        return self._tcp_keepalive_probes_senddelayms

    def _set_tcpkeepalive_probes_failedcount(self, value):
        """
        Setter. Raise exception if a problem occurs.
        :param value: Value.
        :type value: int
        
        """
        if not SolBase.is_int(value):
            logger.error("TcpClientConfig : _set_tcpkeepalive_probes_failedcount : not a int, class=%s", SolBase.get_classname(value))
            raise Exception("TcpClientConfig : _set_tcpkeepalive_probes_failedcount : not a int")
        elif value == 0:
            logger.warning("TcpClientConfig : _set_tcpkeepalive_probes_failedcount : newPort==0")
            raise Exception("TcpClientConfig : _set_tcpkeepalive_probes_failedcount : newPort==0")
        else:
            self._tcp_keepalive_probes_failedcount = value

    def _get_tcpkeepalive_probes_failedcount(self):
        """
        Getter
        :return Value
        :rtype int
        """
        return self._tcp_keepalive_probes_failedcount

    def _set_tcpkeepalive_probes_sendintervalms(self, value):
        """
        Setter. Raise exception if a problem occurs.
        :param value: Value.
        :type value: int
        
        """
        if not SolBase.is_int(value):
            logger.error("TcpClientConfig : _set_tcpkeepalive_probes_sendintervalms : not a int, class=%s", SolBase.get_classname(value))
            raise Exception("TcpClientConfig : _set_tcpkeepalive_probes_sendintervalms : not a int")
        elif value == 0:
            logger.warning("TcpClientConfig : _set_tcpkeepalive_probes_sendintervalms : newPort==0")
            raise Exception("TcpClientConfig : _set_tcpkeepalive_probes_sendintervalms : newPort==0")
        else:
            self._tcp_keepalive_probes_sendintervalms = value

    def _get_tcpkeepalive_probes_sendintervalms(self):
        """
        Getter
        :return Value
        :rtype int
        """
        return self._tcp_keepalive_probes_sendintervalms

    # Properties
    target_addr = property(_get_targetaddr, _set_targetaddr)
    target_port = property(_get_target_port, _set_target_port)
    ssl_enable = property(_get_ssl_enable, _set_ssl_enable)
    timeout_ms = property(_get_timeout_ms, _set_timeout_ms)
    debug_log = property(_get_debug_log, _set_debug_log)

    proxy_enable = property(_get_proxy_enable, _set_proxy_enable)
    proxy_addr = property(_get_proxy_addr, _set_proxy_addr)
    proxy_port = property(_get_proxy_port, _set_proxy_port)

    tcp_keepalive_enabled = property(_get_tcp_keepalive_enabled, _set_tcp_keepalive_enabled)
    tcp_keepalive_probes_senddelayms = property(_get_tcp_keepalive_probes_senddelayms, _set_tcp_keepalive_probes_senddelayms)
    tcp_keepalive_probes_failedcount = property(_get_tcpkeepalive_probes_failedcount, _set_tcpkeepalive_probes_failedcount)
    tcp_keepalive_probes_sendintervalms = property(_get_tcpkeepalive_probes_sendintervalms, _set_tcpkeepalive_probes_sendintervalms)
