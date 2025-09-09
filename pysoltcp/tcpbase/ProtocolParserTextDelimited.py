"""
# -*- coding: utf-8 -*-
# ===============================================================================
#
# Copyright (C) 2013/2025 Laurent Labatut / Laurent Champagnac
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

from pysolbase.SolBase import SolBase

SolBase.logging_init()
logger = logging.getLogger(__name__)


class ProtocolParserTextDelimited(object):
    """
    A protocol parser, able to react to chunk of protocols received onto a socket.
    """

    @classmethod
    def parse_protocol(cls, previous_buffer, input_buffer, gevent_queue, separator=b"\n", single_item_processing=False):
        """
        Parse a received protocol.
        - For all COMPLETE token : enqueue in the provided queue (method : put)
        - Return the remaining INCOMPLETE token (ie not \n terminated)
        - Return None if no INCOMPLETE token remains
        :param cls: Our class.
        :param previous_buffer: The previous incomplete buffer.
        :type previous_buffer: bytes,None
        :param input_buffer: The new buffer.
        :type input_buffer: bytes,None
        :param gevent_queue: A gevent queue, which will be populated with complete items.
        :type gevent_queue: Queue
        :param separator: The separator to use
        :type separator: bytes
        :param single_item_processing: If true, process only one item then exit.
        :type single_item_processing: bool
        :return: The new incomplete buffer.
        :rtype bytes
        """

        # - ar[0] : a string
        # - ar[1] : IF separator found : separator
        # - ar[1] : IF separator not found : empty
        # - ar[2] : remaining part or empty

        # Split
        prev_buf = previous_buffer
        if input_buffer:
            cur_buf = input_buffer
        else:
            cur_buf = b""

        # Prefix by prev_buf
        if prev_buf:
            cur_buf = prev_buf + cur_buf
            prev_buf = None

        while True:
            # Need separator as bytes
            # noinspection PyTypeChecker
            ar = cur_buf.partition(separator)

            # Check ar[1]
            if len(ar[1]) > 0:
                # Separator found, having a COMPLETE token in ar[0] : Enqueue it, with optional previous buffer prefix
                if prev_buf is None:
                    gevent_queue.put(ar[0])
                else:
                    gevent_queue.put(previous_buffer + ar[0])
                    # noinspection PyUnusedLocal
                    prev_buf = None

                # Check if we have remaining stuff
                if len(ar[2]) == 0:
                    # Nothing more
                    return prev_buf
                else:
                    # Remaining stuff : continue to parse
                    if not single_item_processing:
                        # noinspection PyUnusedLocal
                        cur_buf = ar[2]
                    else:
                        return ar[2]
            else:
                # Separator not found
                # We have an INCOMPLETE token
                # Stop parse and return it
                # BUT only IF not empty
                if len(ar[0]) == 0:
                    if prev_buf is None:
                        return None
                    elif len(prev_buf) > 0:
                        return prev_buf
                    else:
                        return None

                else:
                    if prev_buf is None:
                        return ar[0]
                    else:
                        return prev_buf + ar[0]
