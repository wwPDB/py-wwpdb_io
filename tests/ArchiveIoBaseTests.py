##
# File:    ArchiveIoBaseTests.py
# Author:  Ezra Peisach
# Date:    31-Aug-2026
#
# Updates:
#
##
"""Test cases for ArchiveIoBase"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

import logging
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from wwpdb.io.sftp.ArchiveIoBase import ArchiveIoBase

logger = logging.getLogger(__name__)


class ArchiveIoBaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__patcher = patch("wwpdb.io.sftp.ArchiveIoBase.ConfigInfo")
        self.__mockConfigInfoClass: MagicMock = self.__patcher.start()
        self.__mockConfigInfoClass.return_value.get.return_value = {}

    def tearDown(self) -> None:
        self.__patcher.stop()

    def testInitDefaults(self) -> None:
        """With no configuration available all connection attributes default to None."""
        aio = ArchiveIoBase()
        self.assertFalse(aio._raiseExceptions)  # noqa: SLF001
        self.assertIsNone(aio._serverId)  # noqa: SLF001
        self.assertIsNone(aio._hostName)  # noqa: SLF001
        self.assertIsNone(aio._userName)  # noqa: SLF001
        self.assertIsNone(aio._password)  # noqa: SLF001
        self.assertEqual(aio._hostPort, 22)  # noqa: SLF001
        self.assertIsNone(aio._protocol)  # noqa: SLF001
        self.assertIsNone(aio._rootPath)  # noqa: SLF001
        self.assertIsNone(aio._keyFilePath)  # noqa: SLF001
        self.assertIsNone(aio._keyFileType)  # noqa: SLF001

    def testInitWithConfig(self) -> None:
        """Configuration values returned by ConfigInfo are surfaced on the instance."""
        config: dict[str, Any] = {
            "HOST_NAME": "host.example.com",
            "HOST_USERNAME": "user",
            "HOST_PASSWORD": "secret",
            "HOST_PORT": "2222",
            "HOST_PROTOCOL": "sftp",
            "HOST_ROOT_PATH": "/data",
            "HOST_KEY_FILE_PATH": "/keys/id_rsa",
            "HOST_KEY_FILE_TYPE": "RSA",
        }
        self.__mockConfigInfoClass.return_value.get.return_value = config

        aio = ArchiveIoBase(serverId="SOME_SERVER", raiseExceptions=True, siteId="TEST_SITE")
        self.assertTrue(aio._raiseExceptions)  # noqa: SLF001
        self.assertEqual(aio._siteId, "TEST_SITE")  # noqa: SLF001
        self.assertEqual(aio._serverId, "SOME_SERVER")  # noqa: SLF001
        self.assertEqual(aio._hostName, "host.example.com")  # noqa: SLF001
        self.assertEqual(aio._userName, "user")  # noqa: SLF001
        self.assertEqual(aio._password, "secret")  # noqa: SLF001
        self.assertEqual(aio._hostPort, 2222)  # noqa: SLF001
        self.assertEqual(aio._protocol, "sftp")  # noqa: SLF001
        self.assertEqual(aio._rootPath, "/data")  # noqa: SLF001
        self.assertEqual(aio._keyFilePath, "/keys/id_rsa")  # noqa: SLF001
        self.assertEqual(aio._keyFileType, "RSA")  # noqa: SLF001

    def testInitDefaultHostPort(self) -> None:
        """HOST_PORT defaults to 22 when not present in the configuration."""
        self.__mockConfigInfoClass.return_value.get.return_value = {"HOST_NAME": "host.example.com"}
        aio = ArchiveIoBase(serverId="SOME_SERVER")
        self.assertEqual(aio._hostPort, 22)  # noqa: SLF001

    def testUnimplementedMethods(self) -> None:
        """All transfer operations are unimplemented in the base class."""
        aio = ArchiveIoBase()
        with self.assertRaises(NotImplementedError):
            aio.connect("host", "user")
        with self.assertRaises(NotImplementedError):
            aio.mkdir("/path", 0o777)
        with self.assertRaises(NotImplementedError):
            aio.stat("/path")
        with self.assertRaises(NotImplementedError):
            aio.put("/local", "/remote")
        with self.assertRaises(NotImplementedError):
            aio.get("/remote", "/local")
        with self.assertRaises(NotImplementedError):
            aio.listdir("/path")
        with self.assertRaises(NotImplementedError):
            aio.rmdir("/path")
        with self.assertRaises(NotImplementedError):
            aio.remove("/path")
        with self.assertRaises(NotImplementedError):
            aio.close()


if __name__ == "__main__":
    unittest.main()
