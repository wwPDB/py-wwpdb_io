# pylint: disable=logging-not-lazy
##
# File:    PathInfoTests.py
# Date:    26-Feb-2013
#
# Updates:
#   27-Aug-2013  jdw verify after milestone addition to api.
#   28-Jun-2014  jdw add template examples
#   23-Oct-2017  jdw update logging
#   24-Sep-2026  ep  add tests for convenience methods, file sources, templates and error paths
##
"""
Skeleton examples for creating standard file names for sequence resources and data files.

 **** A file source must be created to support these examples  ****

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import logging
import os
import platform
import time
import unittest
from typing import List, Optional, Tuple
from unittest import mock

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(HERE)
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)  # pragma: no cover
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup  # noqa: E402

SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.utils.config.ConfigInfo import getSiteId  # noqa: E402

from wwpdb.io.locator.PathInfo import PathInfo, PathInfoPartitionId, PathInfoStorageType, PathInfoVersionId  # noqa: E402

FORMAT = "[%(levelname)s]-%(module)s.%(funcName)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger()


class PathInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        #
        # self.__verbose = True
        self.__siteId = getSiteId(defaultSiteId=None)

        self.__startTime = time.time()
        logger.debug("Starting %s at %s", self.id(), time.strftime("%Y %m %d %H:%M:%S", time.localtime()))

    def tearDown(self) -> None:
        endTime = time.time()
        logger.debug("Completed %s at %s (%.4f seconds)\n", self.id(), time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - self.__startTime)

    def testGetStandardPaths(self) -> None:
        """Test getting standard file names within session paths."""
        ok = True
        # fileSource, id, partionId, versionId
        tests: List[Tuple[PathInfoStorageType, str, Optional[str], PathInfoPartitionId, PathInfoVersionId]] = [
            ("archive", "D_1000000000", None, 1, "latest"),
            ("archive", "D_1000000000", None, "latest", "latest"),
            ("archive", "D_1000000000", None, "next", "latest"),
            ("archive", "D_1000000000", None, "previous", "latest"),
            ("deposit", "D_1000000000", None, 1, "latest"),
            ("deposit-ui", "D_1000000000", None, 1, "latest"),
        ]
        eId = "1"
        for fs, dataSetId, wfInst, pId, vId in tests:
            logger.debug("File source %s dataSetId %s  partno  %s wfInst %s version %s", fs, dataSetId, pId, wfInst, vId)

            pI = PathInfo(siteId=self.__siteId)
            pI.setDebugFlag(False)
            #
            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Model path (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find model file - default")

            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, mileStone="deposit")
            logger.debug("Model path (deposit) (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find model file - deposit")

            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, mileStone="upload")
            logger.debug("Model path (upload) (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find model file - upload")

            fp = pI.getModelPdbFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Model path (PDB):    %s", fp)
            self.assertIsNotNone(fp, "Failed to find PDB model file")

            fp = pI.getStructureFactorsPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("SF path (pdbx):    %s", fp)
            self.assertIsNotNone(fp, "Failed to find SF file")

            fp = pI.getPolyLinkFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Link dist  (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find PDBx model file")

            fp = pI.getPolyLinkReportFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Link Report dist  (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find link report file")

            fp = pI.getSequenceStatsFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Sequence stats (PIC):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find sequence stats file")

            fp = pI.getSequenceAlignFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Sequence align (PIC):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find sequence align file")

            fp = pI.getReferenceSequenceFilePath(dataSetId, entityId=eId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Reference match entity %s (PDBx):   %s", eId, fp)
            self.assertIsNotNone(fp, "Failed to find reference sequence file")

            fp = pI.getSequenceAssignmentFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Sequence assignment (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find sequence assignment")

            fp = pI.getAssemblyAssignmentFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Assembly assignment (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find assembly assignment")

            fp = pI.getBlastMatchFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Blast match (xml):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find blast match file")

            fp = pI.getFilePath(dataSetId, wfInstanceId=wfInst, contentType="seqdb-match", formatType="pdbx", fileSource=fs, versionId=vId, partNumber=pId, mileStone=None)
            logger.debug("Sequence match (getFilePath) (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find seq-db match")
            #
            fp = pI.getFilePathContentTypeTemplate(dataSetId, wfInstanceId=wfInst, contentType="model", fileSource=fs)
            logger.debug("Model template:   %s", fp)
            self.assertIsNotNone(fp, "Failed to find model template")

            fp = pI.getArchivePath(dataSetId)
            logger.debug("getArchivePath (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find dir path")

            fp = pI.getDepositPath(dataSetId)
            logger.debug("getDepositPath (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find deposit path")

            fp = pI.getInstancePath(dataSetId, wfInstanceId="W_099")
            logger.debug("getWfInstancePath (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find wf instance path")

            fp = pI.getInstanceTopPath(
                dataSetId,
            )
            logger.debug("getWfInstanceTopPath (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find wf Top instance path")

            fp = pI.getTempDepPath(dataSetId)
            logger.debug("getTempDepPath):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find TempDep path")
            #
            fp = pI.getDirPath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, partNumber=pId, mileStone=None)
            logger.debug("Sequence match (getDirPath) (PDBx):   %s", fp)
            self.assertIsNotNone(fp, "Failed to find dir path")

            ft = pI.getFilePathVersionTemplate(dataSetId, wfInstanceId=wfInst, contentType="em-volume", formatType="map", fileSource="archive", partNumber=pId, mileStone=None)
            logger.debug("EM volume version template:   %r", ft)
            ft = pI.getFilePathPartitionTemplate(dataSetId, wfInstanceId=wfInst, contentType="em-mask-volume", formatType="map", fileSource="archive", mileStone=None)
            logger.debug("EM mask partition template:   %r", ft)
            self.assertIsNotNone(ft, "Failed to mask model file")

        self.assertEqual(ok, True)

    def testSessionPath(self) -> None:
        tests = [("archive", "D_1000000000", "session_test/12345")]
        for fs, dataSetId, session_dir in tests:
            logger.debug("File source %s dataSetId %s  session dir %s", fs, dataSetId, session_dir)

            fileSource: Tuple[PathInfoStorageType, ...] = ("session", "wf-session", "session-download", "uploads", "pickles")
            for fsi in fileSource:
                pI = PathInfo(siteId=self.__siteId, sessionPath=session_dir)
                fp = pI.getDirPath(dataSetId=dataSetId, fileSource=fsi)
                logger.debug("%s path %s", fsi, fp)
                self.assertIsNotNone(fp, "Failed to get session path")

            # fp = pI.getWebDownloadPath(dataSetId=dataSetId)
            # self.assertIsNotNone(fp, "Failed to get session path")
            #

    def testFileNames(self) -> None:
        """Tests parsing and validity functions"""
        tests = [
            ("D_000001_model_P1.cif.V1", True),
            ("D_000001_model_P1.cif", False),
            ("D_000001_P1.cif.V1", False),
            ("D_000001_model.cif.V1", False),
            ("D_000001.cif", False),
        ]
        # Matches w/o version number
        tests2 = [
            ("D_000001_model_P1.cif.V1", True),
            ("D_000001_model_P1.cif", True),
            ("D_000001_P1.cif.V1", False),
            ("D_000001_model.cif.V1", False),
            ("D_000001.cif", False),
        ]

        for t in tests:
            pI = PathInfo(siteId=self.__siteId)
            ret = pI.isValidFileName(t[0])
            self.assertEqual(ret, t[1], "Parsing mismatch %s" % t[0])

        # Withot version
        for t in tests2:
            pI = PathInfo(siteId=self.__siteId)
            ret = pI.isValidFileName(t[0], False)
            self.assertEqual(ret, t[1], "Parsing mismatch %s" % t[0])

        pI = PathInfo(siteId=self.__siteId)
        self.assertEqual(pI.parseFileName("D_000001_model_P1.cif.V1"), ("D_000001", "model", "pdbx", 1, 1))

        self.assertEqual(pI.parseFileName("D_000001_model.cif.V1"), (None, None, None, None, None))

        # spiltFileName will give partials
        self.assertEqual(pI.splitFileName("D_000001_model_P1.cif.V1"), ("D_000001", "model", "pdbx", 1, 1))

        self.assertEqual(pI.splitFileName("D_000001_model.cif.V1"), ("D_000001", "model", None, None, 1))

        self.assertEqual(pI.getFileExtension("gif"), "gif", "Getting file extension")
        self.assertEqual(pI.getFileExtension("pdbx"), "cif", "Getting file extension")
        self.assertEqual(pI.getFileExtension("unk"), None, "Getting file extension")


class PathInfoDetailTests(unittest.TestCase):
    """Detailed checks of path construction and error handling in PathInfo"""

    def setUp(self) -> None:
        self.__siteId = getSiteId(defaultSiteId=None)
        self.__dataSetId = "D_1000000000"
        self.__sessionPath = os.path.join(TESTOUTPUT, "sessions", "abc123")
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath)
        self.__dataTop = os.path.join(mockTopPath, "da_top", "data")

    def __archiveDir(self, storage: str = "archive") -> str:
        return os.path.join(self.__dataTop, storage, self.__dataSetId)

    def testConstructorDefaults(self) -> None:
        """siteId is looked up when not provided"""
        with mock.patch("wwpdb.io.locator.PathInfo.getSiteId", return_value=self.__siteId) as mockGetSiteId:
            pI = PathInfo()
            mockGetSiteId.assert_called_once()
        self.assertEqual(pI.getArchivePath(self.__dataSetId), self.__archiveDir())

        # Explicit site id - no lookup
        with mock.patch("wwpdb.io.locator.PathInfo.getSiteId") as mockGetSiteId:
            pI = PathInfo(siteId=self.__siteId, verbose=True)
            mockGetSiteId.assert_not_called()
        pI.setDebugFlag(True)
        pI.setDebugFlag(False)

    def testFileSources(self) -> None:
        """Model file path for each supported file source"""
        fN = "%s_model_P1.cif.V1" % self.__dataSetId
        tests: List[Tuple[PathInfoStorageType, Optional[str]]] = [
            ("archive", os.path.join(self.__archiveDir(), fN)),
            ("wf-archive", os.path.join(self.__archiveDir(), fN)),
            ("autogroup", os.path.join(self.__archiveDir("autogroup"), fN)),
            ("deposit", os.path.join(self.__archiveDir("deposit"), fN)),
            ("deposit-ui", os.path.join(self.__archiveDir("deposit"), fN)),
            ("tempdep", os.path.join(self.__archiveDir("tempdep"), fN)),
            ("wf-instance", os.path.join(self.__dataTop, "workflow", self.__dataSetId, "instance", "W_001", fN)),
            ("session", os.path.join(self.__sessionPath, fN)),
            ("wf-session", os.path.join(self.__sessionPath, fN)),
            ("session-download", os.path.join(self.__sessionPath, "downloads", fN)),
            ("unknown-source", None),  # type: ignore[list-item]
        ]
        for fs, expected in tests:
            fp = self.__pI.getModelPdbxFilePath(self.__dataSetId, wfInstanceId="W_001", fileSource=fs, versionId=1)
            self.assertEqual(fp, expected, "Mismatch for file source %s" % fs)

    def testConvenienceMethods(self) -> None:
        """Content type, format and partition used by each convenience method"""
        pI = self.__pI
        dId = self.__dataSetId
        aDir = self.__archiveDir()
        dDir = self.__archiveDir("deposit")
        tests: List[Tuple[Optional[str], str, str]] = [
            (pI.getModelPdbxFilePath(dId, versionId=1), aDir, "model_P1.cif.V1"),
            (pI.getModelPdbxFilePath(dId, versionId=1, mileStone="deposit"), aDir, "model-deposit_P1.cif.V1"),
            (pI.getModelPdbFilePath(dId, versionId=1), aDir, "model_P1.pdb.V1"),
            (pI.getStructureFactorsPdbxFilePath(dId, versionId=1), aDir, "sf_P1.cif.V1"),
            (pI.getPolyLinkFilePath(dId, versionId=1), aDir, "poly-link-dist_P1.cif.V1"),
            (pI.getPolyLinkReportFilePath(dId, versionId=1), aDir, "poly-link-report_P1.html.V1"),
            (pI.getSequenceStatsFilePath(dId, versionId=1), aDir, "seq-data-stats_P1.pic.V1"),
            (pI.getSequenceAlignFilePath(dId, entityId="2", versionId=1), aDir, "seq-align-data_P2.pic.V1"),
            (pI.getReferenceSequenceFilePath(dId, entityId="3", versionId=1), aDir, "seqdb-match_P3.cif.V1"),
            (pI.getSequenceAssignmentFilePath(dId, versionId=1), aDir, "seq-assign_P1.cif.V1"),
            (pI.getAssemblyAssignmentFilePath(dId, versionId=1), aDir, "assembly-assign_P1.cif.V1"),
            (pI.getBlastMatchFilePath(dId, entityId="2", versionId=1), aDir, "blast-match_P2.xml.V1"),
            (pI.getMap2fofcFilePath(dId, versionId=1), aDir, "map-2fofc_P1.map.V1"),
            (pI.getMapfofcFilePath(dId, versionId=1), aDir, "map-fofc_P1.map.V1"),
            (pI.getEmVolumeFilePath(dId, versionId=1), aDir, "em-volume_P1.map.V1"),
            (pI.getEmDepositVolumeParamsFilePath(dId, versionId=1), dDir, "deposit-volume-params_P1.pic.V1"),
            (pI.getAuthChemcialShiftsFilePath(dId, partNumber="2", versionId=1), aDir, "cs-auth_P2.str.V1"),
            (pI.getChemcialShiftsFilePath(dId, versionId=1), aDir, "cs_P1.str.V1"),
            (pI.getMolecularRestraintsFilePath(dId, versionId=1), aDir, "mr_P1.str.V1"),
            (pI.getNMRCombinedFilePath(dId, versionId=1), aDir, "nmr-data-str_P1.str.V1"),
            (pI.getNMRifFilePath(dId, versionId=1), dDir, "nmrif_P1.cif.V1"),
            (pI.getAssemblyModelFilePath(dId, versionId=1), dDir, "assembly-model_P1.cif.V1"),
            (pI.getAssemblySuggestedFilePath(dId, versionId=1), dDir, "assembly-suggested_P1.json.V1"),
            (pI.getStatusHistoryFilePath(dId, versionId=1), aDir, "status-history_P1.cif.V1"),
        ]
        for fp, dirPath, suffix in tests:
            self.assertEqual(fp, os.path.join(dirPath, "%s_%s" % (dId, suffix)))

        # Content types omit-map-2fofc, omit-map-fofc and em-mask are not defined in the site configuration
        self.assertIsNone(pI.getOmitMap2fofcFilePath(dId, versionId=1))
        self.assertIsNone(pI.getOmitMapfofcFilePath(dId, versionId=1))
        self.assertIsNone(pI.getEmMaskFilePath(dId, maskNumber="2", versionId=1))

    def testGenericMethods(self) -> None:
        """getFilePath, getFileName, getWebDownloadPath and the search templates"""
        pI = self.__pI
        dId = self.__dataSetId
        aDir = self.__archiveDir()

        self.assertEqual(pI.getFilePath(dId, contentType="model", formatType="pdbx", versionId=2, partNumber=3), os.path.join(aDir, "%s_model_P3.cif.V2" % dId))
        self.assertEqual(pI.getFileName(dId, contentType="model", formatType="pdbx", versionId=2, partNumber=3), "%s_model_P3.cif.V2" % dId)
        self.assertEqual(pI.getWebDownloadPath(dId, contentType="model", formatType="pdbx", versionId=1), "/sessions/abc123/downloads/%s_model_P1.cif.V1" % dId)

        self.assertEqual(pI.getFilePathVersionTemplate(dId, contentType="model", formatType="pdbx"), os.path.join(aDir, "%s_model_P1.cif.V*" % dId))
        self.assertEqual(pI.getFilePathPartitionTemplate(dId, contentType="model", formatType="pdbx"), os.path.join(aDir, "%s_model_P*.cif*" % dId))
        self.assertEqual(pI.getFilePathContentTypeTemplate(dId, contentType="model"), os.path.join(aDir, "%s_model_P*" % dId))

        # Unknown content type - no file path and no templates
        self.assertIsNone(pI.getFilePath(dId, contentType="not-a-content-type", formatType="pdbx", versionId=1))
        self.assertIsNone(pI.getFilePathVersionTemplate(dId, contentType="not-a-content-type", formatType="pdbx"))
        self.assertIsNone(pI.getFilePathPartitionTemplate(dId, contentType="not-a-content-type", formatType="pdbx"))
        self.assertIsNone(pI.getFilePathContentTypeTemplate(dId, contentType="not-a-content-type"))

        # Milestone without a content type raises internally and is trapped
        self.assertIsNone(pI.getFilePath(dId, contentType=None, formatType="pdbx", mileStone="deposit"))
        # Unknown file source
        self.assertIsNone(pI.getFilePathVersionTemplate(dId, contentType="model", formatType="pdbx", fileSource="unknown-source"))  # type: ignore[arg-type]

    def testDirectoryPaths(self) -> None:
        """Top level directory convenience methods"""
        pI = self.__pI
        dId = self.__dataSetId
        wfTop = os.path.join(self.__dataTop, "workflow", dId, "instance")

        self.assertEqual(pI.getArchivePath(dId), self.__archiveDir())
        self.assertEqual(pI.getArchivePath("G_1000001"), os.path.join(self.__dataTop, "autogroup", "G_1000001"))
        self.assertEqual(pI.getDepositPath(dId), self.__archiveDir("deposit"))
        self.assertEqual(pI.getDepositUIPath(dId), self.__archiveDir("deposit"))
        self.assertEqual(pI.getTempDepPath(dId), self.__archiveDir("tempdep"))
        self.assertEqual(pI.getInstancePath(dId, "W_002"), os.path.join(wfTop, "W_002"))
        self.assertEqual(pI.getInstanceTopPath(dId), wfTop)
        self.assertEqual(pI.getDirPath(dId, fileSource="wf-session"), self.__sessionPath)
        self.assertEqual(pI.getDirPath(dId, fileSource="session-download"), os.path.join(self.__sessionPath, "downloads"))

    @unittest.expectedFailure
    def testSessionDirPath(self) -> None:
        """getDirPath() for 'session' should not resolve to the downloads directory.

        PathInfo.getDirPath() tests fileSource in ("session-download") which is a substring
        test on a string, so 'session' also matches.  Remove expectedFailure once fixed.
        """
        self.assertEqual(self.__pI.getDirPath(self.__dataSetId, fileSource="session"), self.__sessionPath)

    def testSetSessionPath(self) -> None:
        """Changing the session path is reflected in session file paths"""
        newPath = os.path.join(TESTOUTPUT, "sessions", "xyz789")
        self.__pI.setSessionPath(newPath)
        fN = "%s_model_P1.cif.V1" % self.__dataSetId
        self.assertEqual(self.__pI.getModelPdbxFilePath(self.__dataSetId, fileSource="session", versionId=1), os.path.join(newPath, fN))
        self.assertEqual(self.__pI.getModelPdbxFilePath(self.__dataSetId, fileSource="session-download", versionId=1), os.path.join(newPath, "downloads", fN))
        self.assertEqual(self.__pI.getWebDownloadPath(self.__dataSetId, contentType="model", formatType="pdbx", versionId=1), "/sessions/xyz789/downloads/%s" % fN)

    def testNoSessionPath(self) -> None:
        """No session path - non-session sources are unaffected"""
        pI = PathInfo(siteId=self.__siteId, sessionPath=None)
        self.assertEqual(pI.getArchivePath(self.__dataSetId), self.__archiveDir())
        self.assertEqual(pI.getModelPdbxFilePath(self.__dataSetId, versionId=1), os.path.join(self.__archiveDir(), "%s_model_P1.cif.V1" % self.__dataSetId))

    def testDirPathErrors(self) -> None:
        """Directory methods return None when lookups fail"""
        pI = self.__pI
        self.assertIsNone(pI.getArchivePath(None))  # type: ignore[arg-type]
        with mock.patch.object(pI, "getDirPath", side_effect=ValueError("mock failure")):
            self.assertIsNone(pI.getArchivePath(self.__dataSetId))
            self.assertIsNone(pI.getInstancePath(self.__dataSetId, "W_001"))
            self.assertIsNone(pI.getInstanceTopPath(self.__dataSetId))
            self.assertIsNone(pI.getDepositPath(self.__dataSetId))
            self.assertIsNone(pI.getDepositUIPath(self.__dataSetId))
            self.assertIsNone(pI.getTempDepPath(self.__dataSetId))

    def testFileNameEdgeCases(self) -> None:
        """Invalid file names and parsing failures"""
        pI = self.__pI
        self.assertFalse(pI.isValidFileName("not_a_valid_name"))
        self.assertFalse(pI.isValidFileName("not_a_valid_name", requireVersion=False))
        self.assertEqual(pI.parseFileName("not_a_valid_name"), (None, None, None, None, None))
        self.assertEqual(pI.splitFileName("D_000001_model_P2.cif"), ("D_000001", "model", "pdbx", 2, None))

        with mock.patch("wwpdb.io.locator.PathInfo.ReferenceFileComponents", side_effect=ValueError("mock failure")):
            self.assertEqual(pI.splitFileName("D_000001_model_P1.cif.V1"), (None, None, None, None, None))

    def testFileExtensionMissingDictionary(self) -> None:
        """getFileExtension() returns None if the extension dictionary is unavailable"""
        with mock.patch("wwpdb.io.locator.PathInfo.ConfigInfo") as mockCI:
            mockCI.return_value.get.return_value = None
            pI = PathInfo(siteId=self.__siteId)
            self.assertIsNone(pI.getFileExtension("pdbx"))
            mockCI.return_value.get.assert_called_with("FILE_FORMAT_EXTENSION_DICTIONARY")

    def testPathWorkerErrors(self) -> None:
        """Failures in DataFileReference are trapped and return None"""
        pI = self.__pI
        dId = self.__dataSetId
        with mock.patch("wwpdb.io.locator.PathInfo.DataFileReference", side_effect=RuntimeError("mock failure")):
            self.assertIsNone(pI.getModelPdbxFilePath(dId, versionId=1))
            self.assertIsNone(pI.getFilePathVersionTemplate(dId, contentType="model", formatType="pdbx"))
            self.assertIsNone(pI.getFilePathContentTypeTemplate(dId, contentType="model"))

        # Invalid reference where the content type template cannot be built
        with mock.patch("wwpdb.io.locator.PathInfo.DataFileReference") as mockDfr:
            mockDfr.return_value.isReferenceValid.return_value = False
            mockDfr.return_value.getDirPathReference.return_value = "/some/dir"
            mockDfr.return_value.getContentTypeSearchTarget.side_effect = RuntimeError("mock failure")
            self.assertIsNone(pI.getFilePathContentTypeTemplate(dId, contentType="model"))

            # Invalid reference, but content type template is available
            mockDfr.return_value.getContentTypeSearchTarget.side_effect = None
            mockDfr.return_value.getContentTypeSearchTarget.return_value = "D_1_model_P*"
            self.assertEqual(pI.getFilePathContentTypeTemplate(dId, contentType="model"), os.path.join("/some/dir", "D_1_model_P*"))
            self.assertIsNone(pI.getModelPdbxFilePath(dId, versionId=1))


def suiteStandardPathTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PathInfoTests("testGetStandardPaths"))
    suiteSelect.addTest(PathInfoTests("testSessionPath"))
    suiteSelect.addTest(PathInfoTests("testFileNames"))
    suiteSelect.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(PathInfoDetailTests))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    if True:  # pylint: disable=using-constant-test
        mySuite = suiteStandardPathTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
