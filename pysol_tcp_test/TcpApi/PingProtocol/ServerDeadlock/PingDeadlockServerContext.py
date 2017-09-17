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

from pysol_base.SolBase import SolBase

from pysol_tcp_test.TcpApi.PingProtocol.Server.PingServerContext import PingServerContext

SolBase.logging_init()
logger = logging.getLogger(__name__)


class PingDeadlockServerContext(PingServerContext):
    """
    Tcp server client context.
    """

    # =================================
    # DISCONNECT
    # =================================

    def stop_synch_internal(self):
        """
        Disconnect from server.
        :return Return true upon success.
        """

        # Stop calls
        PingServerContext.stop_synch_internal(self)

        # Deadlock
        while True:
            SolBase.sleep(50)

    def stop_synch(self):
        """
        Stop synch
        """

        # Stop calls
        PingServerContext.stop_synch(self)

        # Deadlock
        while True:
            SolBase.sleep(50)
