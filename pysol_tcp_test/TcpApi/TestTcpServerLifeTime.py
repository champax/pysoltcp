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
# Imports
import unittest

from pysol_base.SolBase import SolBase

from pysol_tcp.tcpclient.TcpClientConfig import TcpClientConfig
from pysol_tcp.tcpclient.TcpSimpleClient import TcpSimpleClient
from pysol_tcp.tcpserver.TcpServer import TcpServer
from pysol_tcp.tcpserver.TcpServerConfig import TcpServerConfig
from pysol_tcp_test.Utility import Utility

SolBase.logging_init()
logger = logging.getLogger(__name__)


class TestTcpServerLifeTime(unittest.TestCase):
    """
    Test description
    """

    def setUp(self):
        """
        Setup
        :return Nothing.
        """

        SolBase.voodoo_init()
        Utility.gevent_reset()
        logger.info("setUp : entering")
        Utility.test_wait()

        # Timeout
        self.checkTimeOut = 2500

        # Init
        self.tcp_server = None
        self.tcpClient = None

        # Certificate path
        self.certificatesPath = Utility.generate_server_keys()
        logger.info("Setting certificates_path=%s", self.certificatesPath)

    def tearDown(self):
        """
        Setup (called on destroy)
        :return Nothing.
        """

        if not SolBase.get_master_process():
            return

        logger.info("tearDown : entering")

        try:
            if self.tcp_server:
                self.tcp_server.stop_server()
        except Exception as e:
            self.fail("Exception on stop_server, ex=" + SolBase.extostr(e))

        try:
            if self.tcpClient:
                self.tcpClient.disconnect()
        except Exception as e:
            self.fail("Exception on disconnect, ex=" + SolBase.extostr(e))

        Utility.test_wait()

    def _start_all(self, server_config):
        """
        Start server and client.
        :param server_config: Server config.
        :return: nothing.
        """

        # Allocate
        self.tcp_server = TcpServer(server_config)

        # Check
        self.assertIsNotNone(self.tcp_server)
        self.assertFalse(self.tcp_server._is_started)
        self.assertTrue(self.tcp_server._server is None)

        # Start
        self.assertTrue(self.tcp_server.start_server())
        self.assertTrue(self.tcp_server._is_started)
        self.assertFalse(self.tcp_server._server is None)

        # Client config
        client_config = TcpClientConfig()
        client_config.target_addr = "127.0.0.1"
        client_config.target_port = 3201
        client_config.debug_log = True

        # Client
        self.tcpClient = TcpSimpleClient(client_config)

        # Check
        self.assertTrue(self.tcpClient.current_socket is None)
        self.assertTrue(not self.tcpClient.is_connected)

        # Connect
        logger.info("Starting connect()")
        self.assertTrue(self.tcpClient.connect())
        logger.info("Starting connect() : done")

        # Check client
        self.assertIsNotNone(self.tcpClient.current_socket)
        self.assertTrue(self.tcpClient.is_connected)

        # Wait for server
        logger.info("TestLog : server : wait connection")
        dt_start = SolBase.datecurrent()
        while SolBase.datediff(dt_start) < self.checkTimeOut:
            if len(self.tcp_server._client_connected_hash) > 0:
                break
            SolBase.sleep(self.checkTimeOut / 100)
        logger.info("TestLog : server : wait connection : done")

        # Check
        self.assertEquals(len(self.tcp_server._client_connected_hash), 1)

        # Ok
        logger.info("Started and connected, effectiveMs=%s", self.tcp_server.get_effective_controlinterval_ms())

    def _waitforserver_disconnection(self, timeout_ms):
        """
        Wait for client disconnection at server level
        :return: Nothing
        """

        logger.info("server : wait for disconnection")
        dt_start = SolBase.datecurrent()
        while SolBase.datediff(dt_start) < timeout_ms:
            if len(self.tcp_server._client_connected_hash) == 0 and self.tcpClient.current_socket is None:
                break
            SolBase.sleep(timeout_ms / 1000)
        logger.info("server : wait for disconnection : done, ms=%s", SolBase.datediff(dt_start))

        # Check
        self.assertEquals(len(self.tcp_server._client_connected_hash), 0)
        self.assertIsNone(self.tcpClient.current_socket)

    def test_server_effective_ms(self):
        """
        Test
        :return Nothing.
        """

        # Instances
        self.tcp_server = None
        self.tcpClient = None

        # Config
        server_config = TcpServerConfig()
        server_config.listen_addr = "127.0.0.1"
        server_config.listen_port = 3201
        server_config.auto_start = False

        # ----------------
        # NOT Bounded by socket_min_checkinterval_ms
        # ----------------

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 100
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 100)

        server_config.socket_absolute_timeout_ms = 100
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 100)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 500
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 500
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 0)

        # ----------------
        # Bounded by socket_min_checkinterval_ms
        # ----------------

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 100
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 100
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEquals(s.get_effective_controlinterval_ms(), 0)

    def test_absolute_timeout(self):
        """
        Test
        :return Nothing.
        """

        # Instances
        self.tcp_server = None
        self.tcpClient = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 2500
            server_config.socket_relative_timeout_ms = 0
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self._start_all(server_config)

            # Client is connected
            self._waitforserver_disconnection((self.tcp_server.get_effective_controlinterval_ms() * 2) + 2000)

            # Check client
            self.assertTrue(self.tcpClient.current_socket is None)
            self.assertFalse(self.tcpClient.is_connected)

            # Reset client
            self.tcpClient = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcpClient = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    def test_absolute_timeout_priortorelative(self):
        """
        Test
        :return Nothing.
        """

        # Instances
        self.tcp_server = None
        self.tcpClient = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 2500
            server_config.socket_relative_timeout_ms = 60000
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self._start_all(server_config)

            # Client is connected
            self._waitforserver_disconnection((self.tcp_server.get_effective_controlinterval_ms() * 2) + 2000)

            # Check client
            self.assertTrue(self.tcpClient.current_socket is None)
            self.assertFalse(self.tcpClient.is_connected)

            # Reset client
            self.tcpClient = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcpClient = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    def test_relative_timeout(self):
        """
        Test
        :return Nothing.
        """

        # Instances
        self.tcp_server = None
        self.tcpClient = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 0
            server_config.socket_relative_timeout_ms = 2500
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self._start_all(server_config)

            # Client is connected
            self._waitforserver_disconnection((self.tcp_server.get_effective_controlinterval_ms() * 2) + 2000)

            # Check client
            self.assertTrue(self.tcpClient.current_socket is None)
            self.assertFalse(self.tcpClient.is_connected)

            # Reset client
            self.tcpClient = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcpClient = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    def test_relative_timeout_priortoabsolute(self):
        """
        Test
        :return Nothing.
        """

        # Instances
        self.tcp_server = None
        self.tcpClient = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 60000
            server_config.socket_relative_timeout_ms = 2500
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self._start_all(server_config)

            # Client is connected
            self._waitforserver_disconnection((self.tcp_server.get_effective_controlinterval_ms() * 2) + 2000)

            # Check client
            self.assertTrue(self.tcpClient.current_socket is None)
            self.assertFalse(self.tcpClient.is_connected)

            # Reset client
            self.tcpClient = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcpClient = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    def test_do_not_close(self):
        """
        Test
        :return Nothing.
        """

        # Instances
        self.tcp_server = None
        self.tcpClient = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 60000
            server_config.socket_relative_timeout_ms = 60000
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self._start_all(server_config)

            # Wait a bit
            SolBase.sleep(5000)

            # Check client
            self.assertIsNotNone(self.tcpClient.current_socket)
            self.assertTrue(self.tcpClient.is_connected)

            # Disconnect
            self.tcpClient.disconnect()

            # Check client
            self.assertTrue(self.tcpClient.current_socket is None)
            self.assertFalse(self.tcpClient.is_connected)

            # Reset client
            self.tcpClient = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcpClient = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()
