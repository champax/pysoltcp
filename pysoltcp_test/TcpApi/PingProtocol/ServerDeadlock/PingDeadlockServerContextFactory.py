"""
# -*- coding: utf-8 -*-
# ===============================================================================
#
# Copyright (C) 2013/2025 Laurent Labatut / Laurent Champagnac
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

from pysoltcp_test.TcpApi.PingProtocol.Server.PingServerContextFactory import PingServerContextFactory
from pysoltcp_test.TcpApi.PingProtocol.ServerDeadlock.PingDeadlockServerContext import PingDeadlockServerContext

SolBase.logging_init()
logger = logging.getLogger(__name__)


class PingDeadlockServerContextFactory(PingServerContextFactory):
    """
    Default factory.
    """

    def get_new_clientcontext(self, tcp_server, client_id, client_socket, client_addr):
        """
        Return a new client context instance.
        :param tcp_server: The tcpserver instance.
        :param client_id: an integer, which is the unique id of this client.
        :param client_socket: The server socket.
        :param client_addr: The remote addr information.
        :return Returned object MUST be a subclass of TcpServerClientContext.
        """
        new_client = PingDeadlockServerContext(tcp_server, client_id, client_socket, client_addr)
        new_client._helloTimeOutMs = self._hello_timeout_ms
        new_client._pingIntervalMs = self._ping_interval_ms
        new_client._pingTimeOutMs = self._ping_timeout_ms
        return new_client
