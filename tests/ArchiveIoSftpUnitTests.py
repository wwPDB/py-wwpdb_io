##
# File:    ArchiveIoSftpUnitTests.py
# Author:  Ezra Peisach
# Date:    31-Aug-2026
#
# Updates:
#
##
"""Unit test cases for ArchiveIoSftp using mocked paramiko transport/client objects.

Unlike ArchiveIoSftpTests.py these tests do not require a live SFTP server -
all paramiko interactions are mocked out.
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

import logging
import unittest
from unittest.mock import MagicMock, patch

from wwpdb.io.sftp.ArchiveIoSftp import ArchiveIoSftp

logger = logging.getLogger(__name__)


class ArchiveIoSftpUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__transportPatcher = patch("wwpdb.io.sftp.ArchiveIoSftp.paramiko.Transport")
        self.__mockTransportClass: MagicMock = self.__transportPatcher.start()
        self.__mockTransport: MagicMock = self.__mockTransportClass.return_value

        self.__fromTransportPatcher = patch("wwpdb.io.sftp.ArchiveIoSftp.paramiko.SFTPClient.from_transport")
        self.__mockFromTransport: MagicMock = self.__fromTransportPatcher.start()
        self.__mockSftpClient: MagicMock = MagicMock(name="sftpClient")
        self.__mockFromTransport.return_value = self.__mockSftpClient

        self.__rsaKeyPatcher = patch("wwpdb.io.sftp.ArchiveIoSftp.paramiko.RSAKey.from_private_key_file")
        self.__mockRsaKey: MagicMock = self.__rsaKeyPatcher.start()

    def tearDown(self) -> None:
        self.__transportPatcher.stop()
        self.__fromTransportPatcher.stop()
        self.__rsaKeyPatcher.stop()

    # ------------------------------------------------------------------
    # getRootPath
    # ------------------------------------------------------------------
    def testGetRootPathDefault(self) -> None:
        aio = ArchiveIoSftp()
        self.assertIsNone(aio.getRootPath())

    # ------------------------------------------------------------------
    # connect()
    # ------------------------------------------------------------------
    def testConnectWithPassword(self) -> None:
        aio = ArchiveIoSftp()
        ok = aio.connect("host.example.com", "user", port=2222, pw="secret")
        self.assertTrue(ok)
        self.__mockTransportClass.assert_called_once_with(("host.example.com", 2222))
        self.__mockTransport.connect.assert_called_once_with(username="user", password="secret")
        self.__mockRsaKey.assert_not_called()

    def testConnectWithKeyFileRsa(self) -> None:
        aio = ArchiveIoSftp()
        mockKey = MagicMock(name="rsaKey")
        self.__mockRsaKey.return_value = mockKey
        ok = aio.connect("host.example.com", "user", keyFilePath="/keys/id_rsa")
        self.assertTrue(ok)
        self.__mockRsaKey.assert_called_once_with("/keys/id_rsa")
        self.__mockTransport.connect.assert_called_once_with(username="user", pkey=mockKey)

    def testConnectWithKeyFileDsaUnsupported(self) -> None:
        """DSA keys are no longer supported; failure is swallowed unless raiseExceptions is set."""
        aio = ArchiveIoSftp()
        ok = aio.connect("host.example.com", "user", keyFilePath="/keys/id_dsa", keyFileType="DSA")
        self.assertTrue(ok)
        self.__mockRsaKey.assert_not_called()
        self.__mockTransportClass.assert_not_called()
        # sftp client was never created, so a subsequent operation fails
        with self.assertRaises(RuntimeError):
            aio.listdir(".")

    def testConnectWithKeyFileDsaUnsupportedRaises(self) -> None:
        aio = ArchiveIoSftp(raiseExceptions=True)
        with self.assertRaises(ValueError):
            aio.connect("host.example.com", "user", keyFilePath="/keys/id_dsa", keyFileType="DSA")

    def testConnectFailureNotRaised(self) -> None:
        self.__mockTransport.connect.side_effect = OSError("connection refused")
        aio = ArchiveIoSftp()
        ok = aio.connect("host.example.com", "user", pw="secret")
        self.assertTrue(ok)
        self.__mockTransport.close.assert_called_once()
        with self.assertRaises(RuntimeError):
            aio.listdir(".")

    def testConnectFailureRaised(self) -> None:
        self.__mockTransport.connect.side_effect = OSError("connection refused")
        aio = ArchiveIoSftp(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.connect("host.example.com", "user", pw="secret")
        self.__mockTransport.close.assert_called_once()

    # ------------------------------------------------------------------
    # connectToServer()
    # ------------------------------------------------------------------
    def testConnectToServerWithPassword(self) -> None:
        aio = ArchiveIoSftp()
        aio._hostName = "host.example.com"  # noqa: SLF001
        aio._userName = "user"  # noqa: SLF001
        aio._hostPort = 22  # noqa: SLF001
        aio._password = "secret"  # noqa: SLF001
        ok = aio.connectToServer()
        self.assertTrue(ok)
        self.__mockTransport.connect.assert_called_once_with(username="user", password="secret")

    def testConnectToServerWithKeyFile(self) -> None:
        aio = ArchiveIoSftp()
        aio._hostName = "host.example.com"  # noqa: SLF001
        aio._userName = "user"  # noqa: SLF001
        aio._hostPort = 22  # noqa: SLF001
        aio._password = None  # noqa: SLF001
        aio._keyFilePath = "/keys/id_rsa"  # noqa: SLF001
        aio._keyFileType = "RSA"  # noqa: SLF001
        ok = aio.connectToServer()
        self.assertTrue(ok)
        self.__mockRsaKey.assert_called_once_with("/keys/id_rsa")

    def testConnectToServerMissingConfig(self) -> None:
        """Neither password nor key file configured -> connect fails immediately."""
        aio = ArchiveIoSftp(serverId="SOME_SERVER")
        ok = aio.connectToServer()
        self.assertFalse(ok)
        self.__mockTransportClass.assert_not_called()

    def testConnectToServerFailureNotRaised(self) -> None:
        self.__mockTransport.connect.side_effect = OSError("connection refused")
        aio = ArchiveIoSftp()
        aio._hostName = "host.example.com"  # noqa: SLF001
        aio._userName = "user"  # noqa: SLF001
        aio._hostPort = 22  # noqa: SLF001
        aio._password = "secret"  # noqa: SLF001
        ok = aio.connectToServer()
        self.assertTrue(ok)
        with self.assertRaises(RuntimeError):
            aio.listdir(".")

    def testConnectToServerFailureRaised(self) -> None:
        self.__mockTransport.connect.side_effect = OSError("connection refused")
        aio = ArchiveIoSftp(raiseExceptions=True)
        aio._hostName = "host.example.com"  # noqa: SLF001
        aio._userName = "user"  # noqa: SLF001
        aio._hostPort = 22  # noqa: SLF001
        aio._password = "secret"  # noqa: SLF001
        with self.assertRaises(OSError):
            aio.connectToServer()

    # ------------------------------------------------------------------
    # helper
    # ------------------------------------------------------------------
    def __connectedClient(self, raiseExceptions: bool = False) -> ArchiveIoSftp:
        aio = ArchiveIoSftp(raiseExceptions=raiseExceptions)
        ok = aio.connect("host.example.com", "user", pw="secret")
        self.assertTrue(ok)
        return aio

    # ------------------------------------------------------------------
    # operations without an active connection
    # ------------------------------------------------------------------
    def testOperationsRequireConnection(self) -> None:
        aio = ArchiveIoSftp()
        with self.assertRaises(RuntimeError):
            aio.mkdir("/path")
        with self.assertRaises(RuntimeError):
            aio.stat("/path")
        with self.assertRaises(RuntimeError):
            aio.put("/local", "/remote")
        with self.assertRaises(RuntimeError):
            aio.get("/remote", "/local")
        with self.assertRaises(RuntimeError):
            aio.listdir("/path")
        with self.assertRaises(RuntimeError):
            aio.rmdir("/path")
        with self.assertRaises(RuntimeError):
            aio.remove("/path")

    # ------------------------------------------------------------------
    # mkdir
    # ------------------------------------------------------------------
    def testMkdirSuccess(self) -> None:
        aio = self.__connectedClient()
        ok = aio.mkdir("/path/test", 0o755)
        self.assertTrue(ok)
        self.__mockSftpClient.mkdir.assert_called_once_with("/path/test", 0o755)

    def testMkdirDefaultMode(self) -> None:
        aio = self.__connectedClient()
        aio.mkdir("/path/test")
        self.__mockSftpClient.mkdir.assert_called_once_with("/path/test", 511)

    def testMkdirFailureNotRaised(self) -> None:
        self.__mockSftpClient.mkdir.side_effect = OSError("permission denied")
        aio = self.__connectedClient()
        ok = aio.mkdir("/path/test")
        self.assertFalse(ok)

    def testMkdirFailureRaised(self) -> None:
        self.__mockSftpClient.mkdir.side_effect = OSError("permission denied")
        aio = self.__connectedClient(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.mkdir("/path/test")

    # ------------------------------------------------------------------
    # stat
    # ------------------------------------------------------------------
    def testStatSuccess(self) -> None:
        mockAttr = MagicMock()
        mockAttr.st_mtime = 1000
        mockAttr.st_size = 17
        mockAttr.st_mode = 0o40755
        mockAttr.st_uid = 0
        mockAttr.st_gid = 0
        mockAttr.st_atime = 1001
        self.__mockSftpClient.stat.return_value = mockAttr

        aio = self.__connectedClient()
        result = aio.stat("/path")
        self.assertEqual(
            result,
            {"mtime": 1000, "size": 17, "mode": 0o40755, "uid": 0, "gid": 0, "atime": 1001},
        )

    def testStatFailureNotRaised(self) -> None:
        self.__mockSftpClient.stat.side_effect = OSError("no such file")
        aio = self.__connectedClient()
        result = aio.stat("/path")
        self.assertEqual(result, {})

    def testStatFailureRaised(self) -> None:
        self.__mockSftpClient.stat.side_effect = OSError("no such file")
        aio = self.__connectedClient(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.stat("/path")

    # ------------------------------------------------------------------
    # put / get
    # ------------------------------------------------------------------
    def testPutSuccess(self) -> None:
        aio = self.__connectedClient()
        ok = aio.put("/local/file", "/remote/file")
        self.assertTrue(ok)
        self.__mockSftpClient.put.assert_called_once_with("/local/file", "/remote/file")

    def testPutFailureNotRaised(self) -> None:
        self.__mockSftpClient.put.side_effect = OSError("disk full")
        aio = self.__connectedClient()
        ok = aio.put("/local/file", "/remote/file")
        self.assertFalse(ok)

    def testPutFailureRaised(self) -> None:
        self.__mockSftpClient.put.side_effect = OSError("disk full")
        aio = self.__connectedClient(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.put("/local/file", "/remote/file")

    def testGetSuccess(self) -> None:
        aio = self.__connectedClient()
        ok = aio.get("/remote/file", "/local/file")
        self.assertTrue(ok)
        self.__mockSftpClient.get.assert_called_once_with("/remote/file", "/local/file")

    def testGetFailureNotRaised(self) -> None:
        self.__mockSftpClient.get.side_effect = OSError("no such file")
        aio = self.__connectedClient()
        ok = aio.get("/remote/file", "/local/file")
        self.assertFalse(ok)

    def testGetFailureRaised(self) -> None:
        self.__mockSftpClient.get.side_effect = OSError("no such file")
        aio = self.__connectedClient(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.get("/remote/file", "/local/file")

    # ------------------------------------------------------------------
    # listdir
    # ------------------------------------------------------------------
    def testListdirSuccess(self) -> None:
        self.__mockSftpClient.listdir.return_value = ["a", "b"]
        aio = self.__connectedClient()
        result = aio.listdir("/path")
        self.assertEqual(result, ["a", "b"])

    def testListdirFailureNotRaised(self) -> None:
        self.__mockSftpClient.listdir.side_effect = OSError("no such directory")
        aio = self.__connectedClient()
        result = aio.listdir("/path")
        self.assertFalse(result)

    def testListdirFailureRaised(self) -> None:
        self.__mockSftpClient.listdir.side_effect = OSError("no such directory")
        aio = self.__connectedClient(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.listdir("/path")

    # ------------------------------------------------------------------
    # rmdir
    # ------------------------------------------------------------------
    def testRmdirSuccess(self) -> None:
        aio = self.__connectedClient()
        ok = aio.rmdir("/path")
        self.assertTrue(ok)
        self.__mockSftpClient.rmdir.assert_called_once_with("/path")

    def testRmdirFailureNotRaised(self) -> None:
        self.__mockSftpClient.rmdir.side_effect = OSError("not empty")
        aio = self.__connectedClient()
        ok = aio.rmdir("/path")
        self.assertFalse(ok)

    def testRmdirFailureRaised(self) -> None:
        self.__mockSftpClient.rmdir.side_effect = OSError("not empty")
        aio = self.__connectedClient(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.rmdir("/path")

    # ------------------------------------------------------------------
    # remove
    # ------------------------------------------------------------------
    def testRemoveSuccess(self) -> None:
        aio = self.__connectedClient()
        ok = aio.remove("/path/file")
        self.assertTrue(ok)
        self.__mockSftpClient.remove.assert_called_once_with("/path/file")

    def testRemoveFailureNotRaised(self) -> None:
        self.__mockSftpClient.remove.side_effect = OSError("no such file")
        aio = self.__connectedClient()
        ok = aio.remove("/path/file")
        self.assertFalse(ok)

    def testRemoveFailureRaised(self) -> None:
        self.__mockSftpClient.remove.side_effect = OSError("no such file")
        aio = self.__connectedClient(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.remove("/path/file")

    # ------------------------------------------------------------------
    # close
    # ------------------------------------------------------------------
    def testCloseWithoutConnection(self) -> None:
        aio = ArchiveIoSftp()
        ok = aio.close()
        self.assertTrue(ok)

    def testCloseSuccess(self) -> None:
        aio = self.__connectedClient()
        ok = aio.close()
        self.assertTrue(ok)
        self.__mockSftpClient.close.assert_called_once()
        self.__mockTransport.close.assert_called_once()

    def testCloseFailureNotRaised(self) -> None:
        self.__mockSftpClient.close.side_effect = OSError("already closed")
        aio = self.__connectedClient()
        ok = aio.close()
        self.assertFalse(ok)

    def testCloseFailureRaised(self) -> None:
        self.__mockSftpClient.close.side_effect = OSError("already closed")
        aio = self.__connectedClient(raiseExceptions=True)
        with self.assertRaises(OSError):
            aio.close()


if __name__ == "__main__":
    unittest.main()
