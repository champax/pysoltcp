"""
    coding=utf-8
    Tests.
"""
import logging
import shutil

import gevent
from os.path import abspath
from os.path import dirname
from pysol_base.SolBase import SolBase

SolBase.logging_init()
logger = logging.getLogger("Utility")


# ============================================
# Unit src class
# ============================================


class Utility(object):
    """
    Test description
    """

    @classmethod
    def test_wait(cls):
        """
        Wait during test.
        :return: Nothing
        """
        SolBase.sleep(0)

    @classmethod
    def gevent_reset(cls):
        """
        Reinit
        :return: Nothing
        """
        logger.info("gevent_reset : reinit now")
        # GEVENT_RC1 fix : shutdown : no more
        # gevent.shutdown()
        gevent.reinit()

    @classmethod
    def generate_server_keys(cls):
        """
        Generate server keys
        :return: Path to server keys.
        """

        try:
            # Get current dir
            current_dir = dirname(abspath(__file__)) + SolBase.get_pathseparator()

            # Certificates path
            cert_path = current_dir + "Certificates" + SolBase.get_pathseparator()

            # Copy to /tmp (required for some files)
            shutil.copyfile(cert_path + "server.key", "/tmp/server.key")
            shutil.copyfile(cert_path + "server.crt", "/tmp/server.crt")

            # Ok
            return cert_path
        except Exception as e:
            logger.error("generate_server_keys : Exception, ex=%s", SolBase.extostr(e))
            return None
