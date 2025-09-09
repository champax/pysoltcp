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
import logging
from threading import RLock

import gevent
# noinspection PyProtectedMember
from gevent.queue import Empty
from pysolbase.SolBase import SolBase
from pysolmeters.Meters import Meters
from random import randint

from pysoltcp.tcpclient.TcpSimpleClient import TcpSimpleClient

SolBase.logging_init()
logger = logging.getLogger(__name__)


class PingSimpleClient(TcpSimpleClient):
    """
    Tcp simple client
    """

    def __init__(self, tcp_client_config, hello_timeout_ms, ping_interval_ms, ping_timeout_ms):
        """
        Constructor.
        :param tcp_client_config: Tcp client configuration.
        :param hello_timeout_ms: Timeout in ms.
        :param ping_interval_ms: Timeout in ms.
        :param ping_timeout_ms: Timeout in ms.
        :return: Nothing.
        """

        # Base call
        TcpSimpleClient.__init__(self, tcp_client_config)

        # Intervals
        self._hello_timeout_ms = hello_timeout_ms
        self._ping_interval_ms = ping_interval_ms
        self._ping_timeout_ms = ping_timeout_ms

        # Greenlets
        self._hello_timeout_greenlet = None
        self._ping_greenlet = None
        self._ping_timeout_greenlet = None

        # Server PID
        self._server_pid = None

        # Instance protocol lock
        self._protocol_lock = RLock()

        # Timestamp
        self.dt_hello_send = None
        self.dt_last_ping_send = None

    # =================================
    # CONNECT
    # =================================

    def connect(self):
        """
        Connect to server.
        :return Return true upon success.
        """

        # Stats
        Meters.aii("ping.client.client_connect_count")

        # Call base
        dt_start = SolBase.datecurrent()
        b = TcpSimpleClient.connect(self)
        if not b:
            # Stat
            logger.error("PingSimpleClient : connect failed, fatal, exiting")
            Meters.aii("ping.client.client_connect_error")

            # Exit
            return False

        # Stat
        Meters.dtci("ping.client.delay_client_connect", SolBase.datediff(dt_start))

        # SSL stats
        ms = self._get_ssl_handshake_ms()
        if ms:
            Meters.dtci("ping.client.delay_client_sslhandshake", ms)

        # Send hello
        self._protocol_client_hello_send()
        return True

    # =================================
    # DISCONNECT
    # =================================

    def disconnect(self):
        """
        Disconnect from server.
        :return Return true upon success.
        """

        # Stat
        Meters.aii("ping.client.client_disconnect_count")

        # Clean
        self._unschedule_client_helloservertimeout()
        self._unschedule_client_ping()
        self._unschedule_client_pingservertimeout()

        # Base
        return TcpSimpleClient.disconnect(self)

    # =================================
    # HELLO TIMEOUT SCHEDULE
    # =================================

    def _schedule_client_helloservertimeout(self):
        """
        Schedule a ping timeout

        """

        with self._protocol_lock:
            # Check
            if self._hello_timeout_greenlet:
                logger.warning("_hello_timeout_greenlet is not None, killing")
                Meters.aii("ping.client.schedule_client_hello_server_timeout_error")
                self._unschedule_client_helloservertimeout()
                # Go
            self._hello_timeout_greenlet = gevent.spawn_later(self._hello_timeout_ms * 0.001, self._protocol_client_hello_server_timeout)

    def _unschedule_client_helloservertimeout(self):
        """
        Unschedule a ping

        """
        with self._protocol_lock:
            if self._hello_timeout_greenlet:
                self._hello_timeout_greenlet.kill()
                self._hello_timeout_greenlet = None

    # =================================
    # PING SCHEDULE
    # =================================

    def _schedule_clientping(self, randomize_delay=False):
        """
        Schedule a ping
        :param randomize_delay: Randomize delay if true.

        """
        with self._protocol_lock:
            # Check
            if self._ping_greenlet:
                logger.warning("PingSimpleClient : _schedule_clientping : _ping_greenlet is not None, killing")
                Meters.aii("ping.client.schedule_client_ping_error")
                self._unschedule_client_ping()

            # Go
            if not randomize_delay:
                self._ping_greenlet = gevent.spawn_later(self._ping_interval_ms * 0.001, self._protocol_client_ping_send)
            else:
                # Randomize delay
                vmin = int(self._ping_interval_ms / 2)
                vmax = int(self._ping_interval_ms)
                ms = randint(vmin, vmax)
                self._ping_greenlet = gevent.spawn_later(ms * 0.001, self._protocol_client_ping_send)

    def _unschedule_client_ping(self):
        """
        Unschedule a ping

        """
        with self._protocol_lock:
            if self._ping_greenlet:
                self._ping_greenlet.kill()
                self._ping_greenlet = None

    # =================================
    # PING TIMEOUT SCHEDULE
    # =================================

    def _schedule_client_pingservertimeout(self):
        """
        Schedule a ping timeout

        """

        with self._protocol_lock:
            # Check
            if self._ping_timeout_greenlet:
                logger.warning("_ping_timeout_greenlet is not None, killing")
                Meters.aii("ping.client.schedule_client_pingtimeouterror")
                self._unschedule_client_pingservertimeout()
                # Go
            self._ping_timeout_greenlet = gevent.spawn_later(self._ping_timeout_ms * 0.001, self._protocol_client_pingserver_timeout)

    def _unschedule_client_pingservertimeout(self):
        """
        Unschedule a ping

        """
        with self._protocol_lock:
            if self._ping_timeout_greenlet:
                self._ping_timeout_greenlet.kill()
                self._ping_timeout_greenlet = None

    # =================================
    # RECEIVE
    # =================================

    def _on_receive(self, binary_buffer):
        """
        Callback called upon server receive.
        :param binary_buffer: The binary buffer received.

        """

        # Received something...
        logger.debug("binary_buffer=%s", binary_buffer)

        # Base
        TcpSimpleClient._on_receive(self, binary_buffer)

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
        :param item: The received item.
        :type item: str
        """

        # PROTOCOL             => Any send failed on socket : fatal.
        # C.HI   : C.HI.REPLY    => Hello sequence. Blocking, fatal on error. Upon success, start ping loop.
        # C.PING : C.PING.REPLY  => Client ping. Upon timeout, reschedule.
        # S.PING : S.PING.REPLY  => Server ping. Client just reply.

        if item.find("C.HI.REPLY") == 0:
            # Reply to hello
            self._protocol_client_hello_server_reply(item)
        elif item.find("C.PING.REPLY") == 0:
            # Reply to a previous client ping
            self._protocol_client_ping_server_reply()
        elif item.find("S.PING") == 0:
            # Server ping, we must reply
            self._protocol_server_ping_receive()
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
        Meters.aii("ping.client.invalid_protocol")

    # =================================
    # HELLO MANAGEMENT
    # =================================

    def _protocol_client_hello_send(self):
        """
        Must send a hello

        """
        with self._protocol_lock:
            # Schedule a timeout
            self._schedule_client_helloservertimeout()

            # Timestamp
            self.dt_hello_send = SolBase.datecurrent()

            # Send a ping
            b = self.send_unicode_to_socket("C.HI")
            if not b:
                # Stat
                logger.error("send failed, fatal, disconnecting")
                Meters.aii("ping.client.client_send_error")

                # Disconnect
                self.disconnect()
            else:
                # Stats
                Meters.aii("ping.client.client_hello_sent")

    def _protocol_client_hello_server_reply(self, item):
        """
        Received a hello reply
        :param item: Received server reply ("C.HI.REPLY PID=...")

        """

        with self._protocol_lock:
            # Parse it
            self._server_pid = item.replace("C.HI.REPLY PID=", "")

            # Unschedule timeout
            self._unschedule_client_helloservertimeout()

            # Stats
            Meters.aii("ping.client.client_hello_server_reply")

            # Delay
            ms = SolBase.datediff(self.dt_hello_send)

            # Stats
            Meters.dtci("ping.client.delay_client_hello_toserver_reply", ms)

            # Initiate the ping loop, with random start
            self._schedule_clientping(True)

    def _protocol_client_hello_server_timeout(self):
        """
        Hello timeout

        """

        with self._protocol_lock:
            logger.error("timeout, fatal, disconnecting")

            # Reset (we are called by it)
            self._hello_timeout_greenlet = None

            # Stats
            Meters.aii("ping.client.client_hello_server_timeout")

            # Disconnect ourselves (this is fatal)
            self.disconnect()

    # =================================
    # PING MANAGEMENT : SERVER PING
    # =================================

    def _protocol_server_ping_receive(self):
        """
        Received a server ping

        """

        with self._protocol_lock:
            # Stats
            Meters.aii("ping.client.server_ping_receive")

            # Reply
            b = self.send_unicode_to_socket("S.PING.REPLY")
            if not b:
                # Stat
                logger.error("send failed, fatal, disconnecting")
                Meters.aii("ping.client.client_send_error")
                # Disconnect
                self.disconnect()
            else:
                # Stats
                Meters.aii("ping.client.server_ping_reply")

    # =================================
    # PING MANAGEMENT : CLIENT PING
    # =================================

    def _protocol_client_ping_send(self):
        """
        Must send a client ping

        """
        with self._protocol_lock:
            # Reset (we are called by it)
            self._ping_greenlet = None

            # Schedule a timeout
            self._schedule_client_pingservertimeout()

            # Timestamp
            self.dt_last_ping_send = SolBase.datecurrent()

            # Send a ping
            b = self.send_unicode_to_socket("C.PING")
            if not b:
                # Stat
                logger.error("send failed, fatal, disconnecting")
                Meters.aii("ping.client.client_send_error")
                # Disconnect
                self.disconnect()
            else:
                # Stats
                Meters.aii("ping.client.client_ping_sent")

    def _protocol_client_ping_server_reply(self):
        """
        A client ping has been replied

        """

        with self._protocol_lock:
            # Must have a timeout ongoing
            if self._ping_timeout_greenlet is None:
                # Ping reply received without ongoing ping
                Meters.aii("ping.client.client_ping_server_reply_noping_ongoing")
            else:
                # Unschedule the timeout
                self._unschedule_client_pingservertimeout()

                # Reschedule a ping
                self._schedule_clientping()

                # Stats
                Meters.aii("ping.client.client_ping_server_reply")

                # Delay and stats
                Meters.dtci("ping.client.delay_client_ping_toserver_reply", SolBase.datediff(self.dt_last_ping_send))

    def _protocol_client_pingserver_timeout(self):
        """
        Called when a ping has time-out (ie no reply from server)

        """

        with self._protocol_lock:
            logger.warning("ping timeout, rescheduling ping, ms=%s", SolBase.datediff(self.dt_last_ping_send))

            # Reset (we are called by it)
            if self._ping_timeout_greenlet is None:
                # Greenlet none, not normal, we are called by it
                logger.warning("_ping_timeout_greenlet None")

            self._ping_timeout_greenlet = None

            # Reschedule a ping
            self._schedule_clientping()

            # Stat
            Meters.aii("ping.client.client_pingserver_timeout")
