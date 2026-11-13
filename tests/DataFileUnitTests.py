##
# File:    DataFileUnitTests.py
# Author:  Ezra Peisach
# Date:    20-Sep-2026
#
# Updates:
#
##
"""Unit test cases for DataFile.

Unlike tests-config/DataFileTests.py, these tests do not require the
wwpdb.utils.config site configuration fixtures - they are self-contained,
use temporary directories/files, and mock external processes (shell
compression tools, smtplib) where real execution would be slow, unreliable
across platforms, or would touch the network.

Tests interact with DataFile only through its public methods and observe
behavior through the filesystem or mocked collaborators - they do not read
or set any of the instance's internal attributes directly.
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

import datetime
import io
import logging
import os
import re
import shutil
import tempfile
import time
import unittest
from typing import Dict
from unittest.mock import patch

from wwpdb.io.file.DataFile import DataFile, DataFileMode

logger = logging.getLogger(__name__)

TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}:\d{2}:\d{2}:\d{2}$")


class DataFileUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.mkdtemp(prefix="DataFileUnitTests_")

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def __path(self, *parts: str) -> str:
        return os.path.join(self.__tmpDir, *parts)

    def __write(self, path: str, content: str = "") -> None:
        with open(path, "w") as fh:
            fh.write(content)

    # ------------------------------------------------------------------
    # existence / size accessors
    # ------------------------------------------------------------------
    def testSrcFileExistsAndDstFileExists(self) -> None:
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")

        df = DataFile(srcPath)
        self.assertFalse(df.srcFileExists())
        self.assertFalse(df.dstFileExists())
        self.assertFalse(df.dstDirExists())

        self.__write(srcPath, "hello")
        self.assertTrue(df.srcFileExists())

        df.dst(dstPath)
        self.assertFalse(df.dstFileExists())
        self.assertTrue(df.dstDirExists())

        df.dst(self.__path("nosuchdir", "dst.txt"))
        self.assertFalse(df.dstDirExists())

    def testSrcAndDstFileSize(self) -> None:
        srcPath = self.__path("src.txt")
        df = DataFile(srcPath)
        # non-existent source -> size defaults to 0
        self.assertEqual(df.srcFileSize(), 0)
        self.assertEqual(df.dstFileSize(), 0)

        self.__write(srcPath, "0123456789")
        df = DataFile(srcPath)
        self.assertEqual(df.srcFileSize(), 10)

        dstPath = self.__path("dst.txt")
        df.copy(dstPath)
        self.assertEqual(df.dstFileSize(), 10)

    # ------------------------------------------------------------------
    # copy() / append()
    # ------------------------------------------------------------------
    def testCopySameTypeUsesPlainCopy(self) -> None:
        """Copying between two files with the same (uncompressed) extension
        should not shell out - it should use a direct filesystem copy."""
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")
        self.__write(srcPath, "some content\n")

        with patch("wwpdb.io.file.DataFile.os.system") as mockSystem:
            df = DataFile(srcPath)
            df.copy(dstPath)
            mockSystem.assert_not_called()

        self.assertTrue(os.path.exists(dstPath))
        with open(dstPath) as fh:
            self.assertEqual(fh.read(), "some content\n")

    def testAppendConcatenatesContent(self) -> None:
        """append() shells out via 'cat ... >> ...' even for matching types."""
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")
        self.__write(srcPath, "SECOND")
        self.__write(dstPath, "FIRST-")

        df = DataFile(srcPath)
        df.append(dstPath)

        with open(dstPath) as fh:
            self.assertEqual(fh.read(), "FIRST-SECOND")

    def testCopyToCompressedDestinationBuildsExpectedCommand(self) -> None:
        srcPath = self.__path("plain.txt")
        self.__write(srcPath, "data")

        cases = {
            ".gz": "gzip",
            ".bz2": "bzip2",
            ".Z": "compress",
        }
        for ext, expectedTool in cases.items():
            with self.subTest(ext=ext):
                dstPath = self.__path("out" + ext)
                with patch("wwpdb.io.file.DataFile.os.system", return_value=0) as mockSystem:
                    df = DataFile(srcPath)
                    df.copy(dstPath)
                    mockSystem.assert_called_once()
                    (cmd,) = mockSystem.call_args[0]
                self.assertIn("cat ", cmd)
                self.assertIn(expectedTool, cmd)
                self.assertIn(srcPath, cmd)
                self.assertIn(dstPath, cmd)

    def testCopyFromCompressedSourceBuildsExpectedCommand(self) -> None:
        dstPath = self.__path("plain-out.txt")

        cases = {
            ".gz": "zcat",
            ".Z": "zcat",
            ".bz2": "bzcat",
        }
        for ext, expectedTool in cases.items():
            with self.subTest(ext=ext):
                srcPath = self.__path("in" + ext)
                self.__write(srcPath, "")
                with patch("wwpdb.io.file.DataFile.os.system", return_value=0) as mockSystem:
                    df = DataFile(srcPath)
                    df.copy(dstPath)
                    mockSystem.assert_called_once()
                    (cmd,) = mockSystem.call_args[0]
                self.assertIn(expectedTool, cmd)
                self.assertIn(srcPath, cmd)
                self.assertIn(dstPath, cmd)

    def testCopyAppendUsesAppendRedirect(self) -> None:
        srcPath = self.__path("plain.txt")
        self.__write(srcPath, "data")
        dstPath = self.__path("out.gz")

        with patch("wwpdb.io.file.DataFile.os.system", return_value=0) as mockSystem:
            df = DataFile(srcPath)
            df.append(dstPath)
            (cmd,) = mockSystem.call_args[0]
        self.assertIn(">>", cmd)

    def testCopyWithNoSourceFileIsNoop(self) -> None:
        srcPath = self.__path("missing.txt")
        dstPath = self.__path("dst.txt")
        with patch("wwpdb.io.file.DataFile.os.system") as mockSystem:
            df = DataFile(srcPath)
            df.copy(dstPath)
            mockSystem.assert_not_called()
        self.assertFalse(os.path.exists(dstPath))

    def testCopyCreatesMissingDestinationDirectory(self) -> None:
        srcPath = self.__path("src.txt")
        self.__write(srcPath, "content")
        dstPath = self.__path("nested", "sub", "dst.txt")

        df = DataFile(srcPath)
        df.copy(dstPath)

        self.assertTrue(os.path.isdir(self.__path("nested", "sub")))
        self.assertTrue(os.path.exists(dstPath))

    # ------------------------------------------------------------------
    # compare()
    # ------------------------------------------------------------------
    def testCompareSameTypeIdenticalAndDifferentContent(self) -> None:
        srcPath = self.__path("a.txt")
        dstPath = self.__path("b.txt")
        self.__write(srcPath, "same")
        self.__write(dstPath, "same")

        df = DataFile(srcPath)
        self.assertTrue(df.compare(dstPath))

        self.__write(dstPath, "different")
        df2 = DataFile(srcPath)
        self.assertFalse(df2.compare(dstPath))

    def testCompareMissingFilesReturnsFalse(self) -> None:
        srcPath = self.__path("missing-src.txt")
        dstPath = self.__path("missing-dst.txt")
        df = DataFile(srcPath)
        self.assertFalse(df.compare(dstPath))

        self.__write(srcPath, "content")
        df = DataFile(srcPath)
        self.assertFalse(df.compare(dstPath))

    def testCompareCrossTypeIdenticalContent(self) -> None:
        srcPath = self.__path("input.gz")
        dstPath = self.__path("output.bz2")
        self.__write(srcPath)
        self.__write(dstPath)

        createdTargets = []

        def fakeSystem(cmd: str) -> int:
            target = cmd[cmd.index(">") + 1 :].strip()
            createdTargets.append(target)
            with open(target, "w") as fh:
                fh.write("identical-payload")
            return 0

        with patch("wwpdb.io.file.DataFile.os.system", side_effect=fakeSystem):
            df = DataFile(srcPath)
            result = df.compare(dstPath)

        self.assertTrue(result)
        self.assertEqual(len(createdTargets), 2)
        for target in createdTargets:
            self.assertFalse(os.path.exists(target), "temporary decompressed file should be cleaned up")

    def testCompareCrossTypeDifferentContent(self) -> None:
        srcPath = self.__path("input.gz")
        dstPath = self.__path("output.bz2")
        self.__write(srcPath)
        self.__write(dstPath)

        def fakeSystem(cmd: str) -> int:
            target = cmd[cmd.index(">") + 1 :].strip()
            content = "src-payload" if "input.gz" in cmd else "dst-payload"
            with open(target, "w") as fh:
                fh.write(content)
            return 0

        with patch("wwpdb.io.file.DataFile.os.system", side_effect=fakeSystem):
            df = DataFile(srcPath)
            result = df.compare(dstPath)

        self.assertFalse(result)

    # ------------------------------------------------------------------
    # remove()
    # ------------------------------------------------------------------
    def testRemoveFile(self) -> None:
        srcPath = self.__path("src.txt")
        self.__write(srcPath, "content")
        df = DataFile(srcPath)
        self.assertTrue(df.srcFileExists())
        df.remove()
        self.assertFalse(df.srcFileExists())

    def testRemoveNonExistentIsSafe(self) -> None:
        df = DataFile(self.__path("missing.txt"))
        df.remove()
        self.assertFalse(df.srcFileExists())

    def testRemoveDirectory(self) -> None:
        dirPath = self.__path("adir")
        os.makedirs(dirPath)
        self.__write(os.path.join(dirPath, "inner.txt"), "x")
        df = DataFile(dirPath)
        df.remove()
        self.assertFalse(os.path.exists(dirPath))

    def testRemoveSymlink(self) -> None:
        targetPath = self.__path("target.txt")
        linkPath = self.__path("link.txt")
        self.__write(targetPath, "content")
        os.symlink(targetPath, linkPath)
        df = DataFile(linkPath)
        df.remove()
        self.assertFalse(os.path.islink(linkPath))
        self.assertTrue(os.path.exists(targetPath))

    # ------------------------------------------------------------------
    # move()
    # ------------------------------------------------------------------
    def testMoveSameTypeSucceeds(self) -> None:
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")
        self.__write(srcPath, "moved content")

        df = DataFile(srcPath)
        df.move(dstPath)

        self.assertFalse(os.path.exists(srcPath))
        self.assertTrue(os.path.exists(dstPath))
        with open(dstPath) as fh:
            self.assertEqual(fh.read(), "moved content")

    def testMoveDifferentTypeIsNoop(self) -> None:
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.gz")
        self.__write(srcPath, "content")

        df = DataFile(srcPath)
        df.move(dstPath)

        # __move() only performs shutil.move() when src/dst compression
        # types match; otherwise it silently does nothing.
        self.assertTrue(os.path.exists(srcPath))
        self.assertFalse(os.path.exists(dstPath))

    # ------------------------------------------------------------------
    # symLink() / symLinkRelative()
    # ------------------------------------------------------------------
    def testSymLinkAbsolute(self) -> None:
        srcPath = self.__path("target.txt")
        linkPath = self.__path("sub", "link.txt")
        self.__write(srcPath, "linked content")

        df = DataFile(srcPath)
        df.symLink(linkPath)

        self.assertTrue(os.path.islink(linkPath))
        self.assertEqual(os.readlink(linkPath), os.path.abspath(srcPath))
        with open(linkPath) as fh:
            self.assertEqual(fh.read(), "linked content")

    def testSymLinkRelative(self) -> None:
        srcPath = self.__path("target.txt")
        linkPath = self.__path("sub1", "sub2", "link.txt")
        self.__write(srcPath, "relative link content")

        df = DataFile(srcPath)
        df.symLinkRelative(linkPath)

        self.assertTrue(os.path.islink(linkPath))
        self.assertTrue(os.readlink(linkPath).startswith(".."))
        with open(linkPath) as fh:
            self.assertEqual(fh.read(), "relative link content")

    def testSymLinkWithMissingSourceIsNoop(self) -> None:
        srcPath = self.__path("missing.txt")
        linkPath = self.__path("link.txt")
        df = DataFile(srcPath)
        df.symLink(linkPath)
        df.symLinkRelative(linkPath)
        self.assertFalse(os.path.exists(linkPath))

    # ------------------------------------------------------------------
    # timestamps / newerThan
    # ------------------------------------------------------------------
    def testSrcModTimeAndTimeStamp(self) -> None:
        srcPath = self.__path("src.txt")
        self.__write(srcPath, "x")
        expectedMTime = os.stat(srcPath).st_mtime

        df = DataFile(srcPath)
        ts = df.srcModTime()
        self.assertIsNotNone(ts)
        if ts:
            self.assertAlmostEqual(ts, expectedMTime, delta=1)

        stamp = df.srcModTimeStamp()
        self.assertIsNotNone(stamp)
        if stamp is not None:
            self.assertRegex(stamp, TIMESTAMP_RE)

    def testSrcModTimeMissingFile(self) -> None:
        df = DataFile(self.__path("missing.txt"))
        self.assertIsNone(df.srcModTime())
        self.assertIsNone(df.srcModTimeStamp())

    def testNewerThan(self) -> None:
        olderPath = self.__path("older.txt")
        newerPath = self.__path("newer.txt")
        self.__write(olderPath, "old")
        self.__write(newerPath, "new")

        now = time.time()
        os.utime(olderPath, (now - 100, now - 100))
        os.utime(newerPath, (now, now))

        dfOlder = DataFile(olderPath)
        dfNewer = DataFile(newerPath)

        self.assertIsNone(dfOlder.newerThan(None))
        self.assertIsNone(dfOlder.newerThan(self.__path("missing.txt")))
        self.assertFalse(dfOlder.newerThan(newerPath))
        self.assertTrue(dfNewer.newerThan(olderPath))
        self.assertFalse(dfOlder.newerThan(olderPath))

        dfMissing = DataFile(self.__path("missing.txt"))
        self.assertIsNone(dfMissing.newerThan(olderPath))

    # ------------------------------------------------------------------
    # file mode
    # ------------------------------------------------------------------
    def testSetSrcAndDstFileMode(self) -> None:
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")
        self.__write(srcPath, "content")
        self.__write(dstPath, "content")

        df = DataFile(srcPath)
        df.dst(dstPath)

        self.assertTrue(df.setSrcFileMode(0o600))
        self.assertEqual(os.stat(srcPath).st_mode & 0o777, 0o600)

        self.assertTrue(df.setDstFileMode(0o640))
        self.assertEqual(os.stat(dstPath).st_mode & 0o777, 0o640)

    def testSetFileModeMissingFileReturnsFalse(self) -> None:
        df = DataFile(self.__path("missing-src.txt"))
        df.dst(self.__path("missing-dst.txt"))
        self.assertFalse(df.setSrcFileMode(0o600))
        self.assertFalse(df.setDstFileMode(0o600))

    # ------------------------------------------------------------------
    # timeMode() applied via copy()
    # ------------------------------------------------------------------
    def testTimeModePreserve(self) -> None:
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")
        self.__write(srcPath, "content")
        past = time.time() - 5000
        os.utime(srcPath, (past, past))

        df = DataFile(srcPath)
        df.timeMode("preserve")
        df.copy(dstPath)

        self.assertAlmostEqual(os.stat(dstPath).st_mtime, past, delta=1)

    def testTimeModeToday(self) -> None:
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")
        self.__write(srcPath, "content")

        df = DataFile(srcPath)
        df.timeMode("today")
        df.copy(dstPath)

        expected = int(time.mktime(datetime.datetime.today().timetuple()))  # noqa: DTZ002
        self.assertAlmostEqual(os.stat(dstPath).st_mtime, expected, delta=5)

    def testTimeModeYesterdayTomorrowLastweek(self) -> None:
        offsets: Dict[DataFileMode, int] = {"yesterday": -1, "tomorrow": 1, "lastweek": -7}
        for tMode, days in offsets.items():
            with self.subTest(tMode=tMode):
                srcPath = self.__path(f"src-{tMode}.txt")
                dstPath = self.__path(f"dst-{tMode}.txt")
                self.__write(srcPath, "content")

                df = DataFile(srcPath)
                df.timeMode(tMode)
                df.copy(dstPath)

                expectedDt = datetime.datetime.today() + datetime.timedelta(days=days)  # noqa: DTZ002
                expected = int(time.mktime(expectedDt.timetuple()))
                self.assertAlmostEqual(os.stat(dstPath).st_mtime, expected, delta=5)

    def testTimeModeNoneLeavesTimestampUntouched(self) -> None:
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")
        self.__write(srcPath, "content")

        beforeCopy = time.time()
        df = DataFile(srcPath)
        df.timeMode(None)
        df.copy(dstPath)

        # mtime should reflect actual copy time, not a specially-set value.
        self.assertGreaterEqual(os.stat(dstPath).st_mtime, beforeCopy - 1)

    # ------------------------------------------------------------------
    # pr()
    # ------------------------------------------------------------------
    def testPrIncludesSourceAndDestinationInfo(self) -> None:
        srcPath = self.__path("src.txt")
        dstPath = self.__path("dst.txt")
        self.__write(srcPath, "content")
        self.__write(dstPath, "content")

        df = DataFile(srcPath)
        df.dst(dstPath)

        buf = io.StringIO()
        df.pr(buf)
        output = buf.getvalue()

        self.assertIn(srcPath, output)
        self.assertIn(dstPath, output)
        self.assertIn("Source", output)
        self.assertIn("Destination", output)

    def testPrWithoutDestination(self) -> None:
        srcPath = self.__path("src.txt")
        self.__write(srcPath, "content")

        df = DataFile(srcPath)
        buf = io.StringIO()
        df.pr(buf)
        output = buf.getvalue()

        self.assertIn(srcPath, output)
        self.assertNotIn("Destination", output)

    # ------------------------------------------------------------------
    # eMail()
    # ------------------------------------------------------------------
    def testEMailRaisesOnPlainFileDueToBinaryReadBug(self) -> None:
        """eMail() opens the source file in binary mode ("rb") but passes the
        resulting bytes straight into MIMEText, which requires str under
        Python 3. This pre-existing bug means eMail() currently cannot
        succeed for any input (it is unused elsewhere in the codebase and is
        marked "# pragma: no cover"). This test documents current behavior
        rather than masking it - it should start failing (and be updated)
        if that bug is ever fixed.
        """
        srcPath = self.__path("src.txt")
        self.__write(srcPath, "email body content")

        with patch("wwpdb.io.file.DataFile.smtplib.SMTP") as mockSmtpClass:
            df = DataFile(srcPath)
            with self.assertRaises(AttributeError):
                df.eMail("to@example.com", "from@example.com", "Test Subject")
            mockSmtpClass.assert_not_called()

        self.assertTrue(os.path.exists(srcPath))

    def testEMailSkippedWhenSourceMissing(self) -> None:
        df = DataFile(self.__path("missing.txt"))
        with patch("wwpdb.io.file.DataFile.smtplib.SMTP") as mockSmtpClass:
            df.eMail("to@example.com", "from@example.com", "Test Subject")
            mockSmtpClass.assert_not_called()

    # ------------------------------------------------------------------
    # no-op stub methods
    # ------------------------------------------------------------------
    def testSetDstMTimeStubsDoNotRaise(self) -> None:
        df = DataFile(self.__path("src.txt"))
        df.setDstMTimeYYYYMMDD("2020-01-01")
        df.setDstMTime(self.__path("ref.txt"))


if __name__ == "__main__":
    unittest.main()
