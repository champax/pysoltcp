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

from gevent.event import Event
from pysolbase.SolBase import SolBase
from pysolmeters.AtomicInt import AtomicIntSafe
from pysolmeters.Meters import Meters

from pysoltcp.tcpbase.SignaledBuffer import SignaledBuffer
from pysoltcp.tcpclient.TcpClientConfig import TcpClientConfig
from pysoltcp.tcpclient.TcpSimpleClient import TcpSimpleClient
from pysoltcp.tcpserver.TcpServer import TcpServer
from pysoltcp.tcpserver.TcpServerConfig import TcpServerConfig
from pysoltcp.tcpserver.queuedclientcontext.TcpServerQueuedClientContextFactory import TcpServerQueuedClientContextFactory
from pysoltcp_test import ENABLE_SSL
from pysoltcp_test.TcpApi import is_dante_detected
from pysoltcp_test.TcpApi.PingProtocol.Client.PingSimpleClient import PingSimpleClient
from pysoltcp_test.TcpApi.PingProtocol.Server.PingServerContextFactory import PingServerContextFactory
from pysoltcp_test.Utility import Utility

SolBase.logging_init()
logger = logging.getLogger(__name__)


# ============================================
# Unit src class
# ============================================


class TestTcpServer(unittest.TestCase):
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

        # Init
        self.tcp_server = None
        self.tcp_client = None
        self.test_ssl = False
        self.test_proxy = False

        # Certificate path
        self.certificates_path = Utility.generate_server_keys()
        logger.info("Setting certificates_path=%s", self.certificates_path)

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

    def test_client_config_setter(self):
        """
        Test
        """

        tcc = TcpClientConfig()

        tcc.tcp_keepalive_enabled = False
        tcc.tcp_keepalive_probes_failedcount = 1
        tcc.tcp_keepalive_probes_senddelayms = 2
        tcc.tcp_keepalive_probes_sendintervalms = 3

        self.assertEqual(tcc.tcp_keepalive_enabled, False)
        self.assertEqual(tcc.tcp_keepalive_probes_failedcount, 1)
        self.assertEqual(tcc.tcp_keepalive_probes_senddelayms, 2)
        self.assertEqual(tcc.tcp_keepalive_probes_sendintervalms, 3)

    def test_tcp_svrstart_svrstop(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # Start again
            self.assertFalse(self.tcp_server.start_server())
            self.assertTrue(self.tcp_server._is_started)
            self.assertFalse(self.tcp_server._server is None)

            # Stop
            self.tcp_server.stop_server()
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)

            # Stop again
            self.tcp_server.stop_server()
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)

            # Reset
            self.tcp_server = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()

    def test_tcp_svrstart_svrstop_fork(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.child_process_count = 1

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # Start again
            self.assertFalse(self.tcp_server.start_server())
            self.assertTrue(self.tcp_server._is_started)
            self.assertFalse(self.tcp_server._server is None)

            # Stop
            self.tcp_server.stop_server()
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)

            # Stop again
            self.tcp_server.stop_server()
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)

            # Reset
            self.tcp_server = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svrstart_clipinghipid_svrstop_fork(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        try:
            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.child_process_count = 2
            server_config.client_factory = PingServerContextFactory(10000, 60000, 60000)

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

            # Check
            if not SolBase.get_master_process():
                logger.info("getIsMaster==False, exiting (child process)")
                return

            # Map of server pid
            server_pid_hash = dict()

            # Go
            logger.info("Starting connect, isMaster=%s", SolBase.get_master_process())
            dt_start_loop = SolBase.datecurrent()
            loop_timeout_ms = 120000
            idx = 0
            while SolBase.datediff(dt_start_loop) < loop_timeout_ms:
                idx += 1
                logger.debug("Starting connect, %s", idx)

                # Client config
                client_config = TcpClientConfig()
                client_config.target_addr = "127.0.0.1"
                client_config.target_port = 3201
                client_config.debug_log = False

                # Client
                self.tcp_client = PingSimpleClient(client_config, 10000, 60000, 60000)

                # Check
                self.assertTrue(self.tcp_client.current_socket is None)
                self.assertFalse(self.tcp_client.is_connected)

                self.assertTrue(self.tcp_client.connect())
                logger.debug("Starting connect() : done")

                # Check client
                self.assertIsNotNone(self.tcp_client.current_socket)
                self.assertTrue(self.tcp_client.is_connected)

                # Wait for client
                logger.debug("Waiting server PID")
                timeout_ms = 10000
                dt_start = SolBase.datecurrent()
                while self.tcp_client._server_pid is None:
                    if SolBase.datediff(dt_start) > timeout_ms:
                        break
                    else:
                        SolBase.sleep(10)

                # Check
                self.assertIsNotNone(self.tcp_client._server_pid)
                logger.info("Received _server_pid=%s", self.tcp_client._server_pid)

                # Register
                if self.tcp_client._server_pid not in server_pid_hash:
                    server_pid_hash[self.tcp_client._server_pid] = AtomicIntSafe(1)
                else:
                    server_pid_hash[self.tcp_client._server_pid].increment()

                # Check
                if len(server_pid_hash) == server_config.child_process_count + 1:
                    logger.info("Server PID complete")
                    break

                # Kill client
                self.tcp_client.disconnect()

                # Check client
                self.assertTrue(self.tcp_client.current_socket is None)
                self.assertFalse(self.tcp_client.is_connected)

                # Reset client
                self.tcp_client = None

                SolBase.sleep(0)

            # Logs
            for key, value in server_pid_hash.items():
                logger.info("Key=%s, Value=%s", key, value.get())

            # Stop
            self.tcp_server.stop_server()
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)

            # Stop again
            self.tcp_server.stop_server()
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)

            # Check
            self.assertTrue(len(server_pid_hash) == server_config.child_process_count + 1)

            # Reset
            self.tcp_server = None
        finally:
            if SolBase.get_master_process():
                if self.tcp_server:
                    self.tcp_server.stop_server()
            else:
                # Run forever
                logger.info("Running forever (child process")
                evt = Event()
                evt.wait()

    def test_tcp_svrstart_cliconnect_svrstop(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Checks
            check_timeout = 2500

            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # ssl
            if self.test_ssl:
                client_config.ssl_enable = True

            # proxy
            if self.test_proxy:
                client_config.proxy_enable = True
                client_config.proxy_addr = "127.0.0.1"
                client_config.proxy_port = 1080

            # Client
            self.tcp_client = TcpSimpleClient(client_config)

            # Check
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Connect
            self.assertTrue(self.tcp_client.connect())

            # Check
            self.assertIsNotNone(self.tcp_client.current_socket)
            self.assertTrue(self.tcp_client.is_connected)

            # Wait for server
            logger.info("server : wait connection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if len(self.tcp_server._client_connected_hash) > 0:
                    break
                SolBase.sleep(int(int(check_timeout / 100)))
            logger.info("server : wait connection : done")

            # Check
            self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

            # Stop
            logger.info("server : stopping")
            self.tcp_server.stop_server()
            logger.info("server : stopped")
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)
            self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

            # Client should be disconnected
            # Wait for client
            logger.info("client : wait for disconnection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if not self.tcp_client.is_connected:
                    break
                SolBase.sleep(int(check_timeout / 100))

            # Check
            logger.info("client : check for disconnection")
            self.assertFalse(self.tcp_client.is_connected)

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    def test_tcp_svrstart_cliconnect_clistop(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Checks
            check_timeout = 2500

            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # ssl
            if self.test_ssl:
                client_config.ssl_enable = True

            # proxy
            if self.test_proxy:
                client_config.proxy_enable = True
                client_config.proxy_addr = "127.0.0.1"
                client_config.proxy_port = 1080

            # Client
            self.tcp_client = TcpSimpleClient(client_config)

            # Check
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Connect
            logger.info("Starting connect()")
            self.assertTrue(self.tcp_client.connect())
            logger.info("Starting connect() : done")

            # Check client
            self.assertIsNotNone(self.tcp_client.current_socket)
            self.assertTrue(self.tcp_client.is_connected)

            # Wait for server
            logger.info("server : wait connection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if len(self.tcp_server._client_connected_hash) > 0:
                    break
                SolBase.sleep(int(check_timeout / 100))
            logger.info("server : wait connection : done")

            # Check
            self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

            # Kill client
            self.tcp_client.disconnect()

            # Check client
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Reset client
            self.tcp_client = None

            # Server should be disconnected from client
            # Wait for server
            logger.info("server : wait for disconnection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if len(self.tcp_server._client_connected_hash) == 0:
                    break
                SolBase.sleep(int(check_timeout / 100))

            # Check
            logger.info("server : check for disconnection")
            self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

            # Stop server
            self.tcp_server.stop_server()

            # Reset
            self.tcp_server = None
            self.tcp_client = None

            # Stats
            Meters.write_to_logger()
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    def test_tcp_svrstart_cliconnect_inloop_clistop(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Checks
            check_timeout = 2500

            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # ssl
            if self.test_ssl:
                client_config.ssl_enable = True

            # proxy
            if self.test_proxy:
                client_config.proxy_enable = True
                client_config.proxy_addr = "127.0.0.1"
                client_config.proxy_port = 1080

            # Client
            self.tcp_client = TcpSimpleClient(client_config)

            # Loop
            for idx in range(100):
                logger.info("Loop idx=%s, instance=%s", idx, self.tcp_client)
                # Check
                self.assertTrue(self.tcp_client.current_socket is None)
                self.assertFalse(self.tcp_client.is_connected)

                # Connect
                logger.info("Starting connect()")
                self.assertTrue(self.tcp_client.connect())
                logger.info("Starting connect() : done")

                # Check client
                self.assertIsNotNone(self.tcp_client.current_socket)
                self.assertTrue(self.tcp_client.is_connected)

                # Wait for server
                logger.info("server : wait connection")
                dt_start = SolBase.datecurrent()
                while SolBase.datediff(dt_start) < check_timeout:
                    if len(self.tcp_server._client_connected_hash) > 0:
                        break
                    SolBase.sleep(int(check_timeout / 100))
                logger.info("server : wait connection : done")

                # Check
                self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

                # Kill client
                self.tcp_client.disconnect()

                # Check client
                self.assertTrue(self.tcp_client.current_socket is None)
                self.assertFalse(self.tcp_client.is_connected)

                # Server should be disconnected from client
                # Wait for server
                logger.info("server : wait for disconnection")
                dt_start = SolBase.datecurrent()
                while SolBase.datediff(dt_start) < check_timeout:
                    if len(self.tcp_server._client_connected_hash) == 0:
                        break
                    SolBase.sleep(int(check_timeout / 100))

                # Check
                logger.info("server : check for disconnection")
                self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

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

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svrstart_clisend_svrreply_svrstop(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Checks
            check_timeout = 2500
            queue_timeout_sec = 5000 / 1000

            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.client_factory = TcpServerQueuedClientContextFactory()

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # ssl
            if self.test_ssl:
                client_config.ssl_enable = True

            # proxy
            if self.test_proxy:
                client_config.proxy_enable = True
                client_config.proxy_addr = "127.0.0.1"
                client_config.proxy_port = 1080

            # Client
            self.tcp_client = TcpSimpleClient(client_config)

            # Check
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Connect
            self.assertTrue(self.tcp_client.connect())

            # Check
            self.assertIsNotNone(self.tcp_client.current_socket)
            self.assertTrue(self.tcp_client.is_connected)

            # Wait for server
            logger.info("server : wait connection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if len(self.tcp_server._client_connected_hash) > 0:
                    break
                SolBase.sleep(int(check_timeout / 100))
            logger.info("server : wait connection : done")

            # Check
            self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

            # ==================================
            # CHAT INIT
            # ==================================

            # Get the server client instance
            tcp_server_client = self.tcp_server._client_connected_hash[list(self.tcp_server._client_connected_hash.keys())[0]]

            # ==================================
            # CHAT START
            # ==================================

            # Client  : send HI
            self.assertTrue(self.tcp_client.send_unicode_to_socket("HI 999"))

            # Server : wait for receive, 5 sec timeout (will raise Empty exception on timeout)
            buf_recv = tcp_server_client.get_from_receive_queue(True, queue_timeout_sec)
            self.assertEqual(buf_recv, b"HI 999")

            # Server : reply
            self.assertTrue(tcp_server_client.send_unicode_to_socket("OK 999"))

            # Client : wait for receive, 5 sec timeout (will raise Empty exception on timeout
            buf_recv = self.tcp_client.get_from_receive_queue(True, queue_timeout_sec)
            self.assertEqual(buf_recv, b"OK 999")

            # ==================================
            # CHAT END
            # ==================================

            # Stop
            logger.info("server : stopping")
            self.tcp_server.stop_server()
            logger.info("server : stopped")
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)
            self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

            # Client should be disconnected
            # Wait for client
            logger.info("client : wait for disconnection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if not self.tcp_client.is_connected:
                    break
                SolBase.sleep(int(check_timeout / 100))

            # Check
            logger.info("client : check for disconnection")
            self.assertFalse(self.tcp_client.is_connected)

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svrstart_clisend_svrreply_svrstop_withsendsignaled(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Checks
            check_timeout = 2500
            queue_timeout_sec = 5000 / 1000

            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.client_factory = TcpServerQueuedClientContextFactory()

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # ssl
            if self.test_ssl:
                client_config.ssl_enable = True

            # proxy
            if self.test_proxy:
                client_config.proxy_enable = True
                client_config.proxy_addr = "127.0.0.1"
                client_config.proxy_port = 1080

            # Client
            self.tcp_client = TcpSimpleClient(client_config)

            # Check
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Connect
            self.assertTrue(self.tcp_client.connect())

            # Check
            self.assertIsNotNone(self.tcp_client.current_socket)
            self.assertTrue(self.tcp_client.is_connected)

            # Wait for server
            logger.info("server : wait connection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if len(self.tcp_server._client_connected_hash) > 0:
                    break
                SolBase.sleep(int(check_timeout / 100))
            logger.info("server : wait connection : done")

            # Check
            self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

            # ==================================
            # CHAT INIT
            # ==================================

            # Get the server client instance
            tcp_server_client = self.tcp_server._client_connected_hash[list(self.tcp_server._client_connected_hash.keys())[0]]

            # ==================================
            # CHAT START
            # ==================================

            # Client  : send HI
            self.assertTrue(self.tcp_client.send_unicode_to_socket("HI 999"))

            # Server : wait for receive, 5 sec timeout (will raise Empty exception on timeout)
            buf_recv = tcp_server_client.get_from_receive_queue(True, queue_timeout_sec)
            self.assertEqual(buf_recv, b"HI 999")

            # Server : reply
            sb = SignaledBuffer()
            sb.binary_buffer = b"OK 999" + b"\n"
            self.assertTrue(tcp_server_client.send_binary_to_socket_with_signal(sb))

            # Send MUST be signaled
            b = sb.send_event.wait(queue_timeout_sec)
            self.assertTrue(b)

            # Client : wait for receive, 5 sec timeout (will raise Empty exception on timeout
            buf_recv = self.tcp_client.get_from_receive_queue(True, queue_timeout_sec)
            self.assertEqual(buf_recv, b"OK 999")

            # ==================================
            # CHAT END
            # ==================================

            # Stop
            logger.info("server : stopping")
            self.tcp_server.stop_server()
            logger.info("server : stopped")
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)
            self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

            # Client should be disconnected
            # Wait for client
            logger.info("client : wait for disconnection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if not self.tcp_client.is_connected:
                    break
                SolBase.sleep(int(check_timeout / 100))

            # Check
            logger.info("client : check for disconnection")
            self.assertFalse(self.tcp_client.is_connected)

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svrstart_clisend_svrreply_loopsendrecv_x2_svrstop(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Checks
            check_timeout = 2500
            queue_timeout_sec = 5000 / 1000

            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.client_factory = TcpServerQueuedClientContextFactory()

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # ssl
            if self.test_ssl:
                client_config.ssl_enable = True

            # proxy
            if self.test_proxy:
                client_config.proxy_enable = True
                client_config.proxy_addr = "127.0.0.1"
                client_config.proxy_port = 1080

            # Client
            self.tcp_client = TcpSimpleClient(client_config)

            # Check
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Connect
            self.assertTrue(self.tcp_client.connect())

            # Check
            self.assertIsNotNone(self.tcp_client.current_socket)
            self.assertTrue(self.tcp_client.is_connected)

            # Wait for server
            logger.info("server : wait connection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if len(self.tcp_server._client_connected_hash) > 0:
                    break
                SolBase.sleep(int(check_timeout / 100))
            logger.info("server : wait connection : done")

            # Check
            self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

            # ==================================
            # CHAT INIT
            # ==================================

            # Get the server client instance
            tcp_server_client = self.tcp_server._client_connected_hash[list(self.tcp_server._client_connected_hash.keys())[0]]

            # ==================================
            # CHAT START
            # ==================================

            logger.info("Loop entering")

            loop_count = 10000
            loop_cur = 0
            dt_start = SolBase.datecurrent()
            while loop_cur < loop_count:
                # Client  : send HI
                self.assertTrue(self.tcp_client.send_unicode_to_socket("HI " + str(loop_cur)))

                # Server : wait for receive, 5 sec timeout (will raise Empty exception on timeout)
                buf_recv = tcp_server_client.get_from_receive_queue(True, queue_timeout_sec)
                self.assertEqual(buf_recv, SolBase.unicode_to_binary("HI " + str(loop_cur), "utf-8"))

                # Server : reply
                self.assertTrue(tcp_server_client.send_unicode_to_socket("OK " + str(loop_cur)))

                # Client : wait for receive, 5 sec timeout (will raise Empty exception on timeout
                buf_recv = self.tcp_client.get_from_receive_queue(True, queue_timeout_sec)
                self.assertEqual(buf_recv, SolBase.unicode_to_binary("OK " + str(loop_cur), "utf-8"))

                loop_cur += 1

            # Per sec
            logger.info("Loop done")
            total_sec = SolBase.datediff(dt_start) / 1000.0
            if total_sec > 0:
                per_sec = loop_count / total_sec
            else:
                per_sec = 0
            logger.info("Loop count=%s, send/recv per sec=%s, total_sec=%s", loop_count, per_sec * 2, total_sec)

            # ==================================
            # CHAT END
            # ==================================

            # Stop
            logger.info("server : stopping")
            self.tcp_server.stop_server()
            logger.info("server : stopped")
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)
            self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

            # Client should be disconnected
            # Wait for client
            logger.info("client : wait for disconnection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if not self.tcp_client.is_connected:
                    break
                SolBase.sleep(int(check_timeout / 100))

            # Check
            logger.info("client : check for disconnection")
            self.assertFalse(self.tcp_client.is_connected)

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svrstart_clisend_svrreply_loopsendthenrecv_svrstop(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None

        try:
            # Checks
            check_timeout = 2500
            queue_timeout_sec = 5000 / 1000

            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.client_factory = TcpServerQueuedClientContextFactory()

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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

            # ssl
            if self.test_ssl:
                client_config.ssl_enable = True

            # proxy
            if self.test_proxy:
                client_config.proxy_enable = True
                client_config.proxy_addr = "127.0.0.1"
                client_config.proxy_port = 1080

            # Client
            self.tcp_client = TcpSimpleClient(client_config)

            # Check
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Connect
            self.assertTrue(self.tcp_client.connect())

            # Check
            self.assertIsNotNone(self.tcp_client.current_socket)
            self.assertTrue(self.tcp_client.is_connected)

            # Wait for server
            logger.info("server : wait connection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if len(self.tcp_server._client_connected_hash) > 0:
                    break
                SolBase.sleep(int(check_timeout / 100))
            logger.info("server : wait connection : done")

            # Check
            self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

            # ==================================
            # CHAT INIT
            # ==================================

            # Get the server client instance
            tcp_server_client = self.tcp_server._client_connected_hash[list(self.tcp_server._client_connected_hash.keys())[0]]

            # ==================================
            # CHAT START
            # ==================================

            logger.info("SendLoop : entering")

            loop_count = 10000
            loop_cur = 0
            dt_start = SolBase.datecurrent()
            while loop_cur < loop_count:
                # Client  : send HI in loop
                self.assertTrue(self.tcp_client.send_unicode_to_socket("HI " + str(loop_cur)))
                loop_cur += 1

            logger.info("SendLoop : send done")

            # Wait for queue len to zero
            client_send_len = self.tcp_client.get_send_queue_len()
            dt_last_change = SolBase.datecurrent()
            change_timeout_ms = 10000
            while client_send_len > 0:
                prev_client_send_len = client_send_len

                client_send_len = self.tcp_client.get_send_queue_len()
                client_recv_len = self.tcp_client.get_recv_queue_len()

                svr_send_len = tcp_server_client.get_send_queue_len()
                svr_recv_len = tcp_server_client.get_recv_queue_len()

                # Change ?
                if prev_client_send_len != client_send_len:
                    dt_last_change = SolBase.datecurrent()

                # Change timeout ?
                change_ms = SolBase.datediff(dt_last_change)
                if change_ms > change_timeout_ms:
                    self.fail("Change timeout in send check loop")

                logger.info(
                    "SendLoop : Wait, cli.send=%s, cli.recv=%s, svr.send=%s, svr.recv=%s, changeSec=%s",
                    client_send_len, client_recv_len, svr_send_len, svr_recv_len, change_ms / 1000.0)
                SolBase.sleep(500)

            # Per sec
            logger.info("Loop done")
            total_sec = SolBase.datediff(dt_start) / 1000.0
            if total_sec > 0:
                per_sec = loop_count / total_sec
            else:
                per_sec = 0
            logger.info("SendLoop count=%s, send per sec=%s, total_sec=%s", loop_count, per_sec, total_sec)

            # Check receive
            logger.info("RecvLoop check entering")
            loop_cur = 0
            dt_start = SolBase.datecurrent()
            while loop_cur < loop_count:
                # Server : wait for receive, 5 sec timeout (will raise Empty exception on timeout
                buf_recv = tcp_server_client.get_from_receive_queue(True, queue_timeout_sec)
                self.assertEqual(buf_recv, SolBase.unicode_to_binary("HI " + str(loop_cur)))

                loop_cur += 1

            # Per sec
            logger.info("RecvLoop check done")
            total_sec = SolBase.datediff(dt_start) / 1000.0
            if total_sec > 0:
                per_sec = loop_count / total_sec
            else:
                per_sec = 0
            logger.info("RecvLoop count=%s, recv per sec=%s, total_sec=%s", loop_count, per_sec, total_sec)

            # ==================================
            # CHAT END
            # ==================================

            # Stop
            logger.info("server : stopping")
            self.tcp_server.stop_server()
            logger.info("server : stopped")
            self.assertFalse(self.tcp_server._is_started)
            self.assertTrue(self.tcp_server._server is None)
            self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

            # Client should be disconnected
            # Wait for client
            logger.info("client : wait for disconnection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if not self.tcp_client.is_connected:
                    break
                SolBase.sleep(int(check_timeout / 100))

            # Check
            logger.info("client : check for disconnection")
            self.assertFalse(self.tcp_client.is_connected)

            # Reset
            self.tcp_server = None
            self.tcp_client = None
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcp_client:
                self.tcp_client.disconnect()

    # ====================================
    # ssl
    # ====================================

    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_cliconnect_clistop_ssl(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = False
        self.test_tcp_svrstart_cliconnect_clistop()
        self.assertTrue(self.test_ssl)
        self.assertFalse(self.test_proxy)

    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_cliconnect_svrstop_ssl(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = False
        self.test_tcp_svrstart_cliconnect_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertFalse(self.test_proxy)

    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_clisend_svrreply_loopsendrecv_x2_svrstop_ssl(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = False
        self.test_tcp_svrstart_clisend_svrreply_loopsendrecv_x2_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertFalse(self.test_proxy)

    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_clisend_svrreply_loopsendthenrecv_svrstop_ssl(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = False
        self.test_tcp_svrstart_clisend_svrreply_loopsendthenrecv_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertFalse(self.test_proxy)

    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_clisend_svrreply_svrstop_ssl(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = False
        self.test_tcp_svrstart_clisend_svrreply_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertFalse(self.test_proxy)

    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_svrstop_ssl(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = False
        self.test_tcp_svrstart_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertFalse(self.test_proxy)

    # ====================================
    # proxy
    # ====================================

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    def test_tcp_svrstart_cliconnect_clistop_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = False
        self.test_proxy = True
        self.test_tcp_svrstart_cliconnect_clistop()
        self.assertFalse(self.test_ssl)
        self.assertTrue(self.test_proxy)

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    def test_tcp_svrstart_cliconnect_svrstop_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = False
        self.test_proxy = True
        self.test_tcp_svrstart_cliconnect_svrstop()
        self.assertFalse(self.test_ssl)
        self.assertTrue(self.test_proxy)

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    def test_tcp_svrstart_clisend_svrreply_loopsendrecv_x2_svrstop_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = False
        self.test_proxy = True
        self.test_tcp_svrstart_clisend_svrreply_loopsendrecv_x2_svrstop()
        self.assertFalse(self.test_ssl)
        self.assertTrue(self.test_proxy)

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    def test_tcp_svrstart_clisend_svrreply_loopsendthenrecv_svrstop_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = False
        self.test_proxy = True
        self.test_tcp_svrstart_clisend_svrreply_loopsendthenrecv_svrstop()
        self.assertFalse(self.test_ssl)
        self.assertTrue(self.test_proxy)

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    def test_tcp_svrstart_clisend_svrreply_svrstop_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = False
        self.test_proxy = True
        self.test_tcp_svrstart_clisend_svrreply_svrstop()
        self.assertFalse(self.test_ssl)
        self.assertTrue(self.test_proxy)

    # ====================================
    # proxy + ssl
    # ====================================

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_cliconnect_clistop_ssl_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = True
        self.test_tcp_svrstart_cliconnect_clistop()
        self.assertTrue(self.test_ssl)
        self.assertTrue(self.test_proxy)

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_cliconnect_svrstop_ssl_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = True
        self.test_tcp_svrstart_cliconnect_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertTrue(self.test_proxy)

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_clisend_svrreply_loopsendrecv_x2_svrstop_ssl_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = True
        self.test_tcp_svrstart_clisend_svrreply_loopsendrecv_x2_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertTrue(self.test_proxy)

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_clisend_svrreply_loopsendthenrecv_svrstop_ssl_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = True
        self.test_tcp_svrstart_clisend_svrreply_loopsendthenrecv_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertTrue(self.test_proxy)

    @unittest.skipIf(not is_dante_detected(), "Need dante")
    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_clisend_svrreply_svrstop_ssl_proxy(self):
        """
        Test.
        :return: Nothing.
        """
        self.test_ssl = True
        self.test_proxy = True
        self.test_tcp_svrstart_clisend_svrreply_svrstop()
        self.assertTrue(self.test_ssl)
        self.assertTrue(self.test_proxy)

    # ==============================
    # ssl HANDSHAKE TIMEOUT
    # ==============================

    @unittest.skipIf(not ENABLE_SSL, "ENABLE_SSL False")
    def test_tcp_svrstart_cliconnect_clistop_sslhandshake_timeout(self):
        """
        Test

        """

        # Instances
        self.tcp_server = None
        self.tcp_client = None
        self.test_ssl = True

        try:
            # Checks
            check_timeout = 2500

            # Config
            server_config = TcpServerConfig()
            server_config.listen_addr = "127.0.0.1"
            server_config.listen_port = 3201
            server_config.ssl_handshake_timeout_ms = 500

            # This force a timeout INSIDE the server (TcpSocketManager class)
            server_config.debug_waitinsslms = 1000

            # Config : ssl ON
            if self.test_ssl:
                server_config.ssl_enable = True
                server_config.ssl_key_file = self.certificates_path + "server.key"
                server_config.ssl_certificate_file = self.certificates_path + "server.crt"

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
            client_config.debugWaitBeforeSslMs = None

            # ssl
            if self.test_ssl:
                client_config.ssl_enable = True

            # proxy
            if self.test_proxy:
                client_config.proxy_enable = True
                client_config.proxy_addr = "127.0.0.1"
                client_config.proxy_port = 1080

            # Client
            self.tcp_client = TcpSimpleClient(client_config)

            # Check
            self.assertTrue(self.tcp_client.current_socket is None)
            self.assertFalse(self.tcp_client.is_connected)

            # Connect
            logger.info("Starting connect()")
            self.assertTrue(self.tcp_client.connect())
            logger.info("Starting connect() : ok")

            # Check client
            self.assertIsNotNone(self.tcp_client.current_socket)
            self.assertTrue(self.tcp_client.is_connected)

            # Wait for server
            logger.info("server : wait for ssl timeout")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if Meters.aig("tcp.server.ssl_handshake_timeout_count") == 1 and self.tcp_server._client_connected_hash == 0:
                    break
                SolBase.sleep(int(check_timeout / 100))
            logger.info("server : wait for ssl timeout : done")

            # Check
            self.assertEqual(Meters.aig("tcp.server.ssl_handshake_timeout_count"), 1)
            self.assertEqual(len(self.tcp_server._client_connected_hash), 0)

            # Client must be disconnect
            self.assertFalse(self.tcp_client.is_connected)

            # Reset client
            self.tcp_client = None

            # Server should be disconnected from client
            # Wait for server
            logger.info("server : wait for disconnection")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < check_timeout:
                if len(self.tcp_server._client_connected_hash) == 0:
                    break
                SolBase.sleep(int(check_timeout / 100))

            # Check
            logger.info("server : check for disconnection")
            self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

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
