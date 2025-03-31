##
# File:    PathInfoTests.py
# Date:    26-Feb-2013
#
# Updates:
#   27-Aug-2013  jdw verify after milestone addition to api.
#   28-Jun-2014  jdw add template examples
#   23-Oct-2017  jdw update logging
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

import time
import unittest
import os
import platform
import logging

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)  # pragma: no cover
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup  # noqa: E402

SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.utils.config.ConfigInfo import getSiteId  # noqa: E402
from wwpdb.io.locator.PathInfo import PathInfo  # noqa: E402


FORMAT = "[%(levelname)s]-%(module)s.%(funcName)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger()


class PathInfoTests(unittest.TestCase):
    def setUp(self):
        #
        self.__verbose = True
        self.__siteId = getSiteId(defaultSiteId=None)

        self.__startTime = time.time()
        logger.debug("Starting %s at %s" % (self.id(), time.strftime("%Y %m %d %H:%M:%S", time.localtime())))

    def tearDown(self):
        endTime = time.time()
        logger.debug("Completed %s at %s (%.4f seconds)\n" % (self.id(), time.strftime("%Y %m %d %H:%M:%S", time.localtime()), endTime - self.__startTime))

    def testGetStandardPaths(self):
        """Test getting standard file names within session paths."""
        ok = True
        # fileSource, id, partionId, versionId
        tests = [
            ("archive", "D_1000000000", None, 1, "latest"),
            ("archive", "D_1000000000", None, "latest", "latest"),
            ("archive", "D_1000000000", None, "next", "latest"),
            ("archive", "D_1000000000", None, "previous", "latest"),
            ("deposit", "D_1000000000", None, 1, "latest"),
            ("deposit-ui", "D_1000000000", None, 1, "latest"),
        ]
        eId = "1"
        for fs, dataSetId, wfInst, pId, vId in tests:
            logger.debug("File source %s dataSetId %s  partno  %s wfInst %s version %s" % (fs, dataSetId, pId, wfInst, vId))

            pI = PathInfo(siteId=self.__siteId)
            pI.setDebugFlag(False)
            #
            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Model path (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find model file - default")

            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, mileStone="deposit")
            logger.debug("Model path (deposit) (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find model file - deposit")

            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, mileStone="upload")
            logger.debug("Model path (upload) (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find model file - upload")

            fp = pI.getModelPdbFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Model path (PDB):    %s" % fp)
            self.assertIsNotNone(fp, "Failed to find PDB model file")

            fp = pI.getStructureFactorsPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("SF path (pdbx):    %s" % fp)
            self.assertIsNotNone(fp, "Failed to find SF file")

            fp = pI.getPolyLinkFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Link dist  (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find PDBx model file")

            fp = pI.getPolyLinkReportFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Link Report dist  (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find link report file")

            fp = pI.getSequenceStatsFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Sequence stats (PIC):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find sequence stats file")

            fp = pI.getSequenceAlignFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Sequence align (PIC):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find sequence align file")

            fp = pI.getReferenceSequenceFilePath(dataSetId, entityId=eId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Reference match entity %s (PDBx):   %s" % (eId, fp))
            self.assertIsNotNone(fp, "Failed to find reference sequence file")

            fp = pI.getSequenceAssignmentFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Sequence assignment (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find sequence assignment")

            fp = pI.getAssemblyAssignmentFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Assembly assignment (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find assembly assignment")

            fp = pI.getBlastMatchFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Blast match (xml):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find blast match file")

            fp = pI.getFilePath(dataSetId, wfInstanceId=wfInst, contentType="seqdb-match", formatType="pdbx", fileSource=fs, versionId=vId, partNumber=pId, mileStone=None)
            logger.debug("Sequence match (getFilePath) (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find seq-db match")
            #
            fp = pI.getFilePathContentTypeTemplate(dataSetId, wfInstanceId=wfInst, contentType="model", fileSource=fs)
            logger.debug("Model template:   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find model template")

            fp = pI.getArchivePath(dataSetId)
            logger.debug("getArchivePath (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find dir path")

            fp = pI.getDepositPath(dataSetId)
            logger.debug("getDepositPath (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find deposit path")

            fp = pI.getInstancePath(dataSetId, wfInstanceId="W_099")
            logger.debug("getWfInstancePath (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find wf instance path")

            fp = pI.getInstanceTopPath(
                dataSetId,
            )
            logger.debug("getWfInstanceTopPath (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find wf Top instance path")

            fp = pI.getTempDepPath(dataSetId)
            logger.debug("getTempDepPath):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find TempDep path")
            #
            fp = pI.getDirPath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, partNumber=pId, mileStone=None)
            logger.debug("Sequence match (getDirPath) (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find dir path")

            ft = pI.getFilePathVersionTemplate(dataSetId, wfInstanceId=wfInst, contentType="em-volume", formatType="map", fileSource="archive", partNumber=pId, mileStone=None)
            logger.debug("EM volume version template:   %r" % ft)
            ft = pI.getFilePathPartitionTemplate(dataSetId, wfInstanceId=wfInst, contentType="em-mask-volume", formatType="map", fileSource="archive", mileStone=None)
            logger.debug("EM mask partition template:   %r" % ft)
            self.assertIsNotNone(ft, "Failed to mask model file")

        self.assertEqual(ok, True)

    def testSessionPath(self):
        tests = [("archive", "D_1000000000", "session_test/12345")]
        for fs, dataSetId, session_dir in tests:
            logger.debug("File source %s dataSetId %s  session dir %s" % (fs, dataSetId, session_dir))

            fileSource = ("session", "wf-session", "session-download", "uploads", "pickles")
            for fs in fileSource:
                pI = PathInfo(siteId=self.__siteId, sessionPath=session_dir)
                fp = pI.getDirPath(dataSetId=dataSetId, fileSource=fs)
                logger.debug("%s path %s" % (fs, fp))
                self.assertIsNotNone(fp, "Failed to get session path")

            # fp = pI.getWebDownloadPath(dataSetId=dataSetId)
            # self.assertIsNotNone(fp, "Failed to get session path")
            #

    def testFileNames(self):
        """Tests parsing and validity functions"""
        tests = [("D_000001_model_P1.cif.V1", True), ("D_000001_model_P1.cif", False), ("D_000001_P1.cif.V1", False), ("D_000001_model.cif.V1", False), ("D_000001.cif", False)]
        # Matches w/o version number
        tests2 = [("D_000001_model_P1.cif.V1", True), ("D_000001_model_P1.cif", True), ("D_000001_P1.cif.V1", False), ("D_000001_model.cif.V1", False), ("D_000001.cif", False)]

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


def suiteStandardPathTests():  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PathInfoTests("testGetStandardPaths"))
    suiteSelect.addTest(PathInfoTests("testSessionPath"))
    suiteSelect.addTest(PathInfoTests("testFileNames"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    if True:
        mySuite = suiteStandardPathTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
