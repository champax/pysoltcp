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

        """
        SolBase.voodoo_init()

    def tearDown(self):
        """
        Setup (called on destroy)

        """
        pass

    def test_parser(self):
        """
        Test

        """

        # Separator
        sep = b"\n"

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, None, q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"", q, sep)
        self.assertTrue(incomplete_buf == b"a.")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"b", q, sep)
        self.assertTrue(incomplete_buf == b"b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"b", q, sep)
        self.assertTrue(incomplete_buf == b"b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"b", q, sep)
        self.assertTrue(incomplete_buf == b"a.b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto", q, sep)
        self.assertTrue(incomplete_buf == b"toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto", q, sep)
        self.assertTrue(incomplete_buf == b"toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto", q, sep)
        self.assertTrue(incomplete_buf == b"a.toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"a.toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"a.toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto\ntutu\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto\ntutu\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto\ntutu\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"a.toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto\ntutu\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto\ntutu\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto\ntutu\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"a.toto")
        self.assertTrue(q.get_nowait() == b"tutu")

    def test_parser2(self):
        """
        Test

        """

        # Separator
        sep = b"\r\n"

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, None, q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"", q, sep)
        self.assertTrue(incomplete_buf == b"a.")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"b", q, sep)
        self.assertTrue(incomplete_buf == b"b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"b", q, sep)
        self.assertTrue(incomplete_buf == b"b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"b", q, sep)
        self.assertTrue(incomplete_buf == b"a.b")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto", q, sep)
        self.assertTrue(incomplete_buf == b"toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto", q, sep)
        self.assertTrue(incomplete_buf == b"toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto", q, sep)
        self.assertTrue(incomplete_buf == b"a.toto")
        self.assertTrue(q.qsize() == 0)

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"a.toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 1)
        self.assertTrue(q.get_nowait() == b"a.toto")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto\r\ntutu\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto\r\ntutu\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto\r\ntutu\r\n", q, sep)
        self.assertTrue(incomplete_buf is None)
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"a.toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(None, b"toto\r\ntutu\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"", b"toto\r\ntutu\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"toto")
        self.assertTrue(q.get_nowait() == b"tutu")

        # Test
        q = Queue()
        incomplete_buf = ProtocolParserTextDelimited.parse_protocol(b"a.", b"toto\r\ntutu\r\n.b", q, sep)
        self.assertTrue(incomplete_buf == b".b")
        self.assertTrue(q.qsize() == 2)
        self.assertTrue(q.get_nowait() == b"a.toto")
        self.assertTrue(q.get_nowait() == b"tutu")
