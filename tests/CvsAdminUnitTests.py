##
# File:    CvsAdminUnitTests.py
# Author:  Ezra Peisach
# Date:    22-Sep-2026
#
# Updates:
#
##
"""Unit test cases for CvsAdmin (CvsAdmin and CvsSandBoxAdmin) using a mocked cvs client process.

Unlike CvsAdminTests.py these tests do not require a live CVS pserver -
subprocess.call is replaced with a fake that writes canned content to
whatever file(s) the constructed shell command would have redirected its
output to, then returns a canned exit code. This lets the tests exercise
the command construction, redirect handling, and return-status/text
extraction logic without running a real cvs client/server round trip.

Tests interact with CvsAdmin/CvsSandBoxAdmin only through their public
methods - they do not read or set any of the instances' internal
attributes directly.
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

import logging
import os
import re
import shutil
import tempfile
import unittest
from typing import Callable, List, Optional
from unittest.mock import MagicMock, patch

from wwpdb.io.cvs.CvsAdmin import CvsAdmin, CvsSandBoxAdmin

logger = logging.getLogger(__name__)

# Matches the stdout/stderr redirect targets produced by CvsWrapperBase._getRedirect(),
# e.g. " > out 2> err ", " >> out 2>> err " or " > out 2>&1 ".
_REDIRECT_TARGET_RE = re.compile(r"(?:>>?|2>>?)\s*(\S+)")


def _redirectTargets(command: str) -> List[str]:
    """Return the file paths a shell redirect in command would write to (skips "2>&1" style merges)."""
    return [path for path in _REDIRECT_TARGET_RE.findall(command) if not path.startswith("&")]


def _fakeCvsServer(returncode: int = 0, content: Optional[str] = None) -> Callable[..., int]:
    """Build a subprocess.call replacement simulating a cvs client talking to a pserver.

    Rather than running a real cvs client, it writes content to every redirect
    target found in the command string and returns returncode - mirroring what
    a real cvs invocation would leave behind for CvsAdmin/CvsSandBoxAdmin to read back.
    """

    def _sideEffect(command: str, shell: bool = True) -> int:  # noqa: ARG001
        if content is not None:
            for target in _redirectTargets(command):
                with open(target, "w") as fh:
                    fh.write(content)
        return returncode

    return _sideEffect


class CvsAdminUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.mkdtemp(prefix="CvsAdminUnitTests_")
        self.__callPatcher = patch("wwpdb.io.cvs.CvsAdmin.subprocess.call")
        self.__mockCall: MagicMock = self.__callPatcher.start()
        self.__mockCall.side_effect = _fakeCvsServer()

    def tearDown(self) -> None:
        self.__callPatcher.stop()
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def __authenticatedAdmin(self) -> CvsAdmin:
        vc = CvsAdmin(tmpPath=self.__tmpDir, verbose=False)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        vc.setAuthInfo(user="tester", password="secret")
        return vc

    # ------------------------------------------------------------------
    # getHistory
    # ------------------------------------------------------------------
    def testGetHistorySuccess(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="cvs history: 3 file(s) examined\n")
        vc = self.__authenticatedAdmin()
        ok, text = vc.getHistory(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertTrue(ok)
        self.assertEqual(text, "cvs history: 3 file(s) examined")
        self.__mockCall.assert_called_once()

    def testGetHistoryNoAuth(self) -> None:
        """Documents current behavior: _setCvsRoot()'s exception handler itself raises
        (it passes the exception object, not str(e), to a text-mode file write), so a
        missing auth info crashes rather than returning a graceful (False, message).
        """
        vc = CvsAdmin(tmpPath=self.__tmpDir, verbose=False)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        with self.assertRaises(TypeError):
            vc.getHistory(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.__mockCall.assert_not_called()

    def testGetHistoryCommandFails(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=1, content=None)
        vc = self.__authenticatedAdmin()
        ok, text = vc.getHistory(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertFalse(ok)
        self.assertEqual(text, "")

    # ------------------------------------------------------------------
    # getRevisionList
    # ------------------------------------------------------------------
    def testGetRevisionListSuccess(self) -> None:
        historyText = "A 2013-01-20 09:00:00 +0000 jdw 1.2 ATP.cif\nM 2013-01-27 10:15:00 +0000 jdw 1.3 ATP.cif\n"
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content=historyText)
        vc = self.__authenticatedAdmin()
        ok, revList = vc.getRevisionList(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertTrue(ok)
        self.assertEqual(
            revList,
            [
                ("1.3", "M", "2013-01-27:10:15:00"),
                ("1.2", "A", "2013-01-20:09:00:00"),
            ],
        )

    def testGetRevisionListNoAuth(self) -> None:
        """See testGetHistoryNoAuth: missing auth info crashes rather than failing gracefully."""
        vc = CvsAdmin(tmpPath=self.__tmpDir, verbose=False)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        with self.assertRaises(TypeError):
            vc.getRevisionList(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.__mockCall.assert_not_called()

    # ------------------------------------------------------------------
    # checkOutFile
    # ------------------------------------------------------------------
    def testCheckOutFileSuccess(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="cvs checkout: Updating ligand-dict-v3/A/ATP\n")
        vc = self.__authenticatedAdmin()
        ok, text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/ATP.cif", outPath="ATP-latest.cif")
        self.assertTrue(ok)
        self.assertEqual(text, "cvs checkout: Updating ligand-dict-v3/A/ATP")

    def testCheckOutFileFailure(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=1, content="cvs [checkout aborted]: connect to cvs.example.org failed\n")
        vc = self.__authenticatedAdmin()
        ok, text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/ATP.cif", outPath="ATP-latest.cif")
        self.assertFalse(ok)
        self.assertEqual(text, "cvs [checkout aborted]: connect to cvs.example.org failed")

    def testCheckOutFileEmptyFileName(self) -> None:
        vc = self.__authenticatedAdmin()
        ok, text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/", outPath="ATP-latest.cif")
        self.assertFalse(ok)
        self.assertIn("repository project path issue", text)
        self.__mockCall.assert_not_called()

    def testCheckOutFileNoAuth(self) -> None:
        """See testGetHistoryNoAuth: missing auth info crashes rather than failing gracefully."""
        vc = CvsAdmin(tmpPath=self.__tmpDir, verbose=False)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        with self.assertRaises(TypeError):
            vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/ATP.cif", outPath="ATP-latest.cif")
        self.__mockCall.assert_not_called()

    def testCheckOutFileWithRevision(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        vc = self.__authenticatedAdmin()
        ok, _text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/ATP.cif", outPath="ATP-1.2.cif", revId="1.2")
        self.assertTrue(ok)
        command = self.__mockCall.call_args.args[0]
        self.assertIn("-r 1.2", command)

    # ------------------------------------------------------------------
    # cleanup
    # ------------------------------------------------------------------
    def testCleanupWithoutPriorUse(self) -> None:
        vc = CvsAdmin(tmpPath=self.__tmpDir, verbose=False)
        self.assertTrue(vc.cleanup())

    def testCleanupAfterUse(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="history\n")
        vc = self.__authenticatedAdmin()
        vc.getHistory(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertTrue(vc.cleanup())


class CvsSandBoxAdminUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.mkdtemp(prefix="CvsSandBoxAdminUnitTests_")
        self.__sandBoxDir = os.path.join(self.__tmpDir, "sandbox")
        self.__callPatcher = patch("wwpdb.io.cvs.CvsAdmin.subprocess.call")
        self.__mockCall: MagicMock = self.__callPatcher.start()
        self.__mockCall.side_effect = _fakeCvsServer()

    def tearDown(self) -> None:
        self.__callPatcher.stop()
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def __sandbox(self) -> CvsSandBoxAdmin:
        vc = CvsSandBoxAdmin(tmpPath=self.__tmpDir, verbose=False)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        vc.setAuthInfo(user="tester", password="secret")
        self.assertTrue(vc.setSandBoxTopPath(self.__sandBoxDir))
        return vc

    # ------------------------------------------------------------------
    # setSandBoxTopPath / getSandBoxTopPath
    # ------------------------------------------------------------------
    def testSetSandBoxTopPathCreatesDirectory(self) -> None:
        vc = CvsSandBoxAdmin(tmpPath=self.__tmpDir, verbose=False)
        self.assertFalse(os.path.isdir(self.__sandBoxDir))
        ok = vc.setSandBoxTopPath(self.__sandBoxDir)
        self.assertTrue(ok)
        self.assertTrue(os.path.isdir(self.__sandBoxDir))
        self.assertEqual(vc.getSandBoxTopPath(), os.path.abspath(self.__sandBoxDir))

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root bypasses filesystem permission checks")
    def testSetSandBoxTopPathPermissionDenied(self) -> None:
        parentDir = os.path.join(self.__tmpDir, "readonly-parent")
        os.mkdir(parentDir)
        os.chmod(parentDir, 0o500)
        try:
            vc = CvsSandBoxAdmin(tmpPath=self.__tmpDir, verbose=False)
            ok = vc.setSandBoxTopPath(os.path.join(parentDir, "child"))
            self.assertFalse(ok)
        finally:
            # restore write permission before tearDown's shutil.rmtree runs
            os.chmod(parentDir, 0o700)

    # ------------------------------------------------------------------
    # checkOut
    # ------------------------------------------------------------------
    def testCheckOutSuccess(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        vc = self.__sandbox()
        ok, _text = vc.checkOut(projectPath="test-project-v1")
        self.assertTrue(ok)
        self.__mockCall.assert_called_once()

    def testCheckOutFailure(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=1, content="cvs checkout: authorization failed\n")
        vc = self.__sandbox()
        ok, text = vc.checkOut(projectPath="test-project-v1")
        self.assertFalse(ok)
        self.assertEqual(text, "cvs checkout: authorization failed")

    def testCheckOutWithoutSandBoxTopPath(self) -> None:
        vc = CvsSandBoxAdmin(tmpPath=self.__tmpDir, verbose=False)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        vc.setAuthInfo(user="tester", password="secret")
        ok, text = vc.checkOut(projectPath="test-project-v1")
        self.assertFalse(ok)
        self.assertIn("repository project path issue", text)
        self.__mockCall.assert_not_called()

    def testCheckOutWithoutProjectPath(self) -> None:
        vc = self.__sandbox()
        ok, text = vc.checkOut(projectPath=None)
        self.assertFalse(ok)
        self.assertIn("repository project path issue", text)
        self.__mockCall.assert_not_called()

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------
    def testUpdateExistingWritablePath(self) -> None:
        vc = self.__sandbox()
        os.makedirs(os.path.join(self.__sandBoxDir, "test-project-v1"))
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        ok, _text = vc.update(projectDir="test-project-v1")
        self.assertTrue(ok)
        self.__mockCall.assert_called_once()
        command = self.__mockCall.call_args.args[0]
        self.assertIn("update", command)

    def testUpdateMissingPathFallsBackToCheckOut(self) -> None:
        vc = self.__sandbox()
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        ok, _text = vc.update(projectDir="test-project-v2")
        self.assertTrue(ok)
        self.assertTrue(os.path.isdir(os.path.join(self.__sandBoxDir, "test-project-v2")))
        command = self.__mockCall.call_args.args[0]
        self.assertIn(" co ", command)

    def testUpdateList(self) -> None:
        vc = self.__sandbox()
        os.makedirs(os.path.join(self.__sandBoxDir, "proj1"))
        os.makedirs(os.path.join(self.__sandBoxDir, "proj2"))
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        dataList = [("proj1", ".", False), ("proj2", ".", False)]
        successList, resultList, diagTextList = vc.updateList(dataList, procName="worker-1", optionsD={}, workingDir=self.__tmpDir)
        self.assertEqual(successList, dataList)
        self.assertEqual(resultList, dataList)
        self.assertEqual(len(diagTextList), 2)

    # ------------------------------------------------------------------
    # add
    # ------------------------------------------------------------------
    def testAddSuccess(self) -> None:
        vc = self.__sandbox()
        dstDir = os.path.join(self.__sandBoxDir, "test-project-v1", "D1")
        os.makedirs(dstDir)
        filePath = os.path.join(dstDir, "F1.DAT")
        with open(filePath, "w") as fh:
            fh.write("data")
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        ok, _text = vc.add(projectDir="test-project-v1", relProjectPath=os.path.join("D1", "F1.DAT"))
        self.assertTrue(ok)

    def testAddMissingPath(self) -> None:
        vc = self.__sandbox()
        ok, text = vc.add(projectDir="test-project-v1", relProjectPath=os.path.join("D1", "F1.DAT"))
        self.assertFalse(ok)
        self.assertIn("repository project path issue", text)
        self.__mockCall.assert_not_called()

    # ------------------------------------------------------------------
    # commit
    # ------------------------------------------------------------------
    def testCommitSuccess(self) -> None:
        vc = self.__sandbox()
        dstDir = os.path.join(self.__sandBoxDir, "test-project-v1", "D1")
        os.makedirs(dstDir)
        filePath = os.path.join(dstDir, "F1.DAT")
        with open(filePath, "w") as fh:
            fh.write("data")
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        ok, _text = vc.commit(projectDir="test-project-v1", relProjectPath=os.path.join("D1", "F1.DAT"))
        self.assertTrue(ok)

    def testCommitMissingPath(self) -> None:
        vc = self.__sandbox()
        ok, text = vc.commit(projectDir="test-project-v1", relProjectPath=os.path.join("D1", "F1.DAT"))
        self.assertFalse(ok)
        self.assertIn("repository project path issue", text)
        self.__mockCall.assert_not_called()

    # ------------------------------------------------------------------
    # remove
    # ------------------------------------------------------------------
    def testRemoveWithSaveCopy(self) -> None:
        vc = self.__sandbox()
        dstDir = os.path.join(self.__sandBoxDir, "test-project-v1", "D1")
        os.makedirs(dstDir)
        filePath = os.path.join(dstDir, "F1.DAT")
        with open(filePath, "w") as fh:
            fh.write("data")
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        relPath = os.path.join("D1", "F1.DAT")
        ok, _text = vc.remove(projectDir="test-project-v1", relProjectPath=relPath, saveCopy=True)
        self.assertTrue(ok)
        savedPath = os.path.join(self.__sandBoxDir, "test-project-v1", "REMOVED", "F1.DAT")
        self.assertTrue(os.path.exists(savedPath))

    def testRemoveWithoutSaveCopy(self) -> None:
        vc = self.__sandbox()
        dstDir = os.path.join(self.__sandBoxDir, "test-project-v1", "D1")
        os.makedirs(dstDir)
        filePath = os.path.join(dstDir, "F1.DAT")
        with open(filePath, "w") as fh:
            fh.write("data")
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        relPath = os.path.join("D1", "F1.DAT")
        ok, _text = vc.remove(projectDir="test-project-v1", relProjectPath=relPath, saveCopy=False)
        self.assertTrue(ok)
        removedDir = os.path.join(self.__sandBoxDir, "test-project-v1", "REMOVED")
        self.assertFalse(os.path.isdir(removedDir))

    def testRemoveShortRelPathIsNoOp(self) -> None:
        vc = self.__sandbox()
        ok, text = vc.remove(projectDir="test-project-v1", relProjectPath="ab")
        self.assertFalse(ok)
        self.assertEqual(text, "")
        self.__mockCall.assert_not_called()

    def testRemoveMissingPath(self) -> None:
        vc = self.__sandbox()
        ok, text = vc.remove(projectDir="test-project-v1", relProjectPath=os.path.join("D1", "F1.DAT"))
        self.assertFalse(ok)
        self.assertIn("repository project path issue", text)
        self.__mockCall.assert_not_called()

    # ------------------------------------------------------------------
    # removeDir
    # ------------------------------------------------------------------
    def testRemoveDirSuccess(self) -> None:
        vc = self.__sandbox()
        dstDir = os.path.join(self.__sandBoxDir, "test-project-v1", "DIR1")
        os.makedirs(dstDir)
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        ok, _text = vc.removeDir(projectDir="test-project-v1", relProjectPath="DIR1")
        self.assertTrue(ok)

    def testRemoveDirShortRelPathIsNoOp(self) -> None:
        vc = self.__sandbox()
        ok, text = vc.removeDir(projectDir="test-project-v1", relProjectPath="ab")
        self.assertFalse(ok)
        self.assertEqual(text, "")
        self.__mockCall.assert_not_called()

    def testRemoveDirMissingPath(self) -> None:
        vc = self.__sandbox()
        ok, text = vc.removeDir(projectDir="test-project-v1", relProjectPath="DIR1")
        self.assertFalse(ok)
        self.assertIn("repository project path issue", text)
        self.__mockCall.assert_not_called()


if __name__ == "__main__":
    unittest.main()
