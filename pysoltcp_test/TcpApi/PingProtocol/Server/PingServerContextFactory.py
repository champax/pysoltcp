"""
# -*- coding: utf-8 -*-
# ===============================================================================
#
# Copyright (C) 2013/2017 Laurent Labatut / Laurent Champagnac
#
#
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

from pysoltcp.tcpserver.basefactory.TcpServerClientContextAbstractFactory import TcpServerClientContextAbstractFactory
from pysoltcp_test.TcpApi.PingProtocol.Server.PingServerContext import PingServerContext

SolBase.logging_init()
logger = logging.getLogger(__name__)


class PingServerContextFactory(TcpServerClientContextAbstractFactory):
    """
    Default factory.
    """

    def __init__(self, hello_timeout_ms, ping_interval_ms, ping_timeout_ms):
        """
        Constructor.
        :param hello_timeout_ms: Timeout in millis.
        :param ping_interval_ms: Timeout in millis.
        :param ping_timeout_ms: Timeout in millis.
        """

        self._hello_timeout_ms = SolBase.to_int(hello_timeout_ms)
        self._ping_interval_ms = SolBase.to_int(ping_interval_ms)
        self._ping_timeout_ms = SolBase.to_int(ping_timeout_ms)

        logger.info("_hello_timeout_ms=%s, type=%s", self._hello_timeout_ms, SolBase.get_classname(self._hello_timeout_ms))
        logger.info("_ping_interval_ms=%s, type=%s", self._ping_interval_ms, SolBase.get_classname(self._ping_interval_ms))
        logger.info("_ping_timeout_ms=%s, type=%s", self._ping_timeout_ms, SolBase.get_classname(self._ping_timeout_ms))

    def get_new_clientcontext(self, tcp_server, client_id, client_socket, client_addr):
        """
        Return a new client context instance.
        :param tcp_server: The tcpserver instance.
        :param client_id: an integer, which is the unique id of this client.
        :param client_socket: The server socket.
        :param client_addr: The remote addr information.
        :return Returned object MUST be a subclass of TcpServerClientContext.
        """
        new_client = PingServerContext(tcp_server, client_id, client_socket, client_addr)
        new_client._helloTimeOutMs = self._hello_timeout_ms
        new_client._pingIntervalMs = self._ping_interval_ms
        new_client._pingTimeOutMs = self._ping_timeout_ms
        return new_client
