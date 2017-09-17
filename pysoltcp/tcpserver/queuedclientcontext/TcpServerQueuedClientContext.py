"""
# -*- coding: utf-8 -*-
# ===============================================================================
#
# Copyright (C) 2013/2017 Laurent Labatut / Laurent Champagnac
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
        :param tcp_server: The tcp server.
        :param client_id: The client id.
        :param client_socket: The client socket.
        :param client_addr: The client remote address.
        :return Nothing
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
        :rtype string
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
        :return Nothing.
        """

        # Got something
        logger.debug("TcpServerQueuedClientContext : _on_receive called, binary_buffer=%s, self=%s", repr(binary_buffer), self)

        # Parse
        self.__receive_current_buf = ProtocolParserTextDelimited.parse_protocol(self.__receive_current_buf, binary_buffer, self.__receive_queue, "\n")

    def get_recv_queue_len(self):
        """
        Get receive queue len.
        :return An integer.
        """
        return self.__receive_queue.qsize()

    # =================================
    # RECEIVE QUEUE
    # =================================

    def get_from_receive_queue(self, block=False, timeout_sec=None):
        """
        Get a buffer from the receive queue.
        :param block: If True, will block.
        :param timeout_sec: Timeout in seconds.
        :return An item queued.
        - If block is False, will return an item OR raise an Empty exception if no item.
        - If block is True AND timeOut=None, will wait forever for an item.
        - If block is True and timeout_sec>0, will wait for timeout_sec then raise Empty exception if no item.
        """

        return self.__receive_queue.get(block, timeout_sec)
