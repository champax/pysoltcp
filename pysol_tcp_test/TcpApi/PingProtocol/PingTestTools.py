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

# Imports
import logging

from pysol_meters.Meters import Meters

logger = logging.getLogger(__name__)


class PingTestTools(object):
    """
    Test
    """

    def __init__(self):
        """
        Constructor: do nothing here.
        :return Nothing
        """

    # =================================
    # STAT : CHECK
    # =================================

    @classmethod
    def get_client_ko_count(cls, log_ko=False, target_client=1):
        """
        Test
        :param log_ko: If true, log ko enabled.
        :param target_client: Target client count.
        :return An integer.
        """
        client_ko = 0

        # Client : connect
        if Meters.aig("ping.client.client_connect_count") != target_client:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_connect_count=%s", Meters.aig("ping.client.client_connect_count"))

        if Meters.aig("ping.client.client_connect_error") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_connect_error=%s", Meters.aig("ping.client.client_connect_error"))

        if Meters.aig("ping.client.client_disconnect_count") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_disconnect_count=%s", Meters.aig("ping.client.client_disconnect_count"))

        # Client : hello
        if Meters.aig("ping.client.client_hello_sent") != target_client:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_hello_sent=%s", Meters.aig("ping.client.client_hello_sent"))

        if Meters.aig("ping.client.client_hello_server_reply") != target_client:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_hello_server_reply=%s", Meters.aig("ping.client.client_hello_server_reply"))

        if Meters.aig("ping.client.client_hello_server_timeout") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_hello_server_timeout=%s", Meters.aig("ping.client.client_hello_server_timeout"))

        # Client : ping
        if Meters.aig("ping.client.client_ping_sent") == 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_ping_sent=%s", Meters.aig("ping.client.client_ping_sent"))

        if Meters.aig("ping.client.client_ping_server_reply") == 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_ping_server_reply=%s", Meters.aig("ping.client.client_ping_server_reply"))

        if Meters.aig("ping.client.client_ping_server_reply_noping_ongoing") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_ping_server_reply_noping_ongoing=%s", Meters.aig("ping.client.client_ping_server_reply_noping_ongoing"))

        if Meters.aig("ping.client.client_pingserver_timeout") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_pingserver_timeout=%s", Meters.aig("ping.client.client_pingserver_timeout"))

        # Client : send
        if Meters.aig("ping.client.client_send_error") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : client_send_error=%s", Meters.aig("ping.client.client_send_error"))

        # Client : protocol
        if Meters.aig("ping.client.invalid_protocol") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : invalid_protocol=%s", Meters.aig("ping.client.invalid_protocol"))

        # Client : Schedule
        if Meters.aig("ping.client.schedule_client_hello_server_timeout_error") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : schedule_client_hello_server_timeout_error=%s", Meters.aig("ping.client.schedule_client_hello_server_timeout_error"))

        if Meters.aig("ping.client.schedule_client_ping_error") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : schedule_client_ping_error=%s", Meters.aig("ping.client.schedule_client_ping_error"))

        if Meters.aig("ping.client.schedule_client_pingtimeouterror") > 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : schedule_client_pingtimeouterror=%s", Meters.aig("ping.client.schedule_client_pingtimeouterror"))

        # Client : server
        if Meters.aig("ping.client.server_ping_receive") == 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : server_ping_receive=%s", Meters.aig("ping.client.server_ping_receive"))

        if Meters.aig("ping.client.server_ping_reply") == 0:
            client_ko += 1
            if log_ko:
                logger.warn("failed : server_ping_reply=%s", Meters.aig("ping.client.server_ping_reply"))

        # Exit
        return client_ko

    @classmethod
    def get_server_ko_count(cls, log_ko=False, target_client=1):
        """
        Test
        :param log_ko: If true, log ko enabled.
        :param target_client: Target client count.
        :return An integer.
        """
        server_ko = 0

        # Stats : Schedule errors
        if Meters.aig("ping.server.scheduleClientHelloTimeOutError") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : scheduleClientHelloTimeOutError=%s", Meters.aig("ping.server.scheduleClientHelloTimeOutError"))

        if Meters.aig("ping.server.scheduleServerPingError") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : scheduleServerPingError=%s", Meters.aig("ping.server.scheduleServerPingError"))

        if Meters.aig("ping.server.scheduleServerPingTimeOutError") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : scheduleServerPingTimeOutError=%s", Meters.aig("ping.server.scheduleServerPingTimeOutError"))

        # Stats : connect/disconnect requests count
        if Meters.aig("ping.server.serverStartCount") != target_client:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : serverStartCount=%s", Meters.aig("ping.server.serverStartCount"))

        if Meters.aig("ping.server.serverStopSynchCount") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : serverStopSynchCount=%s", Meters.aig("ping.server.serverStopSynchCount"))

        # Stats : start/send errors count
        if Meters.aig("ping.server.serverStartError") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : serverStartError=%s", Meters.aig("ping.server.serverStartError"))

        if Meters.aig("ping.server.serverSendError") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : serverSendError=%s", Meters.aig("ping.server.serverSendError"))

        # Stats : hello(s)
        if Meters.aig("ping.server.clientHelloReceived") == 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : clientHelloReceived=%s", Meters.aig("ping.server.clientHelloReceived"))

        if Meters.aig("ping.server.client_hello_server_reply") == 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : client_hello_server_reply=%s", Meters.aig("ping.server.client_hello_server_reply"))

        if Meters.aig("ping.server.clientHelloTimeOut") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : clientHelloTimeOut=%s", Meters.aig("ping.server.clientHelloTimeOut"))

        # Stats : server pings
        if Meters.aig("ping.server.serverPingSent") == 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : serverPingSent=%s", Meters.aig("ping.server.serverPingSent"))

        if Meters.aig("ping.server.serverPingClientReply") == 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : serverPingClientReply=%s", Meters.aig("ping.server.serverPingClientReply"))

        if Meters.aig("ping.server.serverPingClientTimeOut") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : serverPingClientTimeOut=%s", Meters.aig("ping.server.serverPingClientTimeOut"))

        if Meters.aig("ping.server.serverPingServerClientReplyNoPingOngoing") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : serverPingServerClientReplyNoPingOngoing=%s", Meters.aig("ping.server.serverPingServerClientReplyNoPingOngoing"))

        # Stats : client pings
        if Meters.aig("ping.server.clientPingReceive") == 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : clientPingReceive=%s", Meters.aig("ping.server.clientPingReceive"))

        if Meters.aig("ping.server.client_ping_server_reply") == 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : client_ping_server_reply=%s", Meters.aig("ping.server.client_ping_server_reply"))

        # Stats : invalid protocols
        if Meters.aig("ping.server.invalid_protocol") > 0:
            server_ko += 1
            if log_ko:
                logger.warn("_getServerKoCount : failed : invalid_protocol=%s", Meters.aig("ping.server.invalid_protocol"))

        # Exit
        return server_ko
