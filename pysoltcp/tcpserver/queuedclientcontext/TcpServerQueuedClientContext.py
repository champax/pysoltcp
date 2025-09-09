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

from gevent.queue import Queue
from pysolbase.SolBase import SolBase

from pysoltcp.tcpbase.ProtocolParserTextDelimited import ProtocolParserTextDelimited
from pysoltcp.tcpserver.clientcontext.TcpServerClientContext import TcpServerClientContext

SolBase.logging_init()
logger = logging.getLogger(__name__)


class TcpServerQueuedClientContext(TcpServerClientContext):
    """
    Tcp server client context.
    """

    def __init__(self, tcp_server, client_id, client_socket, client_addr):
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
        """

        # Base - we provide two callback :
        # - one for disconnecting ourselves
        # - one to notify socket receive buffer
        TcpServerClientContext.__init__(self, tcp_server, client_id, client_socket, client_addr)

        # Receive queue
        self.__receive_queue = Queue()

        # Receive current buffer
        self.__receive_current_buf = None

    # ================================
    # TO STRING OVERWRITE
    # ================================

    def __str__(self):
        """
        To string override
        :return: A string
        :rtype str
        """

        return "q.recv.size={0}*{1}".format(
            self.__receive_queue.qsize(),
            TcpServerClientContext.__str__(self)
        )

    # ===============================
    # RECEIVE
    # ===============================

    def _on_receive(self, binary_buffer):
        """
        Called on socket receive. Method parse the protocol and put receive queue.
        :param binary_buffer: The binary buffer received.
        :type binary_buffer: bytes

        """

        # Got something
        logger.debug("TcpServerQueuedClientContext : _on_receive called, binary_buffer=%s, self=%s", repr(binary_buffer), self)

        # Parse
        self.__receive_current_buf = ProtocolParserTextDelimited.parse_protocol(self.__receive_current_buf, binary_buffer, self.__receive_queue, b"\n")

    def get_recv_queue_len(self):
        """
        Get receive queue len.
        :return An integer.
        :rtype int
        """
        return self.__receive_queue.qsize()

    # =================================
    # RECEIVE QUEUE
    # =================================

    def get_from_receive_queue(self, block=False, timeout_sec=None):
        """
        Get a buffer from the receive queue.
        :param block: If True, will block.
        :type block: bool
        :param timeout_sec: Timeout in seconds.
        :type timeout_sec: int
        :return An item queued.
        :rtype bytes,pysoltcp.tcpbase.SignaledBuffer.SignaledBuffer
        - If block is False, will return an item OR raise an Empty exception if no item.
        - If block is True AND timeOut=None, will wait forever for an item.
        - If block is True and timeout_sec>0, will wait for timeout_sec then raise Empty exception if no item.
        """

        return self.__receive_queue.get(block, timeout_sec)
