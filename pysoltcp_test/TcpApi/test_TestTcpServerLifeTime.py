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
# Imports
import unittest

from pysolbase.SolBase import SolBase

from pysoltcp.tcpclient.TcpClientConfig import TcpClientConfig
from pysoltcp.tcpclient.TcpSimpleClient import TcpSimpleClient
from pysoltcp.tcpserver.TcpServer import TcpServer
from pysoltcp.tcpserver.TcpServerConfig import TcpServerConfig
from pysoltcp_test.Utility import Utility

SolBase.logging_init()
logger = logging.getLogger(__name__)


class TestTcpServerLifeTime(unittest.TestCase):
    """
    Test description
    """

    def setUp(self):
        """
        Setup

        """

        SolBase.voodoo_init()
        Utility.gevent_reset()
        logger.info("setUp : entering")
        Utility.test_wait()

        # Timeout
        self.checkTimeOut = 2500

        # Init
        self.tcp_server = None
        self.tcp_client = None

        # Certificate path
        self.certificatesPath = Utility.generate_server_keys()
        logger.info("Setting certificates_path=%s", self.certificatesPath)

    def tearDown(self):
        """
        Setup (called on destroy)

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
            if self.tcp_client:
                self.tcp_client.disconnect()
        except Exception as e:
            self.fail("Exception on disconnect, ex=" + SolBase.extostr(e))

        Utility.test_wait()

    def _start_all(self, server_config):
        """
        Start server and client.
        :param server_config: Server config.
        :return: tuple pysoltcp.tcpserver.TcpServer.TcpServer,pysoltcp.tcp_client.TcpSimpleClient.TcpSimpleClient
        :rtype tuple
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
        self.tcp_client = TcpSimpleClient(client_config)

        # Check
        self.assertTrue(self.tcp_client.current_socket is None)
        self.assertTrue(not self.tcp_client.is_connected)

        # Connect
        logger.info("Starting connect()")
        self.assertTrue(self.tcp_client.connect())
        logger.info("Starting connect() : done")

        # Check client
        self.assertIsNotNone(self.tcp_client.current_socket)
        self.assertTrue(self.tcp_client.is_connected)

        # Wait for server
        logger.info("TestLog : server : wait connection")
        dt_start = SolBase.datecurrent()
        while SolBase.datediff(dt_start) < self.checkTimeOut:
            if len(self.tcp_server._client_connected_hash) > 0:
                break
            SolBase.sleep(int(self.checkTimeOut / 100))
        logger.info("TestLog : server : wait connection : done")

        # Check
        self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

        # Ok
        logger.info("Started and connected, effectiveMs=%s", self.tcp_server.get_effective_controlinterval_ms())
        return self.tcp_server, self.tcp_client

    def _waitforserver_disconnection(self, timeout_ms):
        """
        Wait for client disconnection at server level
        :return: Nothing
        """

        logger.info("server : wait for disconnection")
        dt_start = SolBase.datecurrent()
        while SolBase.datediff(dt_start) < timeout_ms:
            if len(self.tcp_server._client_connected_hash) == 0 and self.tcp_client.current_socket is None:
                break
            SolBase.sleep(timeout_ms / 1000)
        logger.info("server : wait for disconnection : done, ms=%s", SolBase.datediff(dt_start))

        # Check
        self.assertEqual(len(self.tcp_server._client_connected_hash), 0)
        self.assertIsNone(self.tcp_client.current_socket)

    def test_server_effective_ms(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

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
        self.assertEqual(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 2500)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 100
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 100)

        server_config.socket_absolute_timeout_ms = 100
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 100)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 500
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 500
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 0
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 0)

        # ----------------
        # Bounded by socket_min_checkinterval_ms
        # ----------------

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 2500
        server_config.socket_relative_timeout_ms = 100
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 100
        server_config.socket_relative_timeout_ms = 2500
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 60000)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = 0
        server_config.socket_relative_timeout_ms = 0
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 0)

        server_config.socket_absolute_timeout_ms = -1
        server_config.socket_relative_timeout_ms = -1
        server_config.socket_min_checkinterval_ms = 60000
        s = TcpServer(server_config)
        self.assertEqual(s.get_effective_controlinterval_ms(), 0)

    def test_absolute_timeout(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 2500
            server_config.socket_relative_timeout_ms = 0
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self.tcp_server, self.tcp_client = self._start_all(server_config)

            # Client is connected
            self._waitforserver_disconnection((self.tcp_server.get_effective_controlinterval_ms() * 2) + 2000)

            # Check client
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Reset client
            self.tcp_client = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    def test_absolute_timeout_priortorelative(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 2500
            server_config.socket_relative_timeout_ms = 60000
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self.tcp_server, self.tcp_client = self._start_all(server_config)

            # Client is connected
            self._waitforserver_disconnection((self.tcp_server.get_effective_controlinterval_ms() * 2) + 2000)

            # Check client
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Reset client
            self.tcp_client = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    def test_relative_timeout(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 0
            server_config.socket_relative_timeout_ms = 2500
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self.tcp_server, self.tcp_client = self._start_all(server_config)

            # Client is connected
            self._waitforserver_disconnection((self.tcp_server.get_effective_controlinterval_ms() * 2) + 2000)

            # Check client
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Reset client
            self.tcp_client = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    def test_relative_timeout_priortoabsolute(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 60000
            server_config.socket_relative_timeout_ms = 2500
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self.tcp_server, self.tcp_client = self._start_all(server_config)

            # Client is connected
            self._waitforserver_disconnection((self.tcp_server.get_effective_controlinterval_ms() * 2) + 2000)

            # Check client
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Reset client
            self.tcp_client = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    def test_do_not_close(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.socket_absolute_timeout_ms = 60000
            server_config.socket_relative_timeout_ms = 60000
            server_config.socket_min_checkinterval_ms = 0

            # Start
            self.tcp_server, self.tcp_client = self._start_all(server_config)

            # Wait a bit
            SolBase.sleep(5000)

            # Check client
            self.assertIsNotNone(self.tcp_client.current_socket)
            self.assertTrue(self.tcp_client.is_connected)

            # Disconnect
            self.tcp_client.disconnect()

            # Check client
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Reset client
            self.tcp_client = None

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()
