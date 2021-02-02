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

import logging
from threading import RLock

import gevent
import os
# noinspection PyProtectedMember
from gevent.queue import Empty
from pysolbase.SolBase import SolBase
from pysolmeters.Meters import Meters
from random import randint

from pysoltcp.tcpserver.queuedclientcontext.TcpServerQueuedClientContext import TcpServerQueuedClientContext

SolBase.logging_init()
logger = logging.getLogger(__name__)


class PingServerContext(TcpServerQueuedClientContext):
    """
    Tcp server client context.
    """

    def __init__(self, tcp_server, client_id, client_socket, client_addr):
        """
        Constructor.
        :param tcp_server: The tcp server.
        :param client_id: The client id.
        :param client_socket: The client socket.
        :param client_addr: The client address.

        """

        # Base - we provide two callback :
        # - one for disconnecting ourselves
        # - one to notify socket receive buffer
        TcpServerQueuedClientContext.__init__(self, tcp_server, client_id, client_socket, client_addr)

        # Intervals (will be set by the factory)
        self._helloTimeOutMs = 0
        self._pingIntervalMs = 0
        self._pingTimeOutMs = 0

        # Greenlets
        self._helloTimeOutGreenlet = None
        self._pingGreenlet = None
        self._pingTimeOutGreenlet = None

        # Instance protocol lock
        self._protocolLock = RLock()

        # Timestamp
        self.dtClientConnect = None
        self.dtLastPingSend = None

        # Stop calls
        self.stop_synch_internalCalled = False
        self.stop_synchCalled = False

    # =================================
    # CONNECT
    # =================================

    def start(self):
        """
        Connect to server.
        :return Return true upon success.
        """

        # Timestamp
        self.dtClientConnect = SolBase.datecurrent()

        # Call base
        b = TcpServerQueuedClientContext.start(self)
        if not b:
            # Stat
            logger.error("start failed, fatal, exiting")
            Meters.aii("ping.server.serverStartError")

            # Exit
            return False

        # Stat
        Meters.aii("ping.server.serverStartCount")

        # Schedule an hello timeout
        self._schedule_client_hello_timeout()
        return True

    # =================================
    # DISCONNECT
    # =================================

    def stop_synch_internal(self):
        """
        Disconnect from server.
        :return Return true upon success.
        """

        # Stat
        Meters.aii("ping.server.serverStopSynchCount")

        # Clean
        self._unschedule_client_hello_timeout()
        self._unschedule_server_ping()
        self._unschedule_server_ping_client_timeout()

        # Called
        self.stop_synch_internalCalled = True

        # Base
        return TcpServerQueuedClientContext.stop_synch_internal(self)

    def stop_synch(self):
        """
        Stop synch
        """

        # Called
        self.stop_synchCalled = True

        # Base
        return TcpServerQueuedClientContext.stop_synch(self)

    # =================================
    # HELLO TIMEOUT SCHEDULE
    # =================================

    def _schedule_client_hello_timeout(self):
        """
        Schedule a ping timeout

        """

        with self._protocolLock:
            # Check
            if self._helloTimeOutGreenlet:
                logger.warning("_helloTimeOutGreenlet is not None, killing")
                Meters.aii("ping.server.scheduleClientHelloTimeOutError")
                self._unschedule_client_hello_timeout()
                # Go
            self._helloTimeOutGreenlet = gevent.spawn_later(self._helloTimeOutMs * 0.001, self._protocol_context_client_hello_timeout)

    def _unschedule_client_hello_timeout(self):
        """
        Unschedule a ping

        """
        with self._protocolLock:
            if self._helloTimeOutGreenlet:
                self._helloTimeOutGreenlet.kill()
                self._helloTimeOutGreenlet = None

    # =================================
    # PING SCHEDULE
    # =================================

    def _schedule_server_ping(self, randomize_delay=False):
        """
        Schedule a ping

        """
        with self._protocolLock:
            # Check
            if self._pingGreenlet:
                logger.warning("_ping_greenlet is not None, killing")
                Meters.aii("ping.server.scheduleServerPingError")
                self._unschedule_server_ping()

            # Go
            if not randomize_delay:
                self._pingGreenlet = gevent.spawn_later(self._pingIntervalMs * 0.001, self._protocol_server_ping_send)
            else:
                # Randomize delay
                vmin = int(self._pingIntervalMs / 2)
                vmax = int(self._pingIntervalMs)
                ms = randint(vmin, vmax)
                self._pingGreenlet = gevent.spawn_later(ms * 0.001, self._protocol_server_ping_send)

    def _unschedule_server_ping(self):
        """
        Unschedule a ping

        """
        with self._protocolLock:
            if self._pingGreenlet:
                self._pingGreenlet.kill()
                self._pingGreenlet = None

    # =================================
    # PING TIMEOUT SCHEDULE
    # =================================

    def _schedule_server_ping_client_timeout(self):
        """
        Schedule a ping timeout

        """

        with self._protocolLock:
            # Check
            if self._pingTimeOutGreenlet:
                logger.warning("_ping_timeout_greenlet is not None, killing")
                Meters.aii("ping.server.scheduleServerPingTimeOutError")
                self._unschedule_server_ping_client_timeout()
                # Go
            self._pingTimeOutGreenlet = gevent.spawn_later(self._pingTimeOutMs * 0.001, self._protocol_server_ping_client_timeout)

    def _unschedule_server_ping_client_timeout(self):
        """
        Unschedule a ping

        """
        with self._protocolLock:
            if self._pingTimeOutGreenlet:
                self._pingTimeOutGreenlet.kill()
                self._pingTimeOutGreenlet = None

    # =================================
    # RECEIVE
    # =================================

    def _on_receive(self, binary_buffer):
        """
        Callback called upon server receive.
        :param binary_buffer: Received buffer.

        """

        # Received something...
        logger.debug("binary_buffer=%s", binary_buffer)

        # Base
        TcpServerQueuedClientContext._on_receive(self, binary_buffer)

        # Pump the queue
        while True:
            try:
                # Try
                item = self.get_from_receive_queue()
                # Process
                self._process_item(SolBase.binary_to_unicode(item, "utf-8"))
            except Empty:
                break

    # =================================
    # PROTOCOL DISPATCHING
    # =================================

    def _process_item(self, item):
        """
        Process a received item
        :param item: Item to process.
        :type item: str

        """

        # PROTOCOL             => Any send failed on socket : fatal.
        # C.HI   : C.HI.REPLY    => Hello sequence. Blocking, fatal on error. Upon success, start ping loop.
        # C.PING : C.PING.REPLY  => Client ping. Upon timeout, reschedule.
        # S.PING : S.PING.REPLY  => Server ping. Client just reply.

        if item.find("C.HI") == 0:
            # Hello received, reply
            self._protocol_client_hello_received()
        elif item.find("S.PING.REPLY") == 0:
            # Reply to a previous server ping
            self._protocol_server_ping_client_reply()
        elif item.find("C.PING") == 0:
            # Client ping, we must reply
            self._protocol_client_ping_receive()
        else:
            # Invalid procotol
            self._protocol_invalid()

    # =================================
    # INVALID MANAGEMENT
    # =================================

    # noinspection PyMethodMayBeStatic
    def _protocol_invalid(self):
        """
        Invalid procotol

        """
        Meters.aii("ping.server.invalid_protocol")

    # =================================
    # HELLO MANAGEMENT
    # =================================

    def _protocol_client_hello_received(self):
        """
        Must send a hello

        """
        with self._protocolLock:
            # Un-schedule hello timeout
            self._unschedule_client_hello_timeout()

            # Stats
            Meters.aii("ping.server.clientHelloReceived")

            # Delay
            Meters.aii("ping.server.delayClientConnectToClientHello", SolBase.datediff(self.dtClientConnect))

            # Send a reply
            b = self.send_unicode_to_socket("C.HI.REPLY PID={0}".format(os.getpid()))
            if not b:
                # Stat
                logger.error("send failed, fatal, disconnecting")
                Meters.aii("ping.server.serverSendError")

                # Disconnect
                self.stop_asynch()
            else:
                # Now connected, schedule a ping
                self._schedule_server_ping()

                # Stats
                Meters.aii("ping.server.client_hello_server_reply")

    def _protocol_context_client_hello_timeout(self):
        """
        Hello timeout

        """

        with self._protocolLock:
            logger.error("timeout, fatal, disconnecting")

            # Reset (we are called by it)
            self._helloTimeOutGreenlet = None

            # Stats
            Meters.aii("ping.server.clientHelloTimeOut")

            # Disconnect ourselves (this is fatal)
            self.stop_asynch()

    # =================================
    # PING MANAGEMENT : CLIENT
    # =================================

    def _protocol_client_ping_receive(self):
        """
        Received a client ping
        """

        with self._protocolLock:
            # Stats
            Meters.aii("ping.server.clientPingReceive")

            # Reply
            b = self.send_unicode_to_socket("C.PING.REPLY")
            if not b:
                # Stat
                logger.error("send failed, fatal, disconnecting")
                Meters.aii("ping.server.serverSendError")
                # Disconnect
                self.stop_asynch()
            else:
                # Stats
                Meters.aii("ping.server.client_ping_server_reply")

    # =================================
    # PING MANAGEMENT : SERVER
    # =================================

    def _protocol_server_ping_send(self):
        """
        Must send a client ping

        """
        with self._protocolLock:
            # Reset (we are called by it)
            self._pingGreenlet = None

            # Schedule a timeout
            self._schedule_server_ping_client_timeout()

            # Timestamp
            self.dtLastPingSend = SolBase.datecurrent()

            # Send a ping
            b = self.send_unicode_to_socket("S.PING")
            if not b:
                # Stat
                logger.error("send failed, fatal, disconnecting")
                Meters.aii("ping.server.serverSendError")
                # Disconnect
                self.stop_asynch()
            else:
                # Stats
                Meters.aii("ping.server.serverPingSent")

    def _protocol_server_ping_client_reply(self):
        """
        A client ping has been replied

        """

        with self._protocolLock:
            # Must have a timeout ongoing
            if self._pingTimeOutGreenlet is None:
                # Ping reply received without ongoing ping
                Meters.aii("ping.server.serverPingServerClientReplyNoPingOngoing")
            else:
                # Unschedule the timeout
                self._unschedule_server_ping_client_timeout()

                # Reschedule a ping
                self._schedule_server_ping()

                # Stats
                Meters.aii("ping.server.serverPingClientReply")

                # Delay
                Meters.dtci("ping.server.client_ping_server_reply", SolBase.datediff(self.dtLastPingSend))

    def _protocol_server_ping_client_timeout(self):
        """
        Called when a ping has time-out (ie no reply from server)

        """

        with self._protocolLock:
            logger.warning("ping timeout, rescheduling ping")

            # Reset (we are called by it)
            self._pingTimeOutGreenlet = None

            # Reschedule a ping
            self._schedule_server_ping()

            # Stat
            Meters.aii("ping.server.serverPingClientTimeOut")
