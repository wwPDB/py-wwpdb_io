##
# File:    DataMaintenanceTests.py
# Author:  Ezra Peisach
# Date:    28-Sep-2026
#
# Updates:
#
##
"""Unit test cases for DataMaintenance.

These tests are self-contained - ConfigInfo and PathInfo are replaced by
mocks that point into a temporary directory tree, so no site configuration
is required.

Tests interact with DataMaintenance only through its public methods and
observe behavior through the filesystem, the log stream, or the mocked
collaborators - they do not read or set any internal attributes directly.
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

import io
import os
import re
import shutil
import tempfile
import unittest
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, cast
from unittest.mock import patch

from wwpdb.io.file.DataMaintenance import DataMaintenance

if TYPE_CHECKING:
    from wwpdb.io.locator.PathInfo import PathInfoStorageType

DATASET_ID = "D_1000000001"
TIMESTAMP_RE = re.compile(r"^\d{4}-[A-Za-z]{3}-\d{2} \d{2}:\d{2}:\d{2}$")


class DataMaintenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__tmpDir = tempfile.mkdtemp(prefix="DataMaintenanceTests_")
        self.__log = io.StringIO()

        cfgPatcher = patch("wwpdb.io.file.DataMaintenance.ConfigInfo")
        self.__mockConfigInfo = cfgPatcher.start()
        self.addCleanup(cfgPatcher.stop)
        self.__mockConfigInfo.return_value.get.side_effect = self.__cfgGet

        piPatcher = patch("wwpdb.io.file.DataMaintenance.PathInfo")
        self.__mockPathInfo = piPatcher.start()
        self.addCleanup(piPatcher.stop)
        self.__pI = self.__mockPathInfo.return_value
        self.__pI.getArchivePath.side_effect = lambda dataSetId: self.__path("archive", dataSetId)
        self.__pI.getDepositPath.side_effect = lambda dataSetId: self.__path("deposit", dataSetId)
        self.__pI.getFilePathVersionTemplate.side_effect = self.__versionTemplate
        self.__pI.getFilePathContentTypeTemplate.side_effect = self.__contentTypeTemplate
        self.__pI.getFilePath.side_effect = self.__filePath

    def tearDown(self) -> None:
        shutil.rmtree(self.__tmpDir, ignore_errors=True)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def __cfgGet(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if key == "SITE_ARCHIVE_STORAGE_PATH":
            return self.__tmpDir
        return default

    def __sourceDir(self, dataSetId: str, fileSource: str) -> str:
        if fileSource in ["archive", "deposit"]:
            return self.__path(fileSource, dataSetId)
        return self.__path("session")

    def __versionTemplate(self, dataSetId: str, contentType: str = "model", formatType: str = "pdbx", fileSource: str = "archive", **_kw: Any) -> str:
        return os.path.join(self.__sourceDir(dataSetId, fileSource), "%s_%s_P1.%s.V*" % (dataSetId, contentType, formatType[:3]))

    def __contentTypeTemplate(self, dataSetId: str, contentType: str = "model", fileSource: str = "archive", **_kw: Any) -> str:
        return os.path.join(self.__sourceDir(dataSetId, fileSource), "%s_%s_P1.*.V*" % (dataSetId, contentType))

    def __filePath(self, dataSetId: str, contentType: str = "model", formatType: str = "pdbx", fileSource: str = "archive", **_kw: Any) -> str:
        return os.path.join(self.__sourceDir(dataSetId, fileSource), "%s_%s_P1.%s" % (dataSetId, contentType, formatType[:3]))

    def __path(self, *parts: str) -> str:
        return os.path.join(self.__tmpDir, *parts)

    def __touch(self, path: str, content: str = "x") -> str:
        dirPath = os.path.dirname(path)
        if not os.path.isdir(dirPath):
            os.makedirs(dirPath)
        with open(path, "w") as fh:
            fh.write(content)
        return path

    def __modelFiles(self, versions: List[int], fileSource: str = "archive", dataSetId: str = DATASET_ID) -> List[str]:
        base = os.path.join(self.__sourceDir(dataSetId, fileSource), "%s_model_P1.pdb" % dataSetId)
        return [self.__touch("%s.V%d" % (base, v)) for v in versions]

    def __dm(self, testMode: bool = False, verbose: bool = False) -> DataMaintenance:
        return DataMaintenance(siteId="WWPDB_TEST", testMode=testMode, verbose=verbose, log=self.__log)

    # ------------------------------------------------------------------
    # construction / session path
    # ------------------------------------------------------------------
    def testConstruction(self) -> None:
        self.__dm(verbose=True)
        self.__mockConfigInfo.assert_called_once_with("WWPDB_TEST")
        self.__mockPathInfo.assert_called_once_with(siteId="WWPDB_TEST", sessionPath=None, verbose=True, log=self.__log)

    def testDefaultConstruction(self) -> None:
        DataMaintenance()
        self.__mockConfigInfo.assert_called_once_with(None)

    def testSetSessionPathUsedForSessionSource(self) -> None:
        sessDir = self.__path("session")
        self.__modelFiles([1, 2], fileSource="session")
        dm = self.__dm()

        # No session path set - PathInfo is not updated
        dm.getVersionFileList(DATASET_ID, fileSource="session")
        self.__pI.setSessionPath.assert_not_called()

        dm.setSessionPath(sessDir)
        vL = dm.getVersionFileList(DATASET_ID, fileSource="session")
        self.__pI.setSessionPath.assert_called_with(sessDir)
        self.assertEqual([v for _f, v in vL], [2, 1])

        self.__pI.setSessionPath.reset_mock()
        dm.getContentTypeFileList(DATASET_ID, None, fileSource="session")
        self.__pI.setSessionPath.assert_called_once_with(sessDir)

    # ------------------------------------------------------------------
    # purgeLogs
    # ------------------------------------------------------------------
    def __makeLogs(self) -> List[str]:
        logDir = self.__path("archive", DATASET_ID, "log")
        return [self.__touch(os.path.join(logDir, n)) for n in ["a.log", "b.log", "keep.txt"]]

    def testPurgeLogs(self) -> None:
        a, b, keep = self.__makeLogs()
        dm = self.__dm(verbose=True)
        pL = dm.purgeLogs(DATASET_ID)
        self.assertEqual(sorted(pL), sorted([a, b]))
        self.assertFalse(os.path.exists(a))
        self.assertFalse(os.path.exists(b))
        self.assertTrue(os.path.exists(keep))
        self.assertIn("purging pattern is", self.__log.getvalue())
        self.assertIn("candidate path length is 2", self.__log.getvalue())

    def testPurgeLogsTestMode(self) -> None:
        a, b, _keep = self.__makeLogs()
        dm = self.__dm(testMode=True)
        pL = dm.purgeLogs(DATASET_ID)
        self.assertEqual(sorted(pL), sorted([a, b]))
        self.assertTrue(os.path.exists(a))
        self.assertTrue(os.path.exists(b))
        self.assertIn("TEST MODE skip remove", self.__log.getvalue())

    def testPurgeLogsRemoveFailureIgnored(self) -> None:
        a, b, _keep = self.__makeLogs()
        dm = self.__dm()
        with patch("wwpdb.io.file.DataMaintenance.os.remove", side_effect=OSError("denied")) as mRemove:
            pL = dm.purgeLogs(DATASET_ID)
        self.assertEqual(sorted(pL), sorted([a, b]))
        self.assertEqual(mRemove.call_count, 2)
        self.assertTrue(os.path.exists(a))

    def testPurgeLogsMissingDirectory(self) -> None:
        # Current behavior: when the log directory is not writable the
        # result list is never bound and an UnboundLocalError escapes.
        dm = self.__dm()
        with self.assertRaises(UnboundLocalError):
            dm.purgeLogs(DATASET_ID)

    # ------------------------------------------------------------------
    # reversePurge
    # ------------------------------------------------------------------
    def testReversePurge(self) -> None:
        v1, v2, v3 = self.__modelFiles([1, 2, 3])
        dm = self.__dm(verbose=True)
        rL = dm.reversePurge(DATASET_ID, "model")
        self.assertEqual(sorted(rL), sorted([v2, v3]))
        self.assertTrue(os.path.exists(v1))
        self.assertFalse(os.path.exists(v2))
        self.assertFalse(os.path.exists(v3))
        self.assertIn("candidate length is 3", self.__log.getvalue())
        _args, kw = self.__pI.getFilePath.call_args
        self.assertEqual(kw["fileSource"], "archive")
        self.assertEqual(kw["versionId"], "none")
        self.assertEqual(kw["partNumber"], 1)

    def testReversePurgeTestMode(self) -> None:
        v1, v2, v3 = self.__modelFiles([1, 2, 3])
        dm = self.__dm(testMode=True)
        rL = dm.reversePurge(DATASET_ID, "model", formatType="pdbx", partitionNumber=1)
        self.assertEqual(sorted(rL), sorted([v2, v3]))
        for f in (v1, v2, v3):
            self.assertTrue(os.path.exists(f))
        self.assertIn("TEST MODE skip remove", self.__log.getvalue())

    def testReversePurgeRemoveFailureIgnored(self) -> None:
        _v1, v2 = self.__modelFiles([1, 2])
        dm = self.__dm()
        with patch("wwpdb.io.file.DataMaintenance.os.remove", side_effect=OSError("denied")):
            rL = dm.reversePurge(DATASET_ID, "model")
        self.assertEqual(rL, [v2])
        self.assertTrue(os.path.exists(v2))

    def testReversePurgeNoFiles(self) -> None:
        dm = self.__dm()
        self.assertEqual(dm.reversePurge(DATASET_ID, "model"), [])

    def testReversePurgeFilePathFailure(self) -> None:
        # When PathInfo cannot produce a file name the base name is None
        # and building the glob pattern fails.
        self.__pI.getFilePath.side_effect = ValueError("bad")
        dm = self.__dm()
        with self.assertRaises(TypeError):
            dm.reversePurge(DATASET_ID, "model")

    # ------------------------------------------------------------------
    # removeWorkflowDir
    # ------------------------------------------------------------------
    def testRemoveWorkflowDirInvalidIds(self) -> None:
        dm = self.__dm()
        for dsId in [None, "X_1000000001", "D_1"]:
            self.assertFalse(dm.removeWorkflowDir(dsId))  # type: ignore[arg-type]

    def testRemoveWorkflowDirMissing(self) -> None:
        dm = self.__dm()
        self.assertFalse(dm.removeWorkflowDir(DATASET_ID))

    def testRemoveWorkflowDir(self) -> None:
        wfDir = self.__path("workflow", DATASET_ID)
        self.__touch(os.path.join(wfDir, "f.txt"))
        dm = self.__dm()
        self.assertTrue(dm.removeWorkflowDir(DATASET_ID))
        self.assertFalse(os.path.exists(wfDir))

    def testRemoveWorkflowDirTestMode(self) -> None:
        wfDir = self.__path("workflow", DATASET_ID)
        self.__touch(os.path.join(wfDir, "f.txt"))
        dm = self.__dm(testMode=True)
        self.assertTrue(dm.removeWorkflowDir(DATASET_ID))
        self.assertTrue(os.path.exists(wfDir))
        self.assertIn("TEST MODE skip remove", self.__log.getvalue())

    # ------------------------------------------------------------------
    # getLogFiles / getLogFileList / getMiscFileList
    # ------------------------------------------------------------------
    def testGetLogFiles(self) -> None:
        aLog = self.__touch(self.__path("archive", DATASET_ID, "a.log"))
        self.__touch(self.__path("archive", DATASET_ID, "a.txt"))
        dLog = self.__touch(self.__path("deposit", DATASET_ID, "d.log"))
        dm = self.__dm()
        self.assertEqual(dm.getLogFiles(DATASET_ID), [aLog])
        self.assertEqual(dm.getLogFiles(DATASET_ID, fileSource="deposit"), [dLog])
        self.assertEqual(dm.getLogFiles(DATASET_ID, fileSource="session"), [])

    def testGetLogFileList(self) -> None:
        a1 = self.__touch(self.__path("archive", DATASET_ID, "run.log"))
        a2 = self.__touch(self.__path("archive", DATASET_ID, "log", "anything.txt"))
        d1 = self.__touch(self.__path("deposit", DATASET_ID, "dep.log"))
        dm = self.__dm()
        for src in cast("List[PathInfoStorageType]", ["archive", "wf-archive"]):
            rL = dm.getLogFileList(DATASET_ID, fileSource=src)
            self.assertEqual(sorted(r[0] for r in rL), sorted([a1, a2]))
            for _fp, tS, sZ in rL:
                self.assertRegex(tS, TIMESTAMP_RE)
                self.assertAlmostEqual(sZ, 0.001)
        rL = dm.getLogFileList(DATASET_ID, fileSource="deposit")
        self.assertEqual([r[0] for r in rL], [d1])
        self.assertEqual(dm.getLogFileList(DATASET_ID, fileSource="session"), [])

    def testGetMiscFileListSorting(self) -> None:
        old = self.__touch(self.__path("misc", "old.txt"))
        new = self.__touch(self.__path("misc", "new.txt"), content="y" * 2000)
        os.utime(old, (1000000000, 1000000000))
        os.utime(new, (2000000000, 2000000000))
        os.makedirs(self.__path("misc", "subdir"))
        dm = self.__dm()
        pat = self.__path("misc", "*")

        rL = dm.getMiscFileList([pat])
        self.assertEqual([r[0] for r in rL], [new, old])
        self.assertAlmostEqual(rL[0][2], 2.0)

        rL = dm.getMiscFileList([pat, "", None], sortFlag=False)  # type: ignore[list-item]
        self.assertEqual(sorted(r[0] for r in rL), sorted([new, old]))

    def testGetMiscFileListDefaultPattern(self) -> None:
        self.__touch(self.__path("cwd", "a.txt"))
        cwd = os.getcwd()
        os.chdir(self.__path("cwd"))
        try:
            rL = self.__dm().getMiscFileList()
        finally:
            os.chdir(cwd)
        self.assertEqual([r[0] for r in rL], ["a.txt"])

    def testGetMiscFileListFailure(self) -> None:
        self.__touch(self.__path("misc", "a.txt"))
        pat = self.__path("misc", "*")
        with patch("wwpdb.io.file.DataMaintenance.os.path.getmtime", side_effect=OSError("gone")):
            self.assertEqual(self.__dm().getMiscFileList([pat]), [])
            self.assertEqual(self.__log.getvalue(), "")
            self.assertEqual(self.__dm(verbose=True).getMiscFileList([pat]), [])
        self.assertIn("failing for patter", self.__log.getvalue())
        self.assertIn("OSError", self.__log.getvalue())

    # ------------------------------------------------------------------
    # getVersionFileList
    # ------------------------------------------------------------------
    def testGetVersionFileList(self) -> None:
        self.__modelFiles([1, 3, 2, 10])
        # Files whose last extension is not a version are ignored
        self.__touch(self.__path("archive", DATASET_ID, "%s_model_P1.pdb.Vbad.txt" % DATASET_ID))
        dm = self.__dm()
        vL = dm.getVersionFileList(DATASET_ID, wfInstanceId="W_1", contentType="model", formatType="pdbx", partitionNumber="1", mileStone=None)
        self.assertEqual([v for _f, v in vL], [10, 3, 2, 1])
        for f, v in vL:
            self.assertTrue(f.endswith(".V%d" % v))
        _args, kw = self.__pI.getFilePathVersionTemplate.call_args
        self.assertEqual(kw["wfInstanceId"], "W_1")
        self.assertEqual(kw["partNumber"], "1")

    def testGetVersionFileListTrailingSuffix(self) -> None:
        # A version id with a non-digit trailing character has it stripped
        base = self.__path("archive", DATASET_ID, "%s_model_P1.pdb" % DATASET_ID)
        self.__touch(base + ".V4a")
        self.__touch(base + ".V2")
        vL = self.__dm().getVersionFileList(DATASET_ID)
        self.assertEqual(vL, [(base + ".V4a", 4), (base + ".V2", 2)])

    def testGetVersionFileListNone(self) -> None:
        self.assertEqual(self.__dm().getVersionFileList(DATASET_ID), [])

    def testGetVersionFileListBadVersion(self) -> None:
        # ".Vx" cannot be converted to an integer - the internal error is
        # caught and an empty list returned
        base = self.__path("archive", DATASET_ID, "%s_model_P1.pdb" % DATASET_ID)
        self.__touch(base + ".V1")
        self.__touch(base + ".Vx")
        self.assertEqual(self.__dm().getVersionFileList(DATASET_ID), [])
        self.assertEqual(self.__log.getvalue(), "")
        self.assertEqual(self.__dm(verbose=True).getVersionFileList(DATASET_ID), [])
        self.assertIn("failing for pattern", self.__log.getvalue())

    def testGetVersionFileListTemplateFailure(self) -> None:
        self.__pI.getFilePathVersionTemplate.side_effect = ValueError("no template")
        self.assertEqual(self.__dm().getVersionFileList(DATASET_ID), [])
        self.assertEqual(self.__log.getvalue(), "")
        self.assertEqual(self.__dm(verbose=True).getVersionFileList(DATASET_ID, wfInstanceId="W_1"), [])
        out = self.__log.getvalue()
        self.assertIn("getVersionFileList() failing for data set %s instance W_1" % DATASET_ID, out)
        self.assertIn("no template", out)
        self.assertIn("Traceback", out)

    # ------------------------------------------------------------------
    # getContentTypeFileList
    # ------------------------------------------------------------------
    def testGetContentTypeFileList(self) -> None:
        self.__modelFiles([1, 2])
        base = self.__path("archive", DATASET_ID, "%s_sf_P1.cif" % DATASET_ID)
        self.__touch(base + ".V5")
        dm = self.__dm()

        vL = dm.getContentTypeFileList(DATASET_ID, None)
        self.assertEqual([v for _f, v in vL], [2, 1])
        self.__pI.getFilePathContentTypeTemplate.assert_called_once_with(dataSetId=DATASET_ID, wfInstanceId=None, contentType="model", fileSource="archive")

        vL = dm.getContentTypeFileList(DATASET_ID, "W_1", contentTypeList=["model", "sf"])
        self.assertEqual([v for _f, v in vL], [5, 2, 1])

    def testGetContentTypeFileListFailure(self) -> None:
        self.__pI.getFilePathContentTypeTemplate.side_effect = ValueError("no template")
        self.assertEqual(self.__dm().getContentTypeFileList(DATASET_ID, None), [])
        self.assertEqual(self.__log.getvalue(), "")
        self.assertEqual(self.__dm(verbose=True).getContentTypeFileList(DATASET_ID, None), [])
        self.assertIn("no template", self.__log.getvalue())

    # ------------------------------------------------------------------
    # getPurgeCandidates
    # ------------------------------------------------------------------
    def __candidates(self, versions: List[int], purgeType: str = "exp") -> Tuple[Optional[str], List[str], List[str]]:
        shutil.rmtree(self.__path("archive"), ignore_errors=True)
        self.__modelFiles(versions)
        latest, rmL, gzL = self.__dm().getPurgeCandidates(DATASET_ID, purgeType=purgeType)
        base = os.path.basename
        return (base(latest) if latest else None, [base(f) for f in rmL], [base(f) for f in gzL])

    def testGetPurgeCandidatesExp(self) -> None:
        fn = "%s_model_P1.pdb.V%%d" % DATASET_ID
        self.assertEqual(self.__candidates([]), (None, [], []))
        self.assertEqual(self.__candidates([1]), (fn % 1, [], []))
        self.assertEqual(self.__candidates([1, 2]), (fn % 2, [], [fn % 1]))
        self.assertEqual(self.__candidates([1, 2, 3]), (fn % 3, [], [fn % 2, fn % 1]))
        self.assertEqual(self.__candidates([1, 2, 3, 4, 5]), (fn % 5, [fn % 4, fn % 3], [fn % 2, fn % 1]))

    def testGetPurgeCandidatesOther(self) -> None:
        fn = "%s_model_P1.pdb.V%%d" % DATASET_ID
        for purgeType in ["other", "report"]:
            self.assertEqual(self.__candidates([1], purgeType), (fn % 1, [], []))
            self.assertEqual(self.__candidates([1, 2], purgeType), (fn % 2, [], [fn % 1]))
            self.assertEqual(self.__candidates([1, 2, 3, 4], purgeType), (fn % 4, [fn % 3, fn % 2], [fn % 1]))

    def testGetPurgeCandidatesUnknownType(self) -> None:
        fn = "%s_model_P1.pdb.V%%d" % DATASET_ID
        self.assertEqual(self.__candidates([1, 2, 3], "unknown"), (fn % 3, [], []))

    def testGetPurgeCandidatesPassesArguments(self) -> None:
        dm = self.__dm()
        with patch.object(dm, "getVersionFileList", return_value=[]) as mGet:
            dm.getPurgeCandidates(DATASET_ID, wfInstanceId="W_1", fileSource="deposit", contentType="sf", formatType="pdbx", partitionNumber="2", mileStone="upload")
        mGet.assert_called_once_with(DATASET_ID, wfInstanceId="W_1", fileSource="deposit", contentType="sf", formatType="pdbx", partitionNumber="2", mileStone="upload")

    # ------------------------------------------------------------------
    # getVersionFileListSnapshot
    # ------------------------------------------------------------------
    def __snapshotSetup(self, fileSource: str) -> Tuple[str, List[str]]:
        snapBase = self.__path("snapshot")
        snapFiles: List[str] = []
        for v in [1, 2, 3]:
            snapFiles.append(self.__touch(os.path.join(snapBase, fileSource, DATASET_ID, "%s_model_P1.pdb.V%d" % (DATASET_ID, v))))
        return snapBase, snapFiles

    def testGetVersionFileListSnapshot(self) -> None:
        for fileSource in cast("List[PathInfoStorageType]", ["archive", "deposit"]):
            snapBase, snapFiles = self.__snapshotSetup(fileSource)
            # V2 already present at the destination and is skipped
            self.__modelFiles([2], fileSource=fileSource)
            dstDir = self.__path(fileSource, DATASET_ID)
            pL = self.__dm().getVersionFileListSnapshot(snapBase, DATASET_ID, fileSource=fileSource)
            self.assertEqual(
                pL,
                [
                    (snapFiles[2], os.path.join(dstDir, os.path.basename(snapFiles[2]))),
                    (snapFiles[0], os.path.join(dstDir, os.path.basename(snapFiles[0]))),
                ],
            )

    def testGetVersionFileListSnapshotOtherSource(self) -> None:
        # For other sources both source and destination are the current
        # directory; nothing matches there.
        tmpCwd = self.__path("cwd")
        os.makedirs(tmpCwd)
        cwd = os.getcwd()
        os.chdir(tmpCwd)
        try:
            pL = self.__dm().getVersionFileListSnapshot(self.__path("snapshot"), DATASET_ID, fileSource="session")
        finally:
            os.chdir(cwd)
        self.assertEqual(pL, [])

    def testGetVersionFileListSnapshotFailure(self) -> None:
        self.__pI.getFilePathVersionTemplate.side_effect = ValueError("no template")
        snapBase = self.__path("snapshot")
        self.assertEqual(self.__dm().getVersionFileListSnapshot(snapBase, DATASET_ID), [])
        self.assertEqual(self.__log.getvalue(), "")
        self.assertEqual(self.__dm(verbose=True).getVersionFileListSnapshot(snapBase, DATASET_ID), [])
        self.assertIn("no template", self.__log.getvalue())
        self.assertIn("Traceback", self.__log.getvalue())

    def testGetVersionFileListSnapshotAccessCheck(self) -> None:
        snapBase, _snapFiles = self.__snapshotSetup("archive")
        with patch("wwpdb.io.file.DataMaintenance.os.access", return_value=True) as mAccess:
            pL = self.__dm().getVersionFileListSnapshot(snapBase, DATASET_ID)
        self.assertEqual(pL, [])
        self.assertEqual(mAccess.call_count, 3)
        for c in mAccess.call_args_list:
            self.assertEqual(c[0][1], os.F_OK)


def suiteDataMaintenance() -> unittest.TestSuite:
    return unittest.TestLoader().loadTestsFromTestCase(DataMaintenanceTests)


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suiteDataMaintenance())
