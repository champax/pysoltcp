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

from pysoltcp.tcpbase.TcpSocketManager import TcpSocketManager

SolBase.logging_init()
logger = logging.getLogger(__name__)


class TcpSocketManagerTest1(TcpSocketManager):
    """
    Test
    """

    def __init__(self, callback_disconnect, callback_receive):
        """
        Constructor.
        :param callback_disconnect: Callback to call upon socket disconnection.
        :param callback_receive:  Callback to call upon socket receive.
        :return: Nothing.
        """

        TcpSocketManager.__init__(self, callback_disconnect, callback_receive)


class TcpSocketManagerTest2(TcpSocketManagerTest1):
    """
    Test
    """

    def __init__(self, callback_disconnect, callback_receive):
        """
        Constructor.
        :param callback_disconnect: Callback to call upon socket disconnection.
        :param callback_receive:  Callback to call upon socket receive.
        :return: Nothing.
        """

        TcpSocketManagerTest1.__init__(self, callback_disconnect, callback_receive)


class TestTcpSocketManager(unittest.TestCase):
    """
    Test description
    """

    def setUp(self):
        """
        Setup
        :return Nothing
        """

        pass

    def tearDown(self):
        """
        Setup (called on destroy)
        :return Nothing.
        """
        pass

    def dummy(self):
        """
        Dummy method
        """
        pass

    def test_tostr(self):
        """
        Test
        """

        t1 = TcpSocketManagerTest1(self.dummy, self.dummy)
        t2 = TcpSocketManagerTest2(self.dummy, self.dummy)

        str1 = str(t1)
        str2 = str(t2)

        logger.info("str1=%s", str1)
        logger.info("str2=%s", str2)

        self.assertTrue(str1.find("*cl=TcpSocketManagerTest1*") > 0)
        self.assertTrue(str2.find("*cl=TcpSocketManagerTest2*") > 0)
