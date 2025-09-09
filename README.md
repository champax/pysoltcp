pysoltcp
============

Welcome to pysol

Copyright (C) 2013/2025 Laurent Labatut / Laurent Champagnac

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
- Instrumented via Meters (pysolmeters)

Please note that, by design, synchronous TCP sockets are not supported.

Due to full asynchronous mode, pay attention that you may receive protocol input (via the receive callback) byte per byte (in a worst case scenario).
Your protocol parser must be ready to handle this in a correct manner.

