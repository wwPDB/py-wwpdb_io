##
# File:    CvsUtilityUnitTests.py
# Author:  Ezra Peisach
# Date:    22-Sep-2026
#
# Updates:
#
##
"""Unit test cases for CvsUtility.CvsWrapper using a mocked cvs client process.

Unlike CvsUtilityTests.py these tests do not require a live CVS pserver -
subprocess.call is replaced with a fake that writes canned content to
whatever file(s) the constructed shell command would have redirected its
output to, then returns a canned exit code. This lets the tests exercise
the command construction, redirect handling, and file-parsing logic without
running a real cvs client/server round trip.

Tests interact with CvsWrapper only through its public methods - they do not
read or set any of the instance's internal attributes directly.
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

import logging
import re
import shutil
import tempfile
import unittest
from typing import Callable, List, Optional
from unittest.mock import MagicMock, patch

from wwpdb.io.cvs.CvsUtility import CvsWrapper

logger = logging.getLogger(__name__)

# Matches the stdout/stderr redirect targets produced by CvsWrapper.__getRedirect(),
# e.g. " > out 2> err ", " >> out 2>> err " or " > out 2>&1 ".
_REDIRECT_TARGET_RE = re.compile(r"(?:>>?|2>>?)\s*(\S+)")


def _redirectTargets(command: str) -> List[str]:
    """Return the file paths a shell redirect in command would write to (skips "2>&1" style merges)."""
    return [path for path in _REDIRECT_TARGET_RE.findall(command) if not path.startswith("&")]


def _fakeCvsServer(returncode: int = 0, content: Optional[str] = None) -> Callable[..., int]:
    """Build a subprocess.call replacement simulating a cvs client talking to a pserver.

    Rather than running a real cvs client, it writes content to every redirect
    target found in the command string and returns returncode - mirroring what
    a real cvs invocation would leave behind for CvsWrapper to read back.
    """

    def _sideEffect(command: str, shell: bool = True) -> int:  # noqa: ARG001
        if content is not None:
            for target in _redirectTargets(command):
                with open(target, "w") as fh:
                    fh.write(content)
        return returncode

    return _sideEffect


class CvsUtilityUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.mkdtemp(prefix="CvsUtilityUnitTests_")
        self.__callPatcher = patch("wwpdb.io.cvs.CvsUtility.subprocess.call")
        self.__mockCall: MagicMock = self.__callPatcher.start()
        self.__mockCall.side_effect = _fakeCvsServer()

    def tearDown(self) -> None:
        self.__callPatcher.stop()
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    def __authenticatedWrapper(self) -> CvsWrapper:
        vc = CvsWrapper(tmpPath=self.__tmpDir)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        vc.setAuthInfo(user="tester", password="secret")
        return vc

    # ------------------------------------------------------------------
    # getHistory
    # ------------------------------------------------------------------
    def testGetHistorySuccess(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="cvs history: 3 file(s) examined\n")
        vc = self.__authenticatedWrapper()
        text = vc.getHistory(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertEqual(text, "cvs history: 3 file(s) examined\n")
        self.__mockCall.assert_called_once()

    def testGetHistoryNoAuth(self) -> None:
        """Without credentials, root construction fails and the command is never run."""
        vc = CvsWrapper(tmpPath=self.__tmpDir)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        text = vc.getHistory(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertEqual(text, "")
        self.__mockCall.assert_not_called()

    def testGetHistoryCommandProducesNoOutput(self) -> None:
        """A failing cvs client that never wrote an output file yields empty text."""
        self.__mockCall.side_effect = _fakeCvsServer(returncode=1, content=None)
        vc = self.__authenticatedWrapper()
        text = vc.getHistory(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertEqual(text, "")

    # ------------------------------------------------------------------
    # getRevisionList
    # ------------------------------------------------------------------
    def testGetRevisionListSuccess(self) -> None:
        historyText = "A 2013-01-20 09:00:00 +0000 jdw 1.2 ATP.cif\nM 2013-01-27 10:15:00 +0000 jdw 1.3 ATP.cif\n"
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content=historyText)
        vc = self.__authenticatedWrapper()
        revList = vc.getRevisionList(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertEqual(
            revList,
            [
                ("1.3", "M", "2013-01-27:10:15:00"),
                ("1.2", "A", "2013-01-20:09:00:00"),
            ],
        )

    def testGetRevisionListNoAuth(self) -> None:
        vc = CvsWrapper(tmpPath=self.__tmpDir)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        revList = vc.getRevisionList(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertEqual(revList, [])
        self.__mockCall.assert_not_called()

    def testGetRevisionListMalformedLineStopsParsing(self) -> None:
        """Parsing stops at the first malformed line but keeps revisions already parsed."""
        historyText = "A 2013-01-20 09:00:00 +0000 jdw 1.2 ATP.cif\nmalformed\n"
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content=historyText)
        vc = self.__authenticatedWrapper()
        revList = vc.getRevisionList(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertEqual(revList, [("1.2", "A", "2013-01-20:09:00:00")])

    # ------------------------------------------------------------------
    # checkOutFile
    # ------------------------------------------------------------------
    def testCheckOutFileSuccess(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        vc = self.__authenticatedWrapper()
        text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/ATP.cif", outPath="ATP-latest.cif")
        self.assertEqual(text, "")
        self.__mockCall.assert_called_once()

    def testCheckOutFileFailure(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=1, content="cvs [checkout aborted]: connect to cvs.example.org failed\n")
        vc = self.__authenticatedWrapper()
        text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/ATP.cif", outPath="ATP-latest.cif")
        self.assertEqual(text, "cvs [checkout aborted]: connect to cvs.example.org failed\n")

    def testCheckOutFileEmptyFileName(self) -> None:
        vc = self.__authenticatedWrapper()
        text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/", outPath="ATP-latest.cif")
        self.assertEqual(text, "")
        self.__mockCall.assert_not_called()

    def testCheckOutFileNoAuth(self) -> None:
        vc = CvsWrapper(tmpPath=self.__tmpDir)
        vc.setRepositoryPath(host="cvs.example.org", path="/cvsroot")
        text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/ATP.cif", outPath="ATP-latest.cif")
        self.assertEqual(text, "")
        self.__mockCall.assert_not_called()

    def testCheckOutFileWithRevision(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="")
        vc = self.__authenticatedWrapper()
        text = vc.checkOutFile(cvsPath="ligand-dict-v3/A/ATP/ATP.cif", outPath="ATP-1.2.cif", revId="1.2")
        self.assertEqual(text, "")
        command = self.__mockCall.call_args.args[0]
        self.assertIn("-r 1.2", command)

    # ------------------------------------------------------------------
    # cleanup
    # ------------------------------------------------------------------
    def testCleanupAfterUse(self) -> None:
        self.__mockCall.side_effect = _fakeCvsServer(returncode=0, content="history\n")
        vc = self.__authenticatedWrapper()
        vc.getHistory(cvsPath="ligand-dict-v3/A/ATP/ATP.cif")
        self.assertIsNone(vc.cleanup())  # type: ignore

    def testCleanupWithoutPriorUseRaises(self) -> None:
        """Documents current behavior: cleanup() before any cvs call has no working directory to remove."""
        vc = CvsWrapper(tmpPath=self.__tmpDir)
        with self.assertRaises(TypeError):
            vc.cleanup()


if __name__ == "__main__":
    unittest.main()
