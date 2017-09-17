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

from gevent.queue import Queue
from pysolbase.SolBase import SolBase

from pysoltcp.tcpbase.ProtocolParserTextDelimited import ProtocolParserTextDelimited

SolBase.logging_init()
logger = logging.getLogger(__name__)


# ============================================
# Unit src class
# ============================================


class TestProtocolParserTextDelimited(unittest.TestCase):
    """
    Test description
    """

    def setUp(self):
        """
        Setup
        :return Nothing.
        """
        SolBase.voodoo_init()

    def tearDown(self):
        """
        Setup (called on destroy)
        :return Nothing.
        """
        pass

    def test_parser(self):
        """
        Test
        :return Nothing.
        """

        # Separator
        sep = "\n"

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, None, q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "", q, sep)
        self.assertTrue(incomplete_buf == "a.")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "b", q, sep)
        self.assertTrue(incomplete_buf == "b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "b", q, sep)
        self.assertTrue(incomplete_buf == "b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "b", q, sep)
        self.assertTrue(incomplete_buf == "a.b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto", q, sep)
        self.assertTrue(incomplete_buf == "toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto", q, sep)
        self.assertTrue(incomplete_buf == "toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto", q, sep)
        self.assertTrue(incomplete_buf == "a.toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "a.toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "a.toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto\ntutu\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto\ntutu\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto\ntutu\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "a.toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto\ntutu\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto\ntutu\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto\ntutu\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "a.toto")
        self.assertTrue(q.get_nowait() == "tutu")

    def test_parser2(self):
        """
        Test
        :return Nothing.
        """

        # Separator
        sep = "\r\n"

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, None, q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "", q, sep)
        self.assertTrue(incomplete_buf == "a.")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "b", q, sep)
        self.assertTrue(incomplete_buf == "b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "b", q, sep)
        self.assertTrue(incomplete_buf == "b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "b", q, sep)
        self.assertTrue(incomplete_buf == "a.b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto", q, sep)
        self.assertTrue(incomplete_buf == "toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto", q, sep)
        self.assertTrue(incomplete_buf == "toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto", q, sep)
        self.assertTrue(incomplete_buf == "a.toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "a.toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == "a.toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto\r\ntutu\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto\r\ntutu\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto\r\ntutu\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "a.toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, "toto\r\ntutu\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("", "toto\r\ntutu\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "toto")
        self.assertTrue(q.get_nowait() == "tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol("a.", "toto\r\ntutu\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == ".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == "a.toto")
        self.assertTrue(q.get_nowait() == "tutu")
