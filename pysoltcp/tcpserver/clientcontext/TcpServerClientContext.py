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

import gevent
# noinspection PyProtectedMember
from gevent.queue import Empty
from pysolbase.SolBase import SolBase
from pysolmeters.Meters import Meters

from pysoltcp.tcpbase.SignaledBuffer import SignaledBuffer
from pysoltcp.tcpbase.TcpSocketManager import TcpSocketManager

SolBase.logging_init()
logger = logging.getLogger(__name__)


class TcpServerClientContext(TcpSocketManager):
    """
    Tcp server client context.
    """

    def __init__(self, tcp_server, client_id, client_socket, client_addr, cb_stop_asynch=None, cb_on_receive=None):
        """
        Constructor.
        :param tcp_server: The tcpserver instance.
        :type tcp_server: pysoltcp.tcpserver.TcpServer.TcpServer
        :param client_id: an integer, which is the unique id of this client.
        :type client_id: int
        :param client_socket: The server socket.
        :type client_socket: socket.socket
        :param client_addr: The remote addr information.
        :type client_addr: str
        :param cb_stop_asynch: Callback to call upon stop. If None, self.stop_asynch is used.
        :type cb_stop_asynch: Callable
        :param cb_on_receive: Callback to call upon socket receive. If none, self._on_receive is used.
        :type cb_on_receive: Callable

        """

        # Check
        if client_socket is None:
            logger.error("client_socket is None")
            raise Exception("client_socket is None")
        elif client_addr is None:
            logger.error("client_addr is None")
            raise Exception("client_addr is None")
        elif client_id is None:
            logger.error("client_id is None")
            raise Exception("client_id is None")
        elif tcp_server is None:
            logger.error("tcp_server is None")
            raise Exception("tcp_server is None")

        # Base - we provide two callback :
        # - one for disconnecting ourselves
        # - one to notify socket receive buffer

        # Stop callback
        cur_cb_stop_asynch = cb_stop_asynch
        if cb_stop_asynch is None:
            # Use default
            cur_cb_stop_asynch = self.stop_asynch

        # Receive callback
        cur_cb_on_receive = cb_on_receive
        if cur_cb_on_receive is None:
            # Use default
            cur_cb_on_receive = self._on_receive

        TcpSocketManager.__init__(self, cur_cb_stop_asynch, cur_cb_on_receive)

        # Store
        self._client_id = client_id
        self._client_addr = client_addr

        # Base store
        self.current_socket = client_socket

        # Server store
        self._tcp_server = tcp_server

        # Greenlets
        self._read_greenlet = None
        self._write_greenlet = None
        self._control_greenlet = None

        # Faster bytes
        self._socket_local_ip = None
        self._socket_local_port = None
        self._socket_remote_ip = None
        self._socket_remote_port = None

    # ================================
    # TO STRING OVERWRITE
    # ================================

    def __get_socket_local_ip(self):
        """
        Get socket local ip
        :return: String
        :rtype: str
        """
        if self._socket_local_ip:
            return self._socket_local_ip
        # noinspection PyBroadException
        try:
            self._socket_local_ip = self.current_socket.getsockname()[0]
            return self._socket_local_ip
        except Exception:
            return "exception"

    def __get_socket_local_port(self):
        """
        Get socket local ip
        :return: int
        :rtype: int
        """

        if self._socket_local_port:
            return self._socket_local_port
        # noinspection PyBroadException
        try:
            self._socket_local_port = self.current_socket.getsockname()[1]
            return self._socket_local_port
        except Exception:
            return "exception"

    def __get_socket_remote_ip(self):
        """
        Get socket remote ip
        :return: String
        :rtype: str
        """
        if self._socket_remote_ip:
            return self._socket_remote_ip
        # noinspection PyBroadException
        try:
            self._socket_remote_ip = self.current_socket.getpeername()[0]
            return self._socket_remote_ip
        except Exception:
            return "exception"

    def __get_socket_remote_port(self):
        """
        Get socket remote port
        :return: int
        :rtype: int
        """
        if self._socket_remote_port:
            return self._socket_remote_port

        # noinspection PyBroadException
        try:
            self._socket_remote_port = self.current_socket.getpeername()[1]
            return self._socket_remote_port
        except Exception:
            return "exception"

    def __str__(self):
        """
        To string override
        :return: A string
        :rtype str
        """

        return "c.id={0}*c.cli={1}:{2}/{3}:{4}*{5}".format(
            self._client_id,
            self.__get_socket_local_ip(),
            self.__get_socket_local_port(),
            self.__get_socket_remote_ip(),
            self.__get_socket_remote_port(),
            TcpSocketManager.__str__(self)
        )

    # ===============================
    # START
    # ===============================

    def start(self):
        """
        Start processing our socket read/write.
        :return True if success, false otherwise.
        :rtype bool
        """
        try:
            # Check
            if self.is_connected:
                logger.warning("TcpServerClientContext : start : already connected, doing nothing, self=%s", self)
                return False

            # Done
            self.is_connected = True
            logger.debug("TcpServerClientContext : start : now connected, starting r/w loops, self=%s", self)

            # Start the read/write loops
            self._read_greenlet = gevent.spawn(self._read_loop)
            self._write_greenlet = gevent.spawn(self._write_loop)

            # Start the control greenlet
            self._schedule_control_greenlet()

            # Done
            logger.debug("TcpServerClientContext : start : done, self=%s", self)
            return True
        except Exception as e:
            logger.error("TcpServerClientContext : start : Exception, ex=%s, self=%s", SolBase.extostr(e), self)
            return False

    # ===============================
    # STOP
    #
    # - stop_asynch
    # => used ONLY if stop comes from OUR instance (read/write loop initiated stop, due to socket issues, control stuff)
    # => This delegates the stop to the tcp_server, which will process it asynchronously, ending with a stop_synch call.
    #
    # - stop_synch
    # => used by external components to request a stop.
    # ===============================

    def stop_asynch(self):
        """
        Request a stop to the tcp_server.. It will call _stopInternal(), via tcp_server._remove_client_asynch.
        Do NOT OVERRIDE this method.
        :return True if success, false otherwise.
        :rtype bool
        """
        try:
            if not self.is_connected:
                return True
            else:
                # noinspection PyProtectedMember
                self._tcp_server._remove_client_asynch(self.get_client_id())
                return True
        except Exception as e:
            logger.error("TcpServerClientContext : stopFromServer : Exception, ex=%s, self=%s", SolBase.extostr(e), self)
            return False

    def stop_synch(self):
        """
        Stop processing our socket read/write.
        CAUTION : This method NOT be called if the server is stopping.
        Do NOT call this from ourselves, instead use stop_asynch, you may/will experience unexpected behaviors.
        This method is RESERVED for EXTERNAL class stop requests.
        You can OVERRIDE this method at HIGHER level to be informed of a socket closure.
        :return True if success, false otherwise.
        :rtype bool
        """

        return True

    def stop_synch_internal(self):
        """
        Stop processing our socket read/write.
        Reserved for PURE in-memory stop operations (greenlet stop, counter put mainly)
        NEVER, NEVER perform any kind of non-memory operations here.
        For instance, are FORDIDEN in higher level implementation of stop_synch_internal :
        - Any socket send/recv
        - Any external queries (redis/mongo, whatever)
        JUST HANDLE IN MEMORY STUFF.
        :return True if success, false otherwise.
        :rtype bool
        """

        try:
            logger.debug("TcpServerClientContext : disconnect : entering, self=%s", self)

            # Check
            if not self.is_connected:
                logger.debug("TcpServerClientContext : disconnect : not connected, doing nothing, self=%s", self)
                return False

            # Signal (move on top, try to avoid some TcpManager warn logs while stopping)
            self.is_connected = False

            # Timeout unschedule
            self._unschedule_ssl_handshake_timeout()

            # Control unschedule
            self._unschedule_control_greenlet()

            # Disconnect
            # Close the socket in this case (should not cover mantis 1173)
            SolBase.safe_close_socket(self.current_socket)
            self.current_socket = None

            # Greenlet reset after is_connected=False (will help to exit itself)
            if self._read_greenlet:
                self._read_greenlet.kill()
                self._read_greenlet = None

            if self._write_greenlet:
                self._write_greenlet.kill()
                self._write_greenlet = None

            # Flush out the send queue now, and decrement pending bytes to send
            total_len = 0
            while True:
                try:
                    item = self.send_queue.get(False)
                    if isinstance(item, bytes):
                        total_len += len(item)
                    elif isinstance(item, SignaledBuffer):
                        total_len += len(item.binary_buffer)
                except Empty:
                    break

            # Decrement
            logger.debug("TcpServerClientContext : disconnect : decrementing, total_len=%s", total_len)
            Meters.aii("tcp.server.server_bytes_send_pending", -total_len)

            # Over
            logger.debug("TcpServerClientContext : disconnect : done, self=%s", self)
            return True

        except Exception as e:
            logger.error("TcpServerClientContext : disconnect : Exception, ex=%s, self=%s", SolBase.extostr(e),
                         self)
            return False
        finally:
            # Session duration stats
            sec = SolBase.datediff(self._dt_created) / 1000
            Meters.dtci("tcp.server.session_duration_second", sec)

    # ===============================
    # GETTER / SETTER
    # ===============================

    def get_client_id(self):
        """
        Getter
        :return The client id.
        :rtype int
        """
        return self._client_id

    def get_client_socket(self):
        """
        Getter
        :return The client socket.
        :rtype socket.socket
        """
        return self.current_socket

    def get_client_addr(self):
        """
        Getter
        :return: The client remote address.
        :rtype str
        """
        return self._client_addr

    # ===============================
    # RECEIVE
    # ===============================

    def _on_receive(self, binary_buffer):
        """
        Called on socket receive.
        :param binary_buffer: The received buffer.
        :type binary_buffer: bytes
        """

        # Got something
        logger.debug("TcpServerClientContext : _on_receive called, binary_buffer=%s, self=%s", repr(binary_buffer), self)
        pass

    # ===============================
    # CONTROL
    # ===============================

    def _schedule_control_greenlet(self):
        """
        Schedule the control greenlet for next run.
        Note: We do not use lock to minimize per socket memory usage...
        """

        # Check
        if not self.is_connected:
            return

        # Get
        ms = self._tcp_server.get_effective_controlinterval_ms()
        if ms <= 0:
            return

        # Schedule it !
        self._control_greenlet = gevent.spawn_later(ms * 0.001, self._control_us)

    def _unschedule_control_greenlet(self):
        """
        unschedule the control greenlet.
        Note: We do not use lock to minimize per socket memory usage...
        """

        if self._control_greenlet:
            self._control_greenlet.kill(block=False)
            self._control_greenlet = None

    def _control_us(self):
        """
        Control us. May force ourself to exit upon inactivity.
        Note: We do not use lock to minimize per socket memory usage...
        """

        logger.info("Entering")

        # Check
        if not self.is_connected:
            return

        # Get settings
        c = self._tcp_server.get_tcpserver_config()

        # Check absolute
        absolute_ms = c.socket_absolute_timeout_ms
        if absolute_ms > 0:
            running_ms = SolBase.datediff(self._dt_created)
            if running_ms > absolute_ms:
                logger.debug("Absolute reached, running_ms=%s, absolute_ms=%s, self=%s", running_ms, absolute_ms, self)
                # Kill ourself if we are running
                if self.is_connected:
                    self.stop_asynch()
                return
            else:
                logger.debug("Absolute not reached, running_ms=%s, absolute_ms=%s, self=%s", running_ms, absolute_ms,
                             self)
                pass

        # Check relative
        relative_ms = c.socket_relative_timeout_ms
        if relative_ms > 0:
            # Get last receive ms
            last_recv_ms = SolBase.datediff(self._dt_last_recv)

            # Get last send ms
            last_send_ms = SolBase.datediff(self._dt_last_send)

            # We keep the minimum of both
            last_ms = min(last_recv_ms, last_send_ms)

            # Check
            if last_ms > relative_ms:
                # Kill ourself
                logger.debug("Relative reached, last_recv_ms=%s, last_send_ms=%s, last_ms=%s, relative_ms=%s, self=%s", last_recv_ms, last_send_ms, last_ms, relative_ms, self)
                if self.is_connected:
                    self.stop_asynch()
                return
            else:
                logger.debug("Relative not reached, last_recv_ms=%s, last_send_ms=%s, last_ms=%s, relative_ms=%s, self=%s", last_recv_ms, last_send_ms, last_ms, relative_ms, self)

        # Schedule next check
        self._schedule_control_greenlet()
