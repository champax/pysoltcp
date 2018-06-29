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

from pysolbase.FileUtility import FileUtility
from pysolbase.SolBase import SolBase
from pysolmeters.Meters import Meters

from pysoltcp.tcpclient.TcpClientConfig import TcpClientConfig
from pysoltcp.tcpserver.TcpServer import TcpServer
from pysoltcp.tcpserver.TcpServerConfig import TcpServerConfig
from pysoltcp_test.TcpApi import is_dante_detected
from pysoltcp_test.TcpApi.PingProtocol.Client.PingSimpleClient import PingSimpleClient
from pysoltcp_test.TcpApi.PingProtocol.PingTestTools import PingTestTools
from pysoltcp_test.TcpApi.PingProtocol.Server.PingServerContextFactory import PingServerContextFactory
from pysoltcp_test.Utility import Utility

SolBase.logging_init()
logger = logging.getLogger(__name__)


# ============================================
# Unit src class
# ============================================


class TestBenchTcpPing(unittest.TestCase):
    """
    Test description
    """

    def setUp(self):
        """
        Setup

        """

        SolBase.voodoo_init()
        Utility.gevent_reset()
        Utility.test_wait()

        # Init
        self.tcp_server = None
        self.arTcpClient = None

        # Config server
        self.serverHelloTimeOutMs = 30000
        self.serverPingIntervalMs = 10000
        self.serverPingTimeOutMs = 60000

        # Config client
        self.clientHelloTimeOutMs = 30000
        self.clientPingIntervalMs = 10000
        self.clientPingTimeOutMs = 60000

        # Config test
        self.runTimeMs = 20000
        self.statEveryMs = 10000
        self.checkTimeOutMs = 60000

        # Client config test
        self.clientMaxCount = 5

        # Misc
        self.expectedPps = 0

        # Debug
        self.debug_log = False

        # Reset
        Meters.reset()

        # ssl
        self.testSsl = False
        self.testProxy = False
        self.certificatesPath = Utility.generate_server_keys()

    def tearDown(self):
        """
        Setup (called on destroy)

        """

        # noinspection PyBroadException
        try:
            self._stop_multi_client()
        except Exception:
            pass

        # noinspection PyBroadException
        try:
            self._stop_server_and_check()
        except Exception:
            pass

        # Wait a bit
        Utility.test_wait()

    def _start_server_and_check(self):
        """
        Test

        """
        # Config
        server_config = TcpServerConfig()
        server_config.listen_addr = "127.0.0.1"
        server_config.listen_port = 3201
        server_config.client_factory = PingServerContextFactory(
            self.serverHelloTimeOutMs,
            self.serverPingIntervalMs,
            self.serverPingTimeOutMs)

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

    # =================================
    # TEST : MULTI CLIENT STOP/START
    # =================================

    def _start_multi_client(self, client_count):
        """
        Test
        :param client_count: Client count.

        """

        # Client config
        client_config = TcpClientConfig()
        client_config.target_addr = "127.0.0.1"
        client_config.target_port = 3201
        client_config.debug_log = self.debug_log

        # ssl
        if self.testSsl:
            client_config.ssl_enable = True

        # Proxy ?
        if self.testProxy:
            client_config.proxy_enable = True
            client_config.proxy_addr = "127.0.0.1"
            client_config.proxy_port = 1080

        # --------------------------------
        # Client array : allocate
        # --------------------------------
        logger.info("allocating, client_count=%s", client_count)
        self.arTcpClient = list()
        dt_cur = SolBase.datecurrent()
        for _ in range(client_count):
            # Alloc
            local_client = PingSimpleClient(
                client_config,
                self.clientHelloTimeOutMs,
                self.clientPingIntervalMs,
                self.clientPingTimeOutMs)

            # Register
            self.arTcpClient.append(local_client)

            # Check
            self.assertTrue(local_client.current_socket is None)
            self.assertFalse(local_client.is_connected)

            if SolBase.datediff(dt_cur) > 1000:
                dt_cur = SolBase.datecurrent()
                logger.info("allocating, client_count=%s, done=%s", client_count, len(self.arTcpClient))

        logger.info("allocating, client_count=%s, done=%s", client_count, len(self.arTcpClient))

        # --------------------------------
        # Client array : start
        # --------------------------------
        logger.info("connecting, client_count=%s", client_count)
        dt_start = SolBase.datecurrent()
        dt_cur = SolBase.datecurrent()
        connected_count = 0
        for local_client in self.arTcpClient:
            # Connect
            self.assertTrue(local_client.connect())

            # Check client
            self.assertIsNotNone(local_client.current_socket)
            self.assertTrue(local_client.is_connected)

            connected_count += 1

            if SolBase.datediff(dt_cur) > 1000:
                dt_cur = SolBase.datecurrent()
                elapsed_ms = SolBase.datediff(dt_start)
                if elapsed_ms > 0:
                    connect_per_sec = client_count / (elapsed_ms * 0.001)
                else:
                    connect_per_sec = 0
                logger.info("connecting, client_count=%s, connected_count=%s, perSec=%.2f", client_count, connected_count, connect_per_sec)

        elapsed_ms = SolBase.datediff(dt_start)
        if elapsed_ms > 0:
            connect_per_sec = client_count / (elapsed_ms * 0.001)
        else:
            connect_per_sec = 0
        logger.info("connecting, client_count=%s, connected_count=%s, perSec=%.2f", client_count, connected_count, connect_per_sec)

        # --------------------------------
        # Wait for server
        # --------------------------------
        logger.info("waiting for server")
        dt_start = SolBase.datecurrent()
        while SolBase.datediff(dt_start) < self.checkTimeOutMs:
            if len(self.tcp_server._client_connected_hash) == client_count:
                break
            logger.info("waiting for server : connected=%s, target=%s", len(self.tcp_server._client_connected_hash), client_count)
            SolBase.sleep(int(self.checkTimeOutMs / 100))

        logger.info("waiting for server : done : connected=%s, target=%s", len(self.tcp_server._client_connected_hash), client_count)

        # Check
        self.assertEqual(len(self.tcp_server._client_connected_hash), client_count)

        # --------------------------------
        # Done
        # --------------------------------
        logger.info("all client connected")

    def _stop_multi_client(self):
        """
        Test

        """

        if self.arTcpClient is None:
            return

        # --------------------------------
        # Disconnect
        # --------------------------------

        logger.info("disconnecting, clientCount=%s", len(self.arTcpClient))
        ko_count_socket = 0
        ko_count_is_connected = 0
        for local_client in self.arTcpClient:
            # Kill client
            local_client.disconnect()

            # Check client
            if local_client.current_socket:
                ko_count_socket += 1
            if local_client.is_connected:
                ko_count_is_connected += 1

        if ko_count_socket == 0 and ko_count_is_connected == 0:
            logger.info("disconnecting, ko_count_socket=%s, ko_count_is_connected=%s", ko_count_socket, ko_count_is_connected)
        else:
            logger.error("disconnecting, ko_count_socket=%s, ko_count_is_connected=%s", ko_count_socket, ko_count_is_connected)

        # --------------------------------
        # Clean up
        # --------------------------------
        self.arTcpClient = None

        # --------------------------------
        # Server should be disconnected from client
        # Wait for server
        # --------------------------------
        logger.info("wait for server disconnection")
        dt_start = SolBase.datecurrent()
        while SolBase.datediff(dt_start) < self.checkTimeOutMs:
            # Check
            if len(self.tcp_server._client_connected_hash) == 0:
                break

            # Log
            logger.info("waiting for server : connected/target=%s/0", len(self.tcp_server._client_connected_hash))

            # Wait
            SolBase.sleep(int(self.checkTimeOutMs / 100))

        # Check
        logger.info("check for disconnection")
        self.assertTrue(len(self.tcp_server._client_connected_hash) == 0)
        self.assertTrue(ko_count_socket == 0)
        self.assertTrue(ko_count_is_connected == 0)

        # Done
        logger.info("all done")

    def _start_multi_client_checkallping_stop(self):
        """
        Test

        """

        # Start
        self._start_multi_client(self.clientMaxCount)

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

        flush_stat_inloop = False
        dt = SolBase.datecurrent()
        dt_stat = SolBase.datecurrent()
        dt_loop = SolBase.datecurrent()
        client_prev_completed_ping = 0
        server_prev_completed_ping = 0
        while SolBase.datediff(dt) < self.runTimeMs:
            # Wait
            SolBase.sleep(1000)

            # Client
            client_ko = PingTestTools.get_client_ko_count(False, self.clientMaxCount)

            # Server
            server_ko = PingTestTools.get_server_ko_count(False, self.clientMaxCount)

            # Total ping
            client_total_completed_ping = Meters.aig("ping.client.client_ping_server_reply")
            server_total_completed_ping = Meters.aig("ping.server.serverPingClientReply")

            # Current ping
            client_local_completed_ping = client_total_completed_ping - client_prev_completed_ping
            server_local_completed_ping = server_total_completed_ping - server_prev_completed_ping

            # Store prev
            client_prev_completed_ping = client_total_completed_ping
            server_prev_completed_ping = server_total_completed_ping

            # Elapsed ms
            elapsed_ms = SolBase.datediff(dt_loop)
            elapsed_total_ms = SolBase.datediff(dt)

            # Ping per sec.
            client_local_pps = (client_local_completed_ping / (elapsed_ms / 1000.0))
            server_local_pps = (server_local_completed_ping / (elapsed_ms / 1000.0))

            client_avg_pps = (client_total_completed_ping / (elapsed_total_ms / 1000.0))
            server_avg_pps = (server_total_completed_ping / (elapsed_total_ms / 1000.0))

            # Reset date
            dt_loop = SolBase.datecurrent()

            # Wait
            logger.info(
                "Running : ko=%s:%s, sec=%s/%s, cli.ping=%s, svr.ping=%s, exp.pps=%.2f, "
                "cli.pps=%.2f, svr.pps=%.2f, cli.aps=%.2f, svr.aps=%.2f",
                client_ko, server_ko,
                int(SolBase.datediff(dt) / 1000), int(self.runTimeMs / 1000),
                client_local_completed_ping, server_local_completed_ping,
                self.expectedPps,
                client_local_pps, server_local_pps,
                client_avg_pps, server_avg_pps
            )

            # Stat
            if flush_stat_inloop and SolBase.datediff(dt_stat) > self.statEveryMs:
                Meters.write_to_logger()
                dt_stat = SolBase.datecurrent()

        # Final check
        client_ko = PingTestTools.get_client_ko_count(True, self.clientMaxCount)
        server_ko = PingTestTools.get_server_ko_count(True, self.clientMaxCount)
        self.assertEqual(client_ko, 0)
        self.assertEqual(server_ko, 0)

        # Stop
        self._stop_multi_client()

    # =================================
    # BENCH
    # =================================

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_bench_cli10_ping100(self):
        """
        Test

        """

        self.debug_log = False
        self._internal_test(10, 100)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli1000_ping10000(self):
        """
        Test

        """

        self._internal_test(1000, 10000)

    @unittest.skip("Medium aggressive benchmark. Requires2 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli2000_ping10000(self):
        """
        Test

        """

        self._internal_test(2000, 10000)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli10000_ping10000(self):
        """
        Test

        """

        self._internal_test(10000, 10000)

    @unittest.skip("Highly aggressive benchmark. Requires 3 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli40000_ping40000_run480000(self):
        """
        Test

        """

        # Raise timeout
        self.serverPingTimeOutMs = 180000
        self.clientPingTimeOutMs = 180000

        # Go
        self._internal_test(10000 * 4, 10000 * 4, 120000 * 4)

    @unittest.skip("Extreme aggressive benchmark. Requires 4 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli60000_ping60000_run720000(self):
        """
        Test

        """

        # Raise timeout
        self.serverPingTimeOutMs = 180000
        self.clientPingTimeOutMs = 180000

        self._internal_test(10000 * 6, 10000 * 6, 120000 * 6)

    # =================================
    # BENCH ssl
    # =================================

    # @unittest.skip("gevent 1.1.1 zzzzz")
    def test_bench_cli10_ping100_ssl(self):
        """
        Test

        """

        self.debug_log = False
        self.testSsl = True
        self._internal_test(10, 100)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli1000_ping10000_ssl(self):
        """
        Test

        """

        self.testSsl = True
        self._internal_test(1000, 10000)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli2000_ping10000_ssl(self):
        """
        Test

        """

        self.testSsl = True
        self._internal_test(2000, 10000)

    @unittest.skip("Medium aggressive benchmark. Requires2 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli10000_ping10000_ssl(self):
        """
        Test

        """

        self.testSsl = True
        self._internal_test(10000, 10000)

    @unittest.skip("Highly aggressive benchmark. Requires 3 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli40000_ping40000_run480000_ssl(self):
        """
        Test

        """

        # Raise timeout
        self.serverPingTimeOutMs = 180000
        self.clientPingTimeOutMs = 180000

        # Go
        self.testSsl = True
        self._internal_test(10000 * 4, 10000 * 4, 120000 * 4)

    @unittest.skip("Extreme aggressive benchmark. Requires 4 GB free memory, Tuned TCP stack, Tuned OS.")
    def test_bench_cli60000_ping60000_run720000_ssl(self):
        """
        Test

        """

        # Raise timeout
        self.serverPingTimeOutMs = 180000
        self.clientPingTimeOutMs = 180000

        self.testSsl = True
        self._internal_test(10000 * 6, 10000 * 6, 120000 * 6)

    # =================================
    # BENCH proxy
    # =================================

    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli10_ping100_proxy(self):
        """
        Test

        """

        self.debug_log = False
        self.testSsl = False
        self.testProxy = True
        self._internal_test(10, 100)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli1000_ping10000_proxy(self):
        """
        Test

        """

        self.testSsl = False
        self.testProxy = True
        self._internal_test(1000, 10000)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli2000_ping10000_proxy(self):
        """
        Test

        """

        self.testSsl = False
        self.testProxy = True
        self._internal_test(2000, 10000)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli10000_ping10000_proxy(self):
        """
        Test

        """

        self.testSsl = False
        self.testProxy = True
        self._internal_test(10000, 10000)

    @unittest.skip("Highly aggressive benchmark. Requires 3 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli40000_ping40000_run480000_proxy(self):
        """
        Test

        """

        # Raise timeout
        self.serverPingTimeOutMs = 180000
        self.clientPingTimeOutMs = 180000

        # Go
        self.testSsl = False
        self.testProxy = True
        self._internal_test(10000 * 4, 10000 * 4, 120000 * 4)

    @unittest.skip("Extreme aggressive benchmark. Requires 4 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli60000_ping60000_run720000_proxy(self):
        """
        Test

        """

        # Raise timeout
        self.serverPingTimeOutMs = 180000
        self.clientPingTimeOutMs = 180000

        self.testSsl = False
        self.testProxy = True
        self._internal_test(10000 * 6, 10000 * 6, 120000 * 6)

    # =================================
    # BENCH proxy + ssl
    # =================================

    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli10_ping100_proxy_ssl(self):
        """
        Test

        """

        self.debug_log = False
        self.testSsl = True
        self.testProxy = True
        self._internal_test(10, 100)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli1000_ping10000_proxy_ssl(self):
        """
        Test

        """

        self.testSsl = True
        self.testProxy = True
        self._internal_test(1000, 10000)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli2000_ping10000_proxy_ssl(self):
        """
        Test

        """

        self.testSsl = True
        self.testProxy = True
        self._internal_test(2000, 10000)

    @unittest.skip("Medium aggressive benchmark. Requires 2 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli10000_ping10000_proxy_ssl(self):
        """
        Test

        """

        self.testSsl = True
        self.testProxy = True
        self._internal_test(10000, 10000)

    @unittest.skip("Highly aggressive benchmark. Requires 3 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli40000_ping40000_run480000_proxy_ssl(self):
        """
        Test

        """

        # Raise timeout
        self.serverPingTimeOutMs = 180000
        self.clientPingTimeOutMs = 180000

        # Go
        self.testSsl = True
        self.testProxy = True
        self._internal_test(10000 * 4, 10000 * 4, 120000 * 4)

    @unittest.skip("Extreme aggressive benchmark. Requires 4 GB free memory, Tuned TCP stack, Tuned OS.")
    @unittest.skipIf(is_dante_detected() == False, "Need dante")
    def test_bench_cli60000_ping60000_run720000_proxy_ssl(self):
        """
        Test

        """

        # Raise timeout
        self.serverPingTimeOutMs = 180000
        self.clientPingTimeOutMs = 180000

        self.testSsl = True
        self.testProxy = True
        self._internal_test(10000 * 6, 10000 * 6, 120000 * 6)

    # =================================
    # INTERNAL TEST
    # =================================

    def _internal_test(self, client_count, ping_interval_ms, my_run_time_ms=20000):
        """
        Test.
        :param client_count: Client count.
        :param ping_interval_ms: Ping interval in millis.
        :param my_run_time_ms: Run time in millis.
        :return: nothing.
        """
        try:
            # Overrides statics (beuuurk but so gooood)
            self.clientMaxCount = client_count
            self.serverPingIntervalMs = ping_interval_ms
            self.clientPingIntervalMs = ping_interval_ms
            self.runTimeMs = my_run_time_ms

            # Expected server and client ping/src
            self.expectedPps = (float(self.clientMaxCount) / float(self.serverPingIntervalMs)) * 1000.0

            logger.info("starting, client=%s, ping.ms=%s, expected.pps=%s", client_count, ping_interval_ms, self.expectedPps)

            # Instance
            self.tcp_server = None

            try:
                # Start server
                self._start_server_and_check()

                # Start client, check and stop client
                self._start_multi_client_checkallping_stop()

                # Stop server
                self._stop_server_and_check()

            except Exception as e:
                logger.error("Exception in test, ex=%s", SolBase.extostr(e))
                raise
            finally:
                if self.tcp_server:
                    self.tcp_server.stop_server()
        finally:
            # Final stats
            logger.info("Finished, final stats bellow")
            Meters.write_to_logger()

            # Reset
            self.tcp_server = None

            # Sleep
            Utility.test_wait()
