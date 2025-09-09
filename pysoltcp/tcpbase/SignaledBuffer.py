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

from gevent.event import Event


class SignaledBuffer(object):
    """
    Send class for tcp, with signal upon send completion.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.__buffer = None
        self.__send_event = Event()

    def __set_buffer(self, local_buffer):
        """
        Set the binary local_buffer.
        :param local_buffer: The binary local_buffer.
        :type local_buffer: bytes
        """
        self.__buffer = local_buffer

    def __get_buffer(self):
        """
        Getter
        :return: The binary localBuffer
        :rtype: bytes
        """
        return self.__buffer

    def __get_event(self):
        """
        Get the event.
        :return: Event
        :rtype: gevent.event.Event
        """
        return self.__send_event

    binary_buffer = property(__get_buffer, __set_buffer)
    send_event = property(__get_event)
