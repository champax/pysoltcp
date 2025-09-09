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

import logging
import signal
import traceback
from _ssl import PROTOCOL_TLSv1
from threading import RLock, Lock

import gevent
import os
from gevent.event import Event
from gevent.server import StreamServer
from gevent.timeout import Timeout
from pysolbase.SolBase import SolBase
from pysolmeters.AtomicInt import AtomicIntSafe
from pysolmeters.Meters import Meters

from pysoltcp.tcpserver.TcpServerConfig import TcpServerConfig

SolBase.voodoo_init()
logger = logging.getLogger(__name__)


# noinspection PyAbstractClass
class StreamServerNoClose(StreamServer):
    """
    Hack
    """

    def do_close(self, *args):
        """
        Do nothing
        """

        pass


class TcpServer(object):
    """
    Fast tcp server, gevent (epoll) based.
    Option via TcpServerConfig to enable SSL.
    If enabled, SSL handshake mode is done AFTER accept (do_handshake_on_connect=False)
    """

    def __init__(self, tcp_server_config):
        """
        Constructor.
        :param tcp_server_config: The configuration.
        :type tcp_server_config: pysoltcp.tcpserver.TcpServerConfig.TcpServerConfig
        """

        # Check
        if tcp_server_config is None:
            logger.error("tcp_server_config is None")
            raise Exception("tcp_server_config is None")
        elif not isinstance(tcp_server_config, TcpServerConfig):
            logger.error("tcp_server_config is not a TcpServerConfig, class=%s", SolBase.get_classname(tcp_server_config))
            raise Exception("tcp_server_config is not a TcpServerConfig")

        # Store
        self._tcp_server_config = tcp_server_config

        # Init =>

        # _is_started :
        # - True if server is started, False is server is stopped.
        # - Start : try to start, if ok set to True
        # - Stop : stop server, stop client, and set to False
        # - Means : During stop ongoing, will be True
        self._is_started = False

        # _is_running :
        # - True if server is running, False is server is no more running
        # - Start : Set to true, try to start, if failed, set to False
        # - Stop : Set to False, stop server, stop client
        # - Means : During stop ongoing, will be False
        self._is_running = False

        # Gevent StreamServer
        self._server = None

        # Fork pids
        self._fork_pid_list = list()

        # Client management (re-entrant lock)
        self._client_connected_atomicint = AtomicIntSafe()
        self._client_connected_hash = dict()
        self._client_connected_hash_lock = RLock()

        # Lock for start/stop
        self.__stop_start_lock = Lock()

        # Control variables
        self._effective_control_interval_ms = 0

        # Control init
        self.__set_effective_controlinterval_ms()

        # Auto start
        if self._tcp_server_config.auto_start is True:
            logger.info("Auto-starting ON, starting now")
            self.start_server()
        else:
            logger.info("Auto-starting OFF")

    # =====================================================
    # START / STOP : HIGH LEVEL
    # =====================================================

    def start_server(self):
        """
        Start

        """

        with self.__stop_start_lock:
            logger.info("start_server : starting")
            try:
                if self._is_started is True:
                    logger.warning("start_server : already started, doing nothing")
                    return False

                # Running
                self._is_running = True

                # Low level start
                self._start_server()

                # Start
                self._is_started = True

                # Done
                logger.info("start_server : started, %s", SolBase.get_current_pid_as_string())

                # Exit
                return True
            except Exception as e:
                logger.error("start_server : exception, ex=%s", SolBase.extostr(e))
                # Failed, not more running
                self._is_running = False

                # Raise
                raise

    def destroy(self):
        """
        For spring python. Just call stop_server().
        """
        logger.info("destroy : Entering, calling self.stop_server(), %s", SolBase.get_current_pid_as_string())
        self.stop_server()

    def stop_server(self):
        """
        Stop server
        """

        with self.__stop_start_lock:
            logger.info("stop_server : stopping, %s", SolBase.get_current_pid_as_string())
            try:
                # No more running
                self._is_running = False

                # Check
                if self._is_started is False:
                    logger.info("stop_server : already stopped, doing nothing, %s", SolBase.get_current_pid_as_string())
                    return

                # Low level stop
                try:
                    gevent.with_timeout(self._tcp_server_config.stop_server_timeout_ms, self._stop_server)
                except Timeout:
                    logger.warning("Timeout while calling low level _stop_server, some socket may be stucked")

                # Stop
                self._is_started = False

                # Done
                logger.info("stop_server : stopped, %s", SolBase.get_current_pid_as_string())
            except Exception as e:
                logger.error("stop_server : exception, ex=%s, %s", SolBase.extostr(e), SolBase.get_current_pid_as_string())
                raise

    # =====================================================
    # CONFIG ACCESS
    # =====================================================

    def get_tcpserver_config(self):
        """
        Return the configuration associated to the tcpserver.
        :return: A TcpServerConfig instance.
        :rtype pysoltcp.tcpserver.TcpServerConfig.TcpServerConfig
        """

        return self._tcp_server_config

    # =====================================================
    # START / STOP : LOW LEVEL
    # =====================================================

    def _start_server(self):
        """
        Low level start
        """

        # Allocate a server, and provide a connection callback
        logger.info("listen_addr=%s", self._tcp_server_config.listen_addr)
        logger.info("listen_port=%s", self._tcp_server_config.listen_port)
        logger.info("ssl_enable=%s", self._tcp_server_config.ssl_enable)
        logger.info("ssl_key_file=%s", self._tcp_server_config.ssl_key_file)
        logger.info("ssl_certificate_file=%s", self._tcp_server_config.ssl_certificate_file)

        logger.info("child_process_count=%s", self._tcp_server_config.child_process_count)

        logger.info("ssl_handshake_timeout_ms=%s", self._tcp_server_config.ssl_handshake_timeout_ms)

        logger.info("onstop_call_client_stopsynch=%s", self._tcp_server_config.onstop_call_client_stopsynch)

        logger.info("socket_absolute_timeout_ms=%s", self._tcp_server_config.socket_absolute_timeout_ms)
        logger.info("socket_relative_timeout_ms=%s", self._tcp_server_config.socket_relative_timeout_ms)
        logger.info("socket_min_checkinterval_ms=%s", self._tcp_server_config.socket_min_checkinterval_ms)

        logger.info("_effective_control_interval_ms=%s", self._effective_control_interval_ms)

        logger.info("stop_client_timeout_ms=%s", self._tcp_server_config.stop_client_timeout_ms)
        logger.info("stop_server_timeout_ms=%s", self._tcp_server_config.stop_server_timeout_ms)

        logger.info("client_factory=%s", self._tcp_server_config.client_factory)

        if self._tcp_server_config.ssl_enable is False:
            # No SSL
            logger.info("Starting in TCP/CLEAR mode")
            self._server = StreamServerNoClose(
                (self._tcp_server_config.listen_addr,
                 self._tcp_server_config.listen_port),
                self._on_connection)
        else:
            # SSL ON
            logger.info("Starting in TCP/SSL mode")
            self._server = StreamServerNoClose(
                (self._tcp_server_config.listen_addr,
                 self._tcp_server_config.listen_port),
                self._on_connection,
                # SSL enabling
                keyfile=self._tcp_server_config.ssl_key_file, certfile=self._tcp_server_config.ssl_certificate_file,
                # SSL handshake after accept
                do_handshake_on_connect=True,
                # TLS
                ssl_version=PROTOCOL_TLSv1,
                # Cipher
                # ciphers="RC4-MD5",
                # Args
            )

            self._server.min_delay = 0.0
            self._server.max_delay = 0.0

        # Startup
        if self._tcp_server_config.child_process_count <= 0:
            # Normal start-up
            logger.info("Starting in NON-FORKED mode")
            self._server.start()
        else:
            # Child process startup : prestart
            logger.info("Pre-starting in FORKED mode, subprocess=%s", self._tcp_server_config.child_process_count)
            # GEVENT_RC1 fix : pre_start => init_socket
            self._server.init_socket()

            # Let's rock
            logger.info("Forking gevent")
            for idx in range(self._tcp_server_config.child_process_count):
                # Fork gevent hub
                # GEVENT_RC1 fix : hub.fork => os.fork
                _fork_pid = gevent.fork()

                logger.info("Forking gevent hub done, idx=%s, forkPid=%s, %s", idx, _fork_pid, SolBase.get_current_pid_as_string())

                # Check it
                if _fork_pid == 0:
                    # We are in a child => exit this loop
                    SolBase.set_master_process(False)
                    break
                else:
                    # Master on
                    SolBase.set_master_process(True)

                    # Store child pid
                    logger.info("Storing child _fork_pid=%s", _fork_pid)
                    self._fork_pid_list.append(int(_fork_pid))

            # Start accepting now (parent and all sub-processes)
            logger.info("Accepting now, %s", SolBase.get_current_pid_as_string())
            self._server.start_accepting()

    def _stop_server(self):
        """
        Low level stop
        """

        try:
            # If we have child, signal them now
            for pid in self._fork_pid_list:
                logger.info("_stop_server : Sending SIGTERM to pid=%s", pid)
                # noinspection PyUnresolvedReferences
                os.kill(pid, signal.SIGTERM)

            # Wait for exit
            for pid in self._fork_pid_list:
                logger.info("_stop_server : Waiting for pid=%s", pid)

                # Wait
                wait_pid, wait_status = os.waitpid(pid, 0)

                # Get result
                wait_signal = wait_status & 0xff
                if wait_signal == 0:
                    wait_code = wait_status > 8
                else:
                    wait_code = 0

                # Info
                logger.info("_stop_server : Waiting for pid=%s ok, wait_status=%s, wait_signal=%s, wait_code=%s, wait_pid=%s", pid, wait_status, wait_signal, wait_code, wait_pid)

            # Stop (timeout = 5 seconds)
            self._server.stop(5)

            # Clear client
            self._remove_all_client()
        finally:
            # Reset
            self._server = None

    # =====================================================
    # INTERNAL CALLBACKS
    # =====================================================

    def _on_connection(self, socket, address):
        """
        Callback called upon client connection.
        :param socket:  The client socket.
        :type socket: socket.socket
        :param address: The client remote address:
        :type address: str

        """
        logger.debug("_on_connection : address=%s %s", address, SolBase.get_current_pid_as_string())

        # Register a new session
        # This will start the read/write loop on client.
        local_client = self._register_client(socket, address)

        # Check
        if local_client is None:
            logger.error("_on_connection : _register_client returned none")

    # =====================================================
    # CONTROL INTERVAL HELPER
    # =====================================================

    def __set_effective_controlinterval_ms(self):
        """
        Set the effective control interval in ms
        """

        # Get values
        val_abs = self._tcp_server_config.socket_absolute_timeout_ms
        val_rel = self._tcp_server_config.socket_relative_timeout_ms

        # If absolute and relative both lower then zero : nothing to do, socket has no limit
        if val_abs <= 0 and val_rel <= 0:
            self._effective_control_interval_ms = 0
        else:
            # Here, one of those is greater than zero.
            # If all of them are greater than zero : we keep the minimum
            if val_abs > 0 and val_rel > 0:
                val_sch = min(val_abs, val_rel)
            # Else, one of them if zero or lower : we keep the maximum
            else:
                val_sch = max(val_abs, val_rel)

            # We have val_sch, which is our target control check interval in ms.
            # To avoid too low values (and too high check frequency), we use correct it with minimal check interval
            self._effective_control_interval_ms = max(val_sch, self._tcp_server_config.socket_min_checkinterval_ms)

    def get_effective_controlinterval_ms(self):
        """
        Return the effective control interval in ms to apply to socket
        :return: An integer (millis)
        :rtype int
        """

        return self._effective_control_interval_ms

    # =====================================================
    # CLIENT MANAGEMENT : REGISTER
    # =====================================================

    def _register_client(self, socket, address):
        """
        Register a new client.
        :param socket:  The client socket.
        :type socket: socket.socket
        :param address: The client remote address
        :type address: str
        :return Return a TcpServerClientContext upon success, None upon failure.
        :rtype pysoltcp.tcpserver.clientcontext.TcpServerClientContext.TcpServerClientContext
        """

        try:
            logger.debug("entering")

            # Must be started
            if self._is_started is False:
                logger.debug("not started, cannot process")
                return None

            # Allocate a new client context
            logger.debug("allocating new_client using factory")
            new_client = self._tcp_server_config.client_factory.get_new_clientcontext(
                self,
                self._client_connected_atomicint.increment(),
                socket, address)

            # Hash id
            logger.debug("hashing new_client")
            with self._client_connected_hash_lock:
                logger.debug("hashing new_client (in lock)")
                self._client_connected_hash[new_client.get_client_id()] = new_client

            # Statistics
            logger.debug("populating statistics")
            Meters.aii("tcp.server.client_connected")
            Meters.aii("tcp.server.client_register_count")

            # Enable SSL if required and set handshake timeout
            if self._tcp_server_config.ssl_enable is True:
                new_client.set_ssl_handshake_asynch(True, self._tcp_server_config.ssl_handshake_timeout_ms, self._tcp_server_config.debug_waitinsslms)
            # Start the client
            logger.debug("starting client")
            new_client.start()

            # Log
            logger.debug("client started and hashed, id=%s, addr=%s", new_client.get_client_id(), new_client.get_client_addr())
            return new_client
        except Exception as e:
            # Error
            logger.warning("extostr, ex=%s", SolBase.extostr(e))

            # Statistics
            Meters.aii("tcp.server.clientRegisterException")

            # Close the socket in this case
            SolBase.safe_close_socket(socket)
            return None

    # =====================================================
    # CLIENT MANAGEMENT : REMOVE (ASYNCH and SYNCH) and REMOVE ALL
    # =====================================================

    def _remove_client_asynch(self, client_id):
        """
        Remove a client, asynch.
        :param client_id: The client id.
        :type client_id: int
        """

        # Spawn
        logger.debug("entering, client_id=%s", client_id)

        # Signal event (mantis 1280)
        evt = Event()

        # Spawn
        gevent.spawn(self._remove_client, client_id, evt)

        # Switch
        SolBase.sleep(0)

        # And wait
        # Note : remove this wait do not impact unittest...
        logger.debug("waiting, client_id=%s", client_id)
        evt.wait()

        # Over
        logger.debug("done, client_id=%s", client_id)

    # noinspection PyMethodMayBeStatic
    def _remove_client_stop_internal(self, old_client, evt):
        """
        Remove internal
        :param old_client: oldclient
        :type: old_client: pysoltcp.tcpserver.clientcontext.TcpServerClientContext.TcpServerClientContext
        :param evt: gevent.Event
        :type evt: gevent.Event
        """

        try:
            # Get
            cid = old_client.get_client_id()

            # Stop the client r/w loops and close the sock
            logger.debug("_remove_client_stop_internal call, cid=%s", cid)
            old_client.stop_synch_internal()
        except Exception as e:
            logger.warning("Ex=%s", SolBase.extostr(e))
        finally:
            evt.set()

    def _remove_client_stop_business(self, old_client, evt):
        """
        Remove internal
        :param old_client: oldclient
        :type old_client: pysoltcp.tcpserver.clientcontext.TcpServerClientContext.TcpServerClientContext
        :param evt: gevent.Event
        :type evt: gevent.Event
        """

        # -------------------------
        # Stop the client (Business call here)
        # We do NOT call if :
        # - service is stopping AND onstop_call_client_stopsynch==False
        # -------------------------

        try:
            cid = old_client.get_client_id()

            logger.debug("_remove_client_stop_business call, cid=%s", cid)

            if self._is_running:
                # -------------------
                # Running, call
                # -------------------
                logger.debug("stop_synch call (_is_running==%s), cid=%s", self._is_running, cid)
                old_client.stop_synch()
            elif not self._is_running and self._tcp_server_config.onstop_call_client_stopsynch:
                # -------------------
                # Not running + call ON : call
                # -------------------
                logger.debug("stop_synch call (_is_running==%s + onstop_call_client_stopsynch==%s), cid=%s", self._is_running, self._tcp_server_config.onstop_call_client_stopsynch, cid)
                old_client.stop_synch()
            else:
                # -------------------
                # No call
                # -------------------
                logger.debug("stop_synch NOT CALLED (_is_running==%s + onstop_call_client_stopsynch==%s), cid=%s", self._is_running, self._tcp_server_config.onstop_call_client_stopsynch, cid)
                pass
        except Exception as e:
            logger.warning("Ex=%s", SolBase.extostr(e))
        finally:
            evt.set()

    def _remove_client(self, client_id, evt):
        """
        Remove a client. Return a TcpServerClientContext upon success,
        :param client_id: The client id.
        :type client_id: int
        :param evt: Event to signal
        :type evt: gevent.Event, None
        :return The removed TcpServerClientContext or None upon failure.
        :rtype None,pysoltcp.tcpserver.clientcontext.TcpServerClientContext.TcpServerClientContext
        """

        logger.debug("entering, client_id=%s", client_id)

        try:
            with self._client_connected_hash_lock:
                # Check
                if client_id not in self._client_connected_hash:
                    # Note : This may occurs in some conditions
                    logger.debug("client_id not hashed, id=%s", client_id)
                    Meters.aii("tcp.server.client_remove_nothashed")
                    return None

                # Get (direct, we are already in lock)
                old_client = self._get_client_fromid(client_id)

                # Remove from hashmap
                logger.debug("un-hashing, client_id=%s", client_id)
                del (self._client_connected_hash[client_id])

            # ------------------------------
            # Out of lock : call async : BUSINESS
            # ------------------------------
            try:
                local_evt = Event()
                g1 = gevent.spawn(self._remove_client_stop_business, old_client, local_evt)
                SolBase.sleep(0)

                local_evt.wait(self._tcp_server_config.stop_client_timeout_ms / 1000.0)

                if not local_evt.isSet():
                    # Flush out warning
                    s = "Greenlet dump, g={0}, frame={1}".format(g1, ''.join(traceback.format_stack(g1.gr_frame)))

                    # Cleanup
                    s = s.replace("\n", " # ")
                    while s.find("  ") >= 0:
                        s = s.replace("  ", " ")

                    # Error logs
                    logger.error("Timeout in _remove_client_stop_business client_id=%s, stack=%s", client_id, s)

                    # Kill
                    g1.kill(block=True)

                    # Stat
                    Meters.aii("tcp.server.client_remove_timeout_business")

            except Exception as e:
                logger.warning("Exception in _remove_client_stop_business client_id=%s, ex=%s", client_id, SolBase.extostr(e))

            # ------------------------------
            # Out of lock : call async : INTERNAL
            # ------------------------------
            try:
                local_evt = Event()
                g2 = gevent.spawn(self._remove_client_stop_internal, old_client, local_evt)
                SolBase.sleep(0)

                local_evt.wait(self._tcp_server_config.stop_client_timeout_ms / 1000.0)

                if not local_evt.isSet():
                    # Flush out warning
                    s = "Greenlet dump, g={0}, frame={1}".format(g2, ''.join(traceback.format_stack(g2.gr_frame)))

                    # Cleanup
                    s = s.replace("\n", " # ")
                    while s.find("  ") >= 0:
                        s = s.replace("  ", " ")

                    # Error logs
                    logger.error("Timeout in _remove_client_stop_internal client_id=%s, stack=%s", client_id, s)

                    # Kill
                    g2.kill(block=True)

                    # Stat
                    Meters.aii("tcp.server.client_remove_timeout_internal")
            except Exception as e:
                logger.warning("Exception in _remove_client_stop_internal client_id=%s, ex=%s", client_id, SolBase.extostr(e))

            # Statistics
            Meters.aii("tcp.server.client_connected", -1)
            Meters.aii("tcp.server.client_remove_count")

            # Log
            logger.debug("client removed, id=%s, addr=%s", old_client.get_client_id(), old_client.get_client_addr())

            return old_client
        except Exception as e:
            # Error
            logger.warning("Exception, ex=%s", SolBase.extostr(e))

            # Statistics
            Meters.aii("tcp.server.client_remove_exception")

            return None
        finally:
            if evt:
                evt.set()

    def _remove_all_client(self):
        """
        Remove all clients.
        """
        try:
            # PY3 : Cannot iterate through keys (it do not copy anymore)
            # => we force a list alloc

            # Pass through all client and remove all
            for client_id in list(self._client_connected_hash.keys()):
                self._remove_client(client_id, None)
        except Exception as e:
            # Error
            logger.warning("_remove_all_client : Exception, ex=%s", SolBase.extostr(e))

    # =====================================================
    # CLIENT MANAGEMENT : GET FROM HASHMAP
    # =====================================================

    def _get_client_fromid(self, client_id):
        """
        Get a client from id. Return None if not found.
        :param client_id: The client Id
        :type client_id: int
        :return A TcpServerClientContext or None if not found.
        :rtype None,pysoltcp.tcpserver.clientcontext.TcpServerClientContext.TcpServerClientContext
        """
        with self._client_connected_hash_lock:
            # Check
            if client_id not in self._client_connected_hash:
                return None
            else:
                return self._client_connected_hash[client_id]
