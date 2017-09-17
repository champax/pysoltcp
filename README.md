pysoltcp
============

Welcome to pysol

Copyright (C) 2013/2017 Laurent Labatut / Laurent Champagnac

pysoltcp is a set of python asynchronous TCP server and client.

It is gevent (co-routines) based.

Both are able to sustain 60 000 asynchronous bi-directional sockets within a single python process.

The TCP server is able to work in forking mode to scale across several CPUs.

It supports:
- Asynchronous TCP sockets (with underlying async read/write loops, send queues and receive callback, per socket)
- SSL sockets
- SOCKS5 proxy (tested via dante)
- TCP Keepalive
- Absolute and relative socket idle timeouts for reads and writes, per socket, via gevent co-routine schedules (no global control thread)
- SSL handshake timeout
- Server forking
- Server context factory for server side protocol handling
- Client derivation with _on_receive override for client side protocol handling
- Intrumented via Meters (pysolmeters)

Please note that, by design, synchronous TCP sockets are not supported.

Due to full asynchronous mode, pay attention that you may receive protocol input (via the receive callback) byte per byte (in a worst case scenario).
Your protocol parser must be ready to handle this in a correct manner.

Usage
===============

A simple client/server ping-pong text protocol (\n delimited) is implemented for unittests.

For client side, refer to:
- pysoltcp_test.TcpApi.PingProtocol.Client.PingSimpleClient.PingSimpleClient

For server side, refer to:
- pysoltcp_test.TcpApi.PingProtocol.Server.PingServerContextFactory.PingServerContextFactory
- pysoltcp_test.TcpApi.PingProtocol.Server.PingServerContext.PingServerContext

Implementations are pretty verbose due to infrastructure in place for unit testing.

Source code
===============

- We are pep8 compliant (as far as we can, with some exemptions)
- We use a right margin of 360 characters (please don't talk me about 80 chars)
- All unittest files must begin with `test_` or `Test`, should implement setUp and tearDown methods
- All tests must adapt to any running directory
- The whole project is backed by gevent (http://www.gevent.org/)
- We use docstring (:return, :rtype, :param, :type etc..), they are mandatory
- We use PyCharm "noinspection", feel free to use them

Requirements
===============

- Debian 8 Jessie or greater, x64, Python 2.7



Unittests
===============

To run unittests, you will need:

- SOCKS5 proxy installed and ready (you may use Dante), using port 127.0.0.1:1080, no credentials.
- TCP Listen port 3201 available
- Advanced unittests (disabled by default) requires tuned OS and TCP stack 

License
===============

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA


