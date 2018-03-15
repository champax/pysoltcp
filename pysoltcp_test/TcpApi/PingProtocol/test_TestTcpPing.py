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

from pysolbase.SolBase import SolBase
from pysolmeters.Meters import Meters

from pysoltcp.tcpclient.TcpClientConfig import TcpClientConfig
from pysoltcp.tcpserver.TcpServer import TcpServer
from pysoltcp.tcpserver.TcpServerConfig import TcpServerConfig
from pysoltcp_test.TcpApi.PingProtocol.Client.PingSimpleClient import PingSimpleClient
from pysoltcp_test.TcpApi.PingProtocol.PingTestTools import PingTestTools
from pysoltcp_test.TcpApi.PingProtocol.Server.PingServerContextFactory import PingServerContextFactory
from pysoltcp_test.TcpApi.PingProtocol.ServerDeadlock.PingDeadlockServerContextFactory import PingDeadlockServerContextFactory
from pysoltcp_test.Utility import Utility

SolBase.logging_init()
logger = logging.getLogger(__name__)


# ============================================
# Unit src class
# ============================================


class TestTcpPing(unittest.TestCase):
    """
    Test description
    """

    def setUp(self):
        """
        Setup

        """

        Utility.gevent_reset()
        SolBase.voodoo_init()
        Utility.test_wait()

        # Init
        self.tcp_server = None
        self.tcpClient = None

        # Config server
        self.serverHelloTimeOutMs = 10000
        self.serverPingIntervalMs = 10000
        self.serverPingTimeoutMs = 10000

        # Config client
        self.clientHelloTimeOutMs = 10000
        self.clientPingIntervalMs = 10000
        self.clientPingTimeOutMs = 10000

        # Config test
        self.checkTimeOutMs = 10000
        self.checkPingTimeOutMs = 30000

        # Client config test
        self.clientMaxCount = 10000
        self.clientWaitMsBetweenSegment = 5000
        self.clientSegment = 100

        # Reset
        Meters.reset()

        # ssl
        self.testSsl = False
        self.certificatesPath = Utility.generate_server_keys()

    def tearDown(self):
        """
        Setup (called on destroy)

        """

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

    def _start_server_and_check(self, deadlock=False):
        """
        Test

        :param deadlock: If true, use a server context that deadlock on stop
        :type deadlock: bool
        """
        # Config
        server_config = TcpServerConfig()
        server_config.listen_addr = "127.0.0.1"
        server_config.listen_port = 3201
        if not deadlock:
            server_config.client_factory = PingServerContextFactory(
                self.serverHelloTimeOutMs, self.serverPingIntervalMs,
                self.serverPingTimeoutMs)
        else:
            server_config.client_factory = PingDeadlockServerContextFactory(
                self.serverHelloTimeOutMs,
                self.serverPingIntervalMs,
                self.serverPingTimeoutMs)
            # Lower the default values
            server_config.stop_client_timeout_ms = 1000

        # Config : ssl ON
        if self.testSsl:
            server_config.ssl_enable = True
            server_config.ssl_key_file = self.certificatesPath + "server.key"
            server_config.ssl_certificate_file = self.certificatesPath + "server.crt"

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

    def _stop_server_and_check(self):
        """
        Test

        """
        # Stop
        self.tcp_server.stop_server()
        self.assertFalse(self.tcp_server._is_started)
        self.assertTrue(self.tcp_server._server is None)

        # Reset
        self.tcp_server = None

    def _stop_server_and_check_withoneclientconnected(self):
        """
        Test

        """
        # Check
        logger.info("TestLog : server : get server context")
        self.assertTrue(len(self.tcp_server._client_connected_hash) == 1)
        ctx = None
        for cur in self.tcp_server._client_connected_hash.values():
            ctx = cur
            break

        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.stop_synchCalled, False)
        self.assertEqual(ctx.stop_synch_internalCalled, False)

        # Stop
        self.tcp_server.stop_server()
        self.assertFalse(self.tcp_server._is_started)
        self.assertTrue(self.tcp_server._server is None)

        # Check
        if not self.tcp_server._tcp_server_config.onstop_call_client_stopsynch:
            # Default...
            logger.info("Checking onstop_call_client_stopsynch=%s", self.tcp_server._tcp_server_config.onstop_call_client_stopsynch)
            self.assertEqual(ctx.stop_synchCalled, False)
            self.assertEqual(ctx.stop_synch_internalCalled, True)
        else:
            # Force call on stop
            logger.info("Checking onstop_call_client_stopsynch=%s", self.tcp_server._tcp_server_config.onstop_call_client_stopsynch)
            self.assertEqual(ctx.stop_synchCalled, True)
            self.assertEqual(ctx.stop_synch_internalCalled, True)

        # Reset
        self.tcp_server = None

    def _start_one_client_checkstop(self):
        """
        Test

        """

        # Start
        self._start_one_client()

        # Wait
        SolBase.sleep(1000)

        # Stop
        self._stop_one_client()

    def _start_one_client(self):
        """
        Test

        """

        # Client config
        client_config = TcpClientConfig()
        client_config.target_addr = "127.0.0.1"
        client_config.target_port = 3201
        client_config.debug_log = True

        # ssl
        if self.testSsl:
            client_config.ssl_enable = True

        # Client
        self.tcpClient = PingSimpleClient(client_config, self.clientHelloTimeOutMs, self.clientPingIntervalMs, self.clientPingTimeOutMs)

        # Check
        self.assertTrue(self.tcpClient.current_socket is None)
        self.assertFalse(self.tcpClient.is_connected)

        # Connect
        self.assertTrue(self.tcpClient.connect())

        # Check client
        self.assertIsNotNone(self.tcpClient.current_socket)
        self.assertTrue(self.tcpClient.is_connected)

        # Wait for server
        logger.info("TestLog : server : wait connection")
        dt_start = SolBase.datecurrent()
        while SolBase.datediff(dt_start) < self.checkTimeOutMs:
            if len(self.tcp_server._client_connected_hash) > 0:
                break
            SolBase.sleep(int(self.checkTimeOutMs / 100))
        logger.info("TestLog : server : wait connection : done")

        # Check
        self.assertEqual(len(self.tcp_server._client_connected_hash), 1)

    def _stop_one_client(self):
        """
        Test

        """

        # Check
        logger.info("TestLog : server : get server context")
        self.assertTrue(len(self.tcp_server._client_connected_hash) == 1)
        ctx = None
        for cur in self.tcp_server._client_connected_hash.values():
            ctx = cur
            break

        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.stop_synchCalled, False)
        self.assertEqual(ctx.stop_synch_internalCalled, False)

        # Kill client
        self.tcpClient.disconnect()

        # Check client
        self.assertTrue(self.tcpClient.current_socket is None)
        self.assertFalse(self.tcpClient.is_connected)

        # Reset client
        self.tcpClient = None

        # Server should be disconnected from client
        # Wait for server
        logger.info("TestLog : server : wait for disconnection")
        dt_start = SolBase.datecurrent()
        while SolBase.datediff(dt_start) < self.checkTimeOutMs:
            ok = True
            if len(self.tcp_server._client_connected_hash) != 0:
                ok = False
            elif not ctx.stop_synchCalled:
                ok = False
            elif not ctx.stop_synch_internalCalled:
                ok = False

            if ok:
                logger.info("TestLog : server : wait for disconnection : done")
                break
            else:
                SolBase.sleep(int(self.checkTimeOutMs / 100))

        # Check
        logger.info("TestLog : server : check for disconnection")
        self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)

        # Check
        self.assertEqual(ctx.stop_synchCalled, True)
        self.assertEqual(ctx.stop_synch_internalCalled, True)

    # =================================
    # TEST : CLIENT STOP/START
    # =================================

    def _start_one_client_checkallping_stop(self):
        """
        Test

        """

        # Start
        self._start_one_client()

        # Here we must wait
        # 1) Client : already connected, must
        #       - send hello, have a reply
        #       - send a ping, have a reply
        #       - reply to one server ping
        # 2) Server
        #       - receive a hello and reply
        #       - send a ping, have a reply
        #       - reply to one client ping
        # => We check using the static PingStatXXX

        dt = SolBase.datecurrent()
        while SolBase.datediff(dt) < self.checkPingTimeOutMs:
            # Client
            client_ko = PingTestTools.get_client_ko_count()

            # Server
            server_ko = PingTestTools.get_server_ko_count()

            # Check full ok
            if client_ko == 0 and server_ko == 0:
                break

            # Wait
            logger.info("Test : client_ko=%s, server_ko=%s", client_ko, server_ko)
            SolBase.sleep(1000)

        # Final check
        client_ko = PingTestTools.get_client_ko_count(True)
        server_ko = PingTestTools.get_server_ko_count(True)
        self.assertEqual(client_ko, 0)
        self.assertEqual(server_ko, 0)

        # Stop
        self._stop_one_client()

    # =================================
    # TEST : CLIENT STOP/START
    # =================================

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svr_start_cli_connect(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        try:
            # Start server
            self._start_server_and_check()

            # Start client, check and stop client
            self._start_one_client_checkstop()

            # Stop server
            self._stop_server_and_check()

        except Exception as e:
            logger.error("Exception in test, ex=%s", SolBase.extostr(e))
            raise
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svr_start_cli_connect_clidisco_clicanreco_deadlock(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        try:
            # Start server
            self._start_server_and_check(deadlock=True)

            # Start client, check and stop client
            self._start_one_client_checkstop()

            # Check stats
            logger.info("TestLog : server : wait for timeout on stop calls")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < self.checkTimeOutMs:
                ok = True
                if Meters.aig("tcp.server.client_remove_timeout_internal") != 1:
                    ok = False
                elif Meters.aig("tcp.server.client_remove_timeout_business") != 1:
                    ok = False

                if ok:
                    logger.info("TestLog : server : wait for timeout on stop calls : done")
                    break
                else:
                    SolBase.sleep(int(self.checkTimeOutMs / 100))

            # Check
            self.assertEqual(Meters.aig("tcp.server.client_remove_timeout_internal"), 1)
            self.assertEqual(Meters.aig("tcp.server.client_remove_timeout_business"), 1)

            # Start client, check and stop client
            self._start_one_client_checkstop()

            # Check stats
            logger.info("TestLog : server : wait for timeout on stop calls")
            dt_start = SolBase.datecurrent()
            while SolBase.datediff(dt_start) < self.checkTimeOutMs:
                ok = True
                if Meters.aig("tcp.server.client_remove_timeout_internal") != 2:
                    ok = False
                elif Meters.aig("tcp.server.client_remove_timeout_business") != 2:
                    ok = False

                if ok:
                    logger.info("TestLog : server : wait for timeout on stop calls : done")
                    break
                else:
                    SolBase.sleep(int(self.checkTimeOutMs / 100))

            # Check
            self.assertEqual(Meters.aig("tcp.server.client_remove_timeout_internal"), 2)
            self.assertEqual(Meters.aig("tcp.server.client_remove_timeout_business"), 2)
        except Exception as e:
            logger.error("Exception in test, ex=%s", SolBase.extostr(e))
            raise
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svr_start_cli_connect_svrstop_onstopfalse(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        try:
            # Start server
            self._start_server_and_check()

            # Force not call
            self.tcp_server._tcp_server_config.onstop_call_client_stopsynch = False

            # Start client
            self._start_one_client()

            # Stop server
            self._stop_server_and_check_withoneclientconnected()

        except Exception as e:
            logger.error("Exception in test, ex=%s", SolBase.extostr(e))
            raise
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svr_start_cli_connect_svrstop_onstoptrue(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        try:
            # Start server
            self._start_server_and_check()

            # Force not call
            self.tcp_server._tcp_server_config.onstop_call_client_stopsynch = True

            # Start client, check and stop client
            self._start_one_client()

            # Stop server
            self._stop_server_and_check_withoneclientconnected()

        except Exception as e:
            logger.error("Exception in test, ex=%s", SolBase.extostr(e))
            raise
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    # =================================
    # TEST : CLIENT AND SERVER PING LOOP
    # =================================

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svr_start_cli_connectallpingcheck(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        try:
            # Start server
            self._start_server_and_check()

            # Start client, check and stop client
            self._start_one_client_checkallping_stop()

            # Stop server
            self._stop_server_and_check()

        except Exception as e:
            logger.error("Exception in test, ex=%s", SolBase.extostr(e))
            raise
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    # =================================
    # TEST : CLIENT STOP/START
    # =================================

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svr_start_cli_connect_ssl(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        # ssl
        self.testSsl = True

        try:
            # Start server
            self._start_server_and_check()

            # Start client, check and stop client
            self._start_one_client_checkstop()

            # Stop server
            self._stop_server_and_check()

        except Exception as e:
            logger.error("Exception in test, ex=%s", SolBase.extostr(e))
            raise
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()

    # =================================
    # TEST : CLIENT AND SERVER PING LOOP
    # =================================

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_tcp_svr_start_cli_connectallpingcheck_ssl(self):
        """
        Test

        """

        # Instance
        self.tcp_server = None

        # ssl
        self.testSsl = True

        try:
            # Start server
            self._start_server_and_check()

            # Start client, check and stop client
            self._start_one_client_checkallping_stop()

            # Stop server
            self._stop_server_and_check()

        except Exception as e:
            logger.error("Exception in test, ex=%s", SolBase.extostr(e))
            raise
        finally:
            if self.tcp_server:
                self.tcp_server.stop_server()
            if self.tcpClient:
                self.tcpClient.disconnect()
