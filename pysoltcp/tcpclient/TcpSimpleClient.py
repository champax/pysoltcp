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
from _socket import SOL_SOCKET, SOL_TCP, SO_KEEPALIVE, TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT
from _ssl import PROTOCOL_TLSv1
from threading import Lock

import gevent
# noinspection PyPackageRequirements
import socks
from gevent import GreenletExit

from gevent.queue import Queue
from pysolbase.SolBase import SolBase
from pysolmeters.AtomicInt import AtomicIntSafe

from pysoltcp.tcpbase.ProtocolParserTextDelimited import ProtocolParserTextDelimited
from pysoltcp.tcpbase.TcpSocketManager import TcpSocketManager
from pysoltcp.tcpclient.TcpClientConfig import TcpClientConfig

from gevent.ssl import SSLSocket

SolBase.voodoo_init()

logger = logging.getLogger(__name__)


class TcpSimpleClient(TcpSocketManager):
    """
    Tcp simple client
    """

    def __init__(self, tcp_client_config):
        """
        Constructor.
        Option via TcpClientConfig to enable SSL on socket.
        In this case, SSL handshake is to be done manually AFTER connect. Higher level implementation MUST handle this.
        :param tcp_client_config: The tcp client config.
        :type tcp_client_config: pysoltcp.tcpclient.TcpClientConfig.TcpClientConfig
        """

        # Base - we provide two callback :
        # - one for disconnecting ourselves
        # - one to notify socket receive buffer
        TcpSocketManager.__init__(self, self.disconnect, self._on_receive)

        # Check
        if tcp_client_config is None:
            logger.error("TcpSimpleClient : tcp_serverConfig is None")
            raise Exception("TcpSimpleClient : tcp_serverConfig is None")
        elif not isinstance(tcp_client_config, TcpClientConfig):
            logger.error("TcpSimpleClient : tcp_serverConfig is not a TcpServerConfig, class=%s", SolBase.get_classname(tcp_client_config))
            raise Exception("TcpSimpleClient : tcp_serverConfig is not a TcpServerConfig")

        # Default
        self._tcp_client_config = tcp_client_config

        # Greenlets
        self._read_greenlet = None
        self._write_greenlet = None

        # Receive queue
        self._receive_queue = Queue()

        # Receive current buffer
        self._receive_current_buf = None

        # Socket info
        self._local_addr = None
        self._local_port = None
        self._remote_addr = None
        self._remote_port = None
        self._connect_count = AtomicIntSafe()
        self._disconnect_count = AtomicIntSafe()

        # Pool stuff
        self.process_id = None
        self.pool_id = None
        self.dt_alloc = SolBase.datecurrent()
        self.dt_last_acquire = self.dt_alloc
        self.dt_last_release = self.dt_alloc
        self.count_acquire = 0
        self.count_release = 0

        # Pool disconnect notify
        self.on_disconnect_notifypoolcallbacklock = Lock()
        self.on_disconnect_notifypoolcallbackcall = True
        self.on_disconnect_notifypoolcallback = None

        # Ssl
        self.ssl_handshake_timeout_ms = 5000

    # ================================
    # POOL METHOD
    # ================================

    def notify_acquire(self):
        """
        Notify
        """
        self.dt_last_acquire = SolBase.datecurrent()
        self.count_acquire += 1

    def notify_release(self):
        """
        Notify
        """
        self.dt_last_release = SolBase.datecurrent()
        self.count_release += 1

    # ================================
    # TO STRING OVERWRITE
    # ================================

    def __str__(self):
        """
        To string override
        :return: A string
        :rtype str
        """

        return "c.addr={0}:{1}/{2}:{3}*cc={4}*dc={5}*c.q.recv.size={6}*sock={7}*proxy={8}/{9}:{10}*{11}".format(
            self._local_addr, self._local_port, self._remote_addr, self._remote_port,
            self._connect_count.get(), self._disconnect_count.get(),
            self._receive_queue.qsize(),
            self.current_socket,
            self._tcp_client_config.proxy_enable,
            self._tcp_client_config.proxy_addr,
            self._tcp_client_config.proxy_port,
            TcpSocketManager.__str__(self)
        )

    # =================================
    # CONNECT
    # =================================

    def connect(self):
        """
        Connect to server. Return true upon success.
        If SSL is enable, do NOT forget at higher level to initiate a SSL handshake manually.
        :return True if connected, false otherwise.
        :rtype bool
        """

        try:
            logger.debug("TcpSimpleClient : connect : starting, target=%s:%s", self._tcp_client_config.target_addr, self._tcp_client_config.target_port)

            # Reset the error flag right now
            self.unset_internal_fatal_error_for_reconnect()

            # Check
            if self.is_connected:
                logger.warning("TcpSimpleClient : connect : already connected, doing nothing, self=%s", self)
                return False

            # Init
            self._connect_count.increment()
            self._dt_created = SolBase.datecurrent()
            self._dt_last_recv = self._dt_created
            self._dt_last_send = self._dt_created

            # ------------------------
            # ALLOC
            # ------------------------
            if self._tcp_client_config.ssl_enable:
                if self._tcp_client_config.proxy_enable:
                    # ------------------------
                    # PROXY ON, SSL ON
                    # ------------------------
                    if self._tcp_client_config.debug_log:
                        logger.info("TcpSimpleClient : Alloc : PROXY ON/SSL ON, self=%s", self)
                    else:
                        logger.debug("TcpSimpleClient : Alloc : PROXY ON/SSL ON, self=%s", self)

                    # Alloc
                    self.current_socket = socks.socksocket()

                    # Proxy
                    self.current_socket.setproxy(socks.PROXY_TYPE_SOCKS5, self._tcp_client_config.proxy_addr, self._tcp_client_config.proxy_port)

                    # SSL Wrap : Inside POST CONNECT
                else:
                    # ------------------------
                    # PROXY OFF, SSL ON
                    # ------------------------
                    if self._tcp_client_config.debug_log:
                        logger.info("TcpSimpleClient : Alloc : PROXY OFF/SSL ON, self=%s", self)
                    else:
                        logger.debug("TcpSimpleClient : Alloc : PROXY OFF/SSL ON, self=%s", self)

                    # Alloc
                    self.current_socket = gevent.socket.socket()

                    # Wrap
                    self.current_socket = SSLSocket(self.current_socket, do_handshake_on_connect=False, ssl_version=PROTOCOL_TLSv1)
            else:
                if self._tcp_client_config.proxy_enable:
                    # ------------------------
                    # PROXY ON, SSL OFF
                    # ------------------------
                    if self._tcp_client_config.debug_log:
                        logger.info("TcpSimpleClient : Alloc : PROXY ON/SSL OFF, self=%s", self)
                    else:
                        logger.debug("TcpSimpleClient : Alloc : PROXY ON/SSL OFF, self=%s", self)

                    # Alloc
                    self.current_socket = socks.socksocket()

                    # Proxy
                    self.current_socket.setproxy(socks.PROXY_TYPE_SOCKS5, self._tcp_client_config.proxy_addr,
                                                 self._tcp_client_config.proxy_port)
                else:
                    # ------------------------
                    # PROXY OFF, SSL OFF
                    # ------------------------
                    if self._tcp_client_config.debug_log:
                        logger.info("TcpSimpleClient : Alloc : PROXY OFF/SSL OFF, self=%s", self)
                    else:
                        logger.debug("TcpSimpleClient : Alloc : PROXY OFF/SSL OFF, self=%s", self)

                    # Alloc
                    self.current_socket = gevent.socket.socket()

            # ------------------------
            # POST ALLOC
            # ------------------------
            if self._tcp_client_config.timeout_ms:
                logger.debug("TcpSimpleClient : connect : setting timeout=%s, self=%s", self._tcp_client_config.timeout_ms, self)
                self.current_socket.settimeout(None)
                logger.debug("TcpSimpleClient : connect : timeout=%s, self=%s", self.current_socket.gettimeout(), self)

            # ------------------------
            # CONNECT
            # ------------------------

            # 2-tuple (host, port)
            address = (self._tcp_client_config.target_addr, self._tcp_client_config.target_port)

            # Connect
            if self._tcp_client_config.debug_log:
                logger.info("TcpSimpleClient : connect : starting, ssl=%s, timeout=%s, self=%s", self._tcp_client_config.ssl_enable, self._tcp_client_config.timeout_ms, self)

            # Go
            logger.debug("TcpSimpleClient : connect : calling connect, self=%s", self)
            self.current_socket.connect(address)
            logger.debug("TcpSimpleClient : connect : now connected, self=%s", self)

            # Store
            self._local_addr = self.current_socket.getsockname()[0]
            self._local_port = self.current_socket.getsockname()[1]
            self._remote_addr = self.current_socket.getpeername()[0]
            self._remote_port = self.current_socket.getpeername()[1]

            # Log
            if self._tcp_client_config.debug_log:
                logger.info("TcpSimpleClient : connected, %s:%s to %s:%s, self=%s", self._local_addr, self._local_port, self._remote_addr, self._remote_port, self)

            # Done
            self.is_connected = True
            self.on_disconnect_notifypoolcallbackcall = True

            # ------------------------
            # POST CONNECT
            # ------------------------
            if self._tcp_client_config.ssl_enable:
                # Switch to SSL now
                if self._tcp_client_config.debug_log:
                    logger.info("PROXY ON/SSL ON, switching to SSL now, self=%s", self)
                else:
                    logger.debug("PROXY ON/SSL ON, switching to SSL now, self=%s", self)

                # Wrap (already connected
                self.current_socket = SSLSocket(self.current_socket, do_handshake_on_connect=False, ssl_version=PROTOCOL_TLSv1)

                # Start
                dt_start = SolBase.datecurrent()

                # Do it
                logger.debug("TcpSimpleClient : __do_ssl_handshake now, self=%s", self)
                self.__do_ssl_handshake()

                # Time
                self._set_ssl_handshake_ms(SolBase.datediff(dt_start))

            # ------------------------
            # POST CONNECT
            # ------------------------

            if self._tcp_client_config.tcp_keepalive_enabled:
                # Switch to TCP KA now
                if self._tcp_client_config.debug_log:
                    logger.info(
                        "TCP KA ON, switching to KA now, (on=%s/delay=%s/failed=%s/interval=%s), self=%s",
                        self._tcp_client_config.tcp_keepalive_enabled,
                        self._tcp_client_config.tcp_keepalive_probes_senddelayms,
                        self._tcp_client_config.tcp_keepalive_probes_failedcount,
                        self._tcp_client_config.tcp_keepalive_probes_sendintervalms,
                        self)
                else:
                    logger.debug(
                        "TCP KA ON, switching to KA now, (on=%s/delay=%s/failed=%s/interval=%s), self=%s",
                        self._tcp_client_config.tcp_keepalive_enabled,
                        self._tcp_client_config.tcp_keepalive_probes_senddelayms,
                        self._tcp_client_config.tcp_keepalive_probes_failedcount,
                        self._tcp_client_config.tcp_keepalive_probes_sendintervalms,
                        self)

                # Go
                self.current_socket.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
                self.current_socket.setsockopt(SOL_TCP, TCP_KEEPIDLE, int(self._tcp_client_config.tcp_keepalive_probes_senddelayms / 1000))
                self.current_socket.setsockopt(SOL_TCP, TCP_KEEPINTVL, int(self._tcp_client_config.tcp_keepalive_probes_sendintervalms / 1000))
                self.current_socket.setsockopt(SOL_TCP, TCP_KEEPCNT, int(self._tcp_client_config.tcp_keepalive_probes_failedcount))

                # Check
                v = self.current_socket.getsockopt(SOL_SOCKET, SO_KEEPALIVE)
                if v != 1:
                    logger.warning("SO_KEEPALIVE mismatch, having=%s, required=1", v)

                v = self.current_socket.getsockopt(SOL_TCP, TCP_KEEPIDLE)
                if v != self._tcp_client_config.tcp_keepalive_probes_senddelayms / 1000:
                    logger.warning("TCP_KEEPIDLE mismatch, having=%s, required=%s", v, self._tcp_client_config.tcp_keepalive_probes_senddelayms / 1000)

                v = self.current_socket.getsockopt(SOL_TCP, TCP_KEEPINTVL)
                if v != self._tcp_client_config.tcp_keepalive_probes_sendintervalms / 1000:
                    logger.warning("TCP_KEEPINTVL mismatch, having=%s, required=%s", v, self._tcp_client_config.tcp_keepalive_probes_sendintervalms / 1000)

                v = self.current_socket.getsockopt(SOL_TCP, TCP_KEEPCNT)
                if v != self._tcp_client_config.tcp_keepalive_probes_failedcount:
                    logger.warning("TCP_KEEPCNT mismatch, having=%s, required=%s", v, self._tcp_client_config.tcp_keepalive_probes_failedcount)

            # Non-blocking mode
            self.current_socket.setblocking(0)
            self.current_socket.settimeout(None)
            logger.debug("TcpSimpleClient : connect : non blocking mode set, self=%s", self)

            # Start the read/write loops
            self._read_greenlet = gevent.spawn(self._read_loop)
            self._write_greenlet = gevent.spawn(self._write_loop)
            logger.debug("TcpSimpleClient : connect : r/w loops started, self=%s", self)

            # Done
            logger.debug("TcpSimpleClient : connect : done, self=%s", self)
            return True

        except Exception as e:
            # Logs
            logger.error("TcpSimpleClient : connect : Exception, ex=%s, self=%s", SolBase.extostr(e), self)

            # Call disconnect
            self._callback_disconnect()

            # Exit
            return False

    # =================================
    # DISCONNECT
    # =================================

    def disconnect(self):
        """
        Disconnect from server. Return true upon success.
        :return True if success, false otherwise.
        :rtype bool
        """
        try:
            logger.debug("TcpSimpleClient : disconnect : entering, self=%s", self)

            # Check
            if not self.is_connected:
                logger.debug("TcpSimpleClient : disconnect : not connected, doing nothing, self=%s", self)
                return False

            # Disconnect
            if self.current_socket:
                logger.debug("TcpSimpleClient : disconnect : socket.shutdown, self=%s", self)
                # noinspection PyUnusedLocal
                try:
                    self.current_socket.shutdown(2)
                except Exception as e:
                    logger.debug("Exception on shutdown, ex=%s, self=%s", SolBase.extostr(e), self)
                    pass

                logger.debug("TcpSimpleClient : disconnect : socket.close, self=%s", self)
                self.current_socket.close()
                self.current_socket = None

            # Reset socket related context
            self._dt_created = SolBase.datecurrent()
            self._dt_last_recv = self._dt_created
            self._dt_last_send = self._dt_created
            self._disconnect_count.increment()
            self._local_addr = None
            self._local_port = None
            self._remote_addr = None
            self._remote_port = None

            # Signal
            logger.debug("TcpSimpleClient : disconnect : is_connected=False, self=%s", self)
            self.is_connected = False

            # Handle notifications at upper level
            go_call = False

            # Second level callback - Process in lock to avoid multiple notification for same simple client instance
            with self.on_disconnect_notifypoolcallbacklock:
                if self.on_disconnect_notifypoolcallbackcall and self.on_disconnect_notifypoolcallback:
                    logger.debug("TcpSimpleClient : disconnect : calling second level disconnect callback, callback=%s, self=%s", self.on_disconnect_notifypoolcallback, self)
                    self.on_disconnect_notifypoolcallbackcall = False
                    go_call = True

            # Out of lock : call
            # (ASYNC, because we may be called by read/write greenlet, which are going to be killed just after)
            if go_call:
                try:
                    # Call it synchronously (mantis 1907)
                    self.on_disconnect_notifypoolcallback(self)

                    # DO NOT MOVE THIS SLEEP, REDIS WILL DEADLOCK ON START
                    SolBase.sleep(0)
                except Exception as e:
                    logger.warning("on_disconnect_notifypoolcallback : call exception=%s", SolBase.extostr(e))

            # Greenlet reset after is_connected=False (will help to exit itself)
            if self._read_greenlet:
                logger.debug("TcpSimpleClient : disconnect : read kill, self=%s", self)
                self._read_greenlet.kill(GreenletExit, False)
                logger.debug("TcpSimpleClient : disconnect : read kill 1, self=%s", self)
                self._read_greenlet = None
                logger.debug("TcpSimpleClient : disconnect : read kill 2, self=%s", self)

            if self._write_greenlet:
                logger.debug("TcpSimpleClient : disconnect : write kill, self=%s", self)
                self._write_greenlet.kill(GreenletExit, False)
                logger.debug("TcpSimpleClient : disconnect : write kill 1, self=%s", self)
                self._write_greenlet = None
                logger.debug("TcpSimpleClient : disconnect : write kill 2, self=%s", self)

            logger.debug("TcpSimpleClient : disconnect : done, self=%s", self)
            return True

        except Exception as e:
            logger.error("TcpSimpleClient : disconnect : Exception, ex=%s, self=%s", SolBase.extostr(e), self)
            return False

    # =================================
    # SSL HANDSHAKE
    # =================================

    def __do_ssl_handshake(self):
        """
        Do a ssl handshake. Method is using a greenlet, but is blocking for the caller.
        """

        # Go
        SolBase.sleep(0)
        try:
            logger.debug("Calling do_handshake now, ssl_handshake_timeout_ms=%s", self.ssl_handshake_timeout_ms)
            with gevent.Timeout(seconds=self.ssl_handshake_timeout_ms / 1000.0, exception=Exception):
                SolBase.sleep(0)
                self.current_socket.do_handshake()
                logger.debug("Called do_handshake")
        except Exception as e:
            logger.warning("Exception while waiting for do_handshake, ex=%s", SolBase.extostr(e))
            self._callback_disconnect()
        finally:
            SolBase.sleep(0)

    def __do_ssl_handshake_internal(self):
        """
        Do a ssl handshake. Call _callback_disconnect() if error.
        """
        try:
            logger.debug("__do_ssl_handshake_internal : start now, self=%s", self)
            SolBase.sleep(0)

        except Exception as e:
            logger.error("__do_ssl_handshake_internal : exception=%s, self=%s", SolBase.extostr(e), self)
            self._callback_disconnect()
        finally:
            SolBase.sleep(0)

    # =================================
    # RECEIVE
    # =================================

    def _on_receive(self, binary_buffer):
        """
        Callback called upon server receive.
        - binary_buffer : a BINARY buffer received on the socket.

        !! CAUTION !!
        - IN ALL CASES THIS METHOD RECEIVE A BINARY BUFFER

        !! CAUTION !!
        - PYTHON 2.X / binary - bytes    => bytes is a byte array (or an ascii string) : nothing to do
        - PYTHON 2.X / text - str  => you receive a bytes, you may convert it to str (SolBase.binary_to_unicode)

        !! CAUTION !!
        - PYTHON 3.X / binary - bytes  => bytes is binary. You may convert it to a bytes using encoding.

                |  2.x                     |  3.x
        --------+--------------------------+-----------------------
        Bytes   |  'abc' <type 'bytes'>      |  b'abc' <type 'bytes'>
        Unicode | u'abc' <type 'str'>  |   'abc' <type 'bytes'>
        :param binary_buffer: Binary buffer received.
        :type binary_buffer: bytes
        """

        # Received something...
        logger.debug("TcpSimpleClient : _on_receive : binary_buffer=%s, self=%s", repr(binary_buffer), self)

        # Parse
        self._receive_current_buf = ProtocolParserTextDelimited.parse_protocol(self._receive_current_buf, binary_buffer, self._receive_queue, b"\n")

    def get_recv_queue_len(self):
        """
        Get receive queue len
        :return The receive queue length.
        :rtype int
        """
        return self._receive_queue.qsize()

    # =================================
    # RECEIVE QUEUE
    # =================================

    def get_from_receive_queue(self, block=False, timeout_sec=None):
        """
        Get a buffer from the receive queue.
        - If block is False, will return an item OR raise an Empty exception if no item.
        - If block is True AND timeOut=None, will wait forever for an item.
        - If block is True and timeout_sec>0, will wait for timeout_sec then raise Empty exception if no item.
        :param block: If true, will block.
        :type block: bool
        :param timeout_sec: The timeout in second.
        :type timeout_sec: None,int
        """

        return self._receive_queue.get(block, timeout_sec)
