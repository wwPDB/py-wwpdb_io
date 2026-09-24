# pylint: disable=protected-access
##
# File:    ReferenceFileComponentsTests.py
# Date:    18-Sep-2013
##
"""
Test cases for data reference class accessors

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"


import os
import os.path
import platform
import sys
import tempfile
import traceback
import unittest
from typing import Any, Optional, TextIO, cast
from unittest.mock import MagicMock, patch

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(HERE)
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)  # pragma: no cover
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup  # noqa: E402

SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.utils.config.ConfigInfo import ConfigInfo  # noqa: E402

from wwpdb.io.locator.DataReference import DataFileReference, DataReferenceBase, DataReferenceStorageType, ReferenceFileComponents, ReferenceFileInfo  # noqa: E402


class MyConfigInfo(ConfigInfo):
    def __init__(self, siteId: Optional[str] = None, verbose: bool = True, log: TextIO = sys.stderr) -> None:
        super(MyConfigInfo, self).__init__(siteId=siteId, verbose=verbose, log=log)

    def get(self, keyWord: str, default: Any = None) -> Any:
        if keyWord == "SITE_ARCHIVE_UI_STORAGE_PATH":
            val = os.path.join(TESTOUTPUT, "ui-path")
        else:
            val = super(MyConfigInfo, self).get(keyWord, default)
        return val


class DataReferenceBaseTests(unittest.TestCase):
    def testReferenceType(self) -> None:
        """Test the reference type accessor on the base class"""
        base = DataReferenceBase()
        self.assertIsNone(base.getReferenceType())
        base.setReferenceType("file")
        self.assertEqual(base.getReferenceType(), "file")
        base.setReferenceType("directory")
        self.assertEqual(base.getReferenceType(), "directory")


class ReferenceFileInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__rfi = ReferenceFileInfo(verbose=True, log=sys.stderr)

    def testContentTypeExists(self) -> None:
        """Test lookup of known and unknown content types"""
        self.assertTrue(self.__rfi.contentTypeExists("model"))
        self.assertFalse(self.__rfi.contentTypeExists("bogus-content-type"))

    def testGetContentType(self) -> None:
        """Test recovery of content type from a content type acronym"""
        self.assertEqual(self.__rfi.getContentType("sf"), "structure-factors")
        self.assertIsNone(self.__rfi.getContentType("bogus-acronym"))

    def testGetFormatTypes(self) -> None:
        """Test recovery of the supported format list for a content type"""
        self.assertEqual(self.__rfi.getFormatTypes("model"), ["pdbx", "pdb", "pdbml", "cifeps"])
        self.assertEqual(self.__rfi.getFormatTypes("bogus-content-type"), [])

    def testGetContentTypeAcronym(self) -> None:
        """Test recovery of the acronym for a content type"""
        self.assertEqual(self.__rfi.getContentTypeAcronym("model"), "model")
        self.assertIsNone(self.__rfi.getContentTypeAcronym("bogus-content-type"))

    def testGetExtensionFormats(self) -> None:
        """Test recovery of formats associated with a file extension"""
        self.assertIn("pdbx", self.__rfi.getExtensionFormats("cif"))
        self.assertEqual(self.__rfi.getExtensionFormats("bogus-extension"), [])


class ReferenceFileComponentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__verbose = True
        self.__lfh = sys.stderr
        #
        self.__fileNameList = ["D_111111_sf_P1.cif.V3", "D_111111_sf_P1.mtz.V3", "D_111111_model_P1.pdb.V3", "D_111111_model_P1.pdb.V3"]

    def tearDown(self) -> None:
        pass

    def testInvalidFileName(self) -> None:
        """Test that an unparseable file name leaves all accessors at their default None"""
        rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
        self.assertFalse(rfc.set("garbage"))
        self.assertEqual(rfc.get(), (None, None, None, None, None))
        self.assertIsNone(rfc.getVersionId())
        self.assertIsNone(rfc.getDepositionDataSetId())
        self.assertIsNone(rfc.getPartitionNumber())
        self.assertIsNone(rfc.getContentTypeAcronym())
        self.assertIsNone(rfc.getContentType())
        self.assertIsNone(rfc.getContentFormat())

    def testAccessors(self) -> None:
        """Test file component accessors"""
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)  # noqa: SLF001
        self.__lfh.write(" -------------------------\n")

        valid = {
            "D_111111_sf_P1.cif.V3": ["D_111111", "structure-factors", "pdbx", 1, 3],
            "D_111111_sf_P1.mtz.V3": ["D_111111", "structure-factors", "mtz", 1, 3],
            "D_111111_model_P1.pdb.V3": ["D_111111", "model", "pdb", 1, 3],
        }
        try:
            rfi = ReferenceFileInfo(verbose=self.__verbose, log=self.__lfh)
            rfi.dump(ofh=self.__lfh)
            for fileName in self.__fileNameList:
                rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
                rfc.set(fileName)
                idCode, contentType, contentFormat, partNo, versionNo = rfc.get()
                self.__lfh.write(
                    "RFC- fileName %s idcode %s contentType %s contentFormat %s partNo %d versionId %s\n" % (fileName, idCode, contentType, contentFormat, partNo, versionNo)
                )
                self.assertEqual(valid[fileName], [idCode, contentType, contentFormat, partNo, versionNo])
        except:  # noqa: E722  # pragma: no cover  # pylint: disable=bare-except
            traceback.print_exc(file=self.__lfh)
            self.fail()


class DataFileReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__verbose = True
        self.__lfh = sys.stderr
        #

    def __getdfr(self, loc: DataReferenceStorageType = "deposit") -> DataFileReference:
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        dfr.setContentTypeAndFormat("model", "pdbx")
        dfr.setStorageType(loc)
        dfr.setVersionId("1")
        dfr.setDepositionDataSetId("D_12345")
        return dfr

    def testDepositUIDefault(self) -> None:
        """Test equivalence of deposit-ui and deposit under normal circumstances"""
        dfr = self.__getdfr()
        pth = dfr.getDirPathReference()
        dfr = self.__getdfr("deposit-ui")
        pth2 = dfr.getDirPathReference()
        self.assertEqual(pth, pth2)

    def testUploadsUIDefault(self) -> None:
        """Test uploads should not have /deposit-ui/ in path"""
        dfr = self.__getdfr("uploads")
        pth = cast(str, dfr.getDirPathReference())
        self.assertNotIn("/deposit-ui/", pth)
        self.assertIn("/deposition_uploads/", pth)

    def testTempDepUIDefault(self) -> None:
        """Test tempdep should not have /deposit-ui/ in path"""
        dfr = self.__getdfr("tempdep")
        pth = cast(str, dfr.getDirPathReference())
        self.assertNotIn("/ui-path/tempdep/", pth)

    @patch("wwpdb.io.locator.DataReference.ConfigInfo", side_effect=MyConfigInfo)
    def testTempDepUISep(self, mock1: MagicMock) -> None:
        """Test tempdep should not have /deposit-ui/ in path"""
        dfr = self.__getdfr("tempdep")
        pth = dfr.getDirPathReference()
        self.assertIn("/ui-path/tempdep/", pth)
        self.assertTrue(mock1.called, "Patch did not work")

    @patch("wwpdb.io.locator.DataReference.ConfigInfo", side_effect=MyConfigInfo)
    def testDepositUISep(self, mock1: MagicMock) -> None:
        """Test deposit-ui and deposit should be different"""
        dfr = self.__getdfr()
        pth = dfr.getDirPathReference()

        self.assertTrue(mock1.called, "Patch did not work")

        dfr = self.__getdfr("deposit-ui")
        pth2 = dfr.getDirPathReference()
        self.assertNotEqual(pth, pth2)

    @patch("wwpdb.io.locator.DataReference.ConfigInfo", side_effect=MyConfigInfo)
    def testUploadsUISep(self, mock1: MagicMock) -> None:
        """Test uploads should have /deposit-ui/ in path"""
        dfr = self.__getdfr("uploads")
        pth = dfr.getDirPathReference()
        self.assertIn("/deposit-ui/", pth)
        self.assertTrue(mock1.called, "Patch did not work")

    def testUploadsPicklesDefault(self) -> None:
        """Test pickles should not have /deposit-ui/ in path"""
        dfr = self.__getdfr("pickles")
        pth = dfr.getDirPathReference()
        self.assertNotIn("/deposit-ui/", pth)
        self.assertIn("/deposition-v-200/", pth)

    def testGetSitePrefix(self) -> None:
        """Test recovery of the configured site prefix"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertEqual(dfr.getSitePrefix(), "WWPDB_DEPLOY_TEST")

    def testGetStorageTypeList(self) -> None:
        """Test the list of supported storage types"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        storageTypes = dfr.getStorageTypeList()
        self.assertIn("archive", storageTypes)
        self.assertIn("deposit", storageTypes)
        self.assertIn("session", storageTypes)

    def testSetStorageTypeInvalid(self) -> None:
        """Test that an unrecognized storage type is rejected"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertFalse(dfr.setStorageType("bogus-storage-type"))  # type: ignore[arg-type]
        self.assertIsNone(dfr.getStorageType())

    def testSetContentTypeAndFormatInvalid(self) -> None:
        """Test that an unrecognized content type or format is rejected"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertFalse(dfr.setContentTypeAndFormat("bogus-content-type", "pdbx"))
        self.assertFalse(dfr.setContentTypeAndFormat("model", "bogus-format"))

    def testSetVersionId(self) -> None:
        """Test setting of symbolic and numeric version identifiers"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertTrue(dfr.setVersionId("latest"))
        self.assertEqual(dfr.getVersionId(), "latest")
        self.assertTrue(dfr.setVersionId("3"))
        self.assertEqual(dfr.getVersionId(), "3")
        self.assertFalse(dfr.setVersionId("bogus-version"))

    def testSetDepositionDataSetId(self) -> None:
        """Test setting of a properly formed deposition data set identifier"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertTrue(dfr.setDepositionDataSetId("D_12345"))
        self.assertEqual(dfr.getDepositionDataSetId(), "D_12345")
        self.assertFalse(dfr.setDepositionDataSetId("D_abc"))
        self.assertFalse(dfr.setDepositionDataSetId("Dabc"))

    def testSetWorkflowInstanceId(self) -> None:
        """Test setting of a properly formed workflow instance identifier"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertTrue(dfr.setWorkflowInstanceId("W_1"))
        self.assertEqual(dfr.getWorkflowInstanceId(), "W_1")
        self.assertFalse(dfr.setWorkflowInstanceId("X_1"))

    def testSetWorkflowNameSpace(self) -> None:
        """Test setting of an alphanumeric workflow name space identifier"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertTrue(dfr.setWorkflowNameSpace("abc123"))
        self.assertEqual(dfr.getWorkflowNameSpace(), "abc123")
        self.assertFalse(dfr.setWorkflowNameSpace("abc-123"))
        self.assertFalse(dfr.setWorkflowNameSpace(None))
        self.assertFalse(dfr.setWorkflowNameSpace(""))

    def testSetSessionDataSetId(self) -> None:
        """Test setting of the session data set identifier"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertTrue(dfr.setSessionDataSetId("1abc"))
        self.assertFalse(dfr.setSessionDataSetId(""))
        self.assertFalse(dfr.setSessionDataSetId(None))

    def testSetPartitionNumber(self) -> None:
        """Test setting of symbolic and numeric partition numbers"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertTrue(dfr.setPartitionNumber("latest"))
        self.assertEqual(dfr.getPartitionNumber(), "latest")
        self.assertTrue(dfr.setPartitionNumber(3))
        self.assertEqual(dfr.getPartitionNumber(), 3)
        self.assertFalse(dfr.setPartitionNumber("bogus-partition"))

    def testAccessorsAfterSetup(self) -> None:
        """Test the getters for a fully configured internal file reference"""
        dfr = self.__getdfr()
        self.assertEqual(dfr.getContentType(), "model")
        self.assertEqual(dfr.getFileFormat(), "pdbx")
        self.assertEqual(dfr.getStorageType(), "deposit")
        self.assertEqual(dfr.getVersionId(), "1")
        self.assertEqual(dfr.getDepositionDataSetId(), "D_12345")

    def testIsReferenceValidIncomplete(self) -> None:
        """Test that a partially configured file reference is not valid"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        self.assertFalse(dfr.isReferenceValid())
        dfr.setContentTypeAndFormat("model", "pdbx")
        self.assertFalse(dfr.isReferenceValid())
        dfr.setStorageType("archive")
        self.assertFalse(dfr.isReferenceValid())
        dfr.setVersionId("1")
        # storage type "archive" also requires a deposition data set id
        self.assertFalse(dfr.isReferenceValid())
        dfr.setDepositionDataSetId("D_12345")
        self.assertTrue(dfr.isReferenceValid())

    def testIsReferenceValidDirectory(self) -> None:
        """Test validity of a directory reference for archive and workflow instance storage"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        dfr.setStorageType("archive")
        # setReferenceType() must follow setStorageType() since the latter always resets the type to "file"
        dfr.setReferenceType("directory")
        self.assertFalse(dfr.isReferenceValid())
        dfr.setDepositionDataSetId("D_12345")
        self.assertTrue(dfr.isReferenceValid())

        dfr2 = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        dfr2.setStorageType("wf-instance")
        dfr2.setReferenceType("directory")
        dfr2.setDepositionDataSetId("D_12345")
        self.assertFalse(dfr2.isReferenceValid())
        dfr2.setWorkflowInstanceId("W_1")
        self.assertTrue(dfr2.isReferenceValid())

    def testExternalFilePath(self) -> None:
        """Test that an external file reference bypasses internal naming conventions"""
        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.close()
        try:
            dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
            self.assertTrue(dfr.setExternalFilePath(tf.name))
            self.assertTrue(dfr.isReferenceValid())
            # getDirPathReference() returns the full external file path unchanged, not its containing directory
            self.assertEqual(dfr.getDirPathReference(), tf.name)
            self.assertEqual(dfr.getFilePathReference(), tf.name)
            self.assertEqual(dfr.getFileVersionNumber(), 0)
        finally:
            os.remove(tf.name)

        self.assertFalse(DataFileReference().setExternalFilePath(""))
        self.assertFalse(DataFileReference().setExternalFilePath(None))
        self.assertFalse(DataFileReference().setExternalFilePath(tf.name, fileFormat="bogus-format"))

    def testGetFilePathExists(self) -> None:
        """Test the file existence check used for resolved file references"""
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.close()
        try:
            self.assertTrue(dfr.getFilePathExists(tf.name))
        finally:
            os.remove(tf.name)
        self.assertFalse(dfr.getFilePathExists(tf.name))
        self.assertFalse(dfr.getFilePathExists("/no/such/path/for/testing"))

    def testVersioningAndSearchTargets(self) -> None:
        """Test version resolution and glob search target generation against real files on disk"""
        sessDir = os.path.join(TESTOUTPUT, "dfr_version_test")
        if not os.path.exists(sessDir):  # pragma: no cover
            os.makedirs(sessDir)
        for fn in os.listdir(sessDir):
            os.remove(os.path.join(sessDir, fn))

        def makeRef(versionId: str) -> DataFileReference:
            dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
            dfr.setContentTypeAndFormat("model", "pdbx")
            dfr.setStorageType("session")
            dfr.setSessionPath(sessDir)
            dfr.setSessionDataSetId("1abc")
            dfr.setPartitionNumber(1)
            dfr.setVersionId(versionId)
            return dfr

        baseName = "1ABC_model_P1.cif"

        # No files on disk yet - "latest" and "next" both start at V1
        latestRef = makeRef("latest")
        latestPath = latestRef.getFilePathReference()
        self.assertEqual(latestPath, os.path.join(sessDir, baseName + ".V1"))
        self.assertEqual(makeRef("next").getFilePathReference(), os.path.join(sessDir, baseName + ".V1"))
        assert latestPath is not None
        with open(latestPath, "w") as ofh:
            ofh.write("V1")

        # One version exists - "latest" resolves to it, "next" advances, "previous" has none
        self.assertEqual(makeRef("latest").getFilePathReference(), os.path.join(sessDir, baseName + ".V1"))
        self.assertEqual(makeRef("next").getFilePathReference(), os.path.join(sessDir, baseName + ".V2"))
        self.assertIsNone(makeRef("previous").getFilePathReference())
        self.assertEqual(makeRef("original").getFilePathReference(), os.path.join(sessDir, baseName + ".V1"))
        self.assertEqual(makeRef("none").getFilePathReference(), os.path.join(sessDir, baseName))
        self.assertEqual(makeRef("2").getFilePathReference(), os.path.join(sessDir, baseName + ".V2"))
        self.assertEqual(makeRef("2").getFileVersionNumber(), 2)

        searchRef = makeRef("1")
        self.assertEqual(searchRef.getVersionIdSearchTarget(), baseName + ".V*")
        self.assertEqual(searchRef.getPartitionNumberSearchTarget(), "1ABC_model_P*.cif*")
        self.assertEqual(searchRef.getContentTypeSearchTarget(), "1ABC_model_P*")


def suiteComponentAccessorsTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataReferenceBaseTests("testReferenceType"))
    suiteSelect.addTest(ReferenceFileInfoTests("testContentTypeExists"))
    suiteSelect.addTest(ReferenceFileInfoTests("testGetContentType"))
    suiteSelect.addTest(ReferenceFileInfoTests("testGetFormatTypes"))
    suiteSelect.addTest(ReferenceFileInfoTests("testGetContentTypeAcronym"))
    suiteSelect.addTest(ReferenceFileInfoTests("testGetExtensionFormats"))
    suiteSelect.addTest(ReferenceFileComponentsTests("testInvalidFileName"))
    suiteSelect.addTest(ReferenceFileComponentsTests("testAccessors"))
    return suiteSelect


def suiteDataFileReferenceTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataFileReferenceTests("testDepositUIDefault"))
    suiteSelect.addTest(DataFileReferenceTests("testDepositUISep"))
    suiteSelect.addTest(DataFileReferenceTests("testUploadsUIDefault"))
    suiteSelect.addTest(DataFileReferenceTests("testUploadsUISep"))
    suiteSelect.addTest(DataFileReferenceTests("testTempDepUIDefault"))
    suiteSelect.addTest(DataFileReferenceTests("testTempDepUISep"))
    suiteSelect.addTest(DataFileReferenceTests("testUploadsPicklesDefault"))
    suiteSelect.addTest(DataFileReferenceTests("testGetSitePrefix"))
    suiteSelect.addTest(DataFileReferenceTests("testGetStorageTypeList"))
    suiteSelect.addTest(DataFileReferenceTests("testSetStorageTypeInvalid"))
    suiteSelect.addTest(DataFileReferenceTests("testSetContentTypeAndFormatInvalid"))
    suiteSelect.addTest(DataFileReferenceTests("testSetVersionId"))
    suiteSelect.addTest(DataFileReferenceTests("testSetDepositionDataSetId"))
    suiteSelect.addTest(DataFileReferenceTests("testSetWorkflowInstanceId"))
    suiteSelect.addTest(DataFileReferenceTests("testSetWorkflowNameSpace"))
    suiteSelect.addTest(DataFileReferenceTests("testSetSessionDataSetId"))
    suiteSelect.addTest(DataFileReferenceTests("testSetPartitionNumber"))
    suiteSelect.addTest(DataFileReferenceTests("testAccessorsAfterSetup"))
    suiteSelect.addTest(DataFileReferenceTests("testIsReferenceValidIncomplete"))
    suiteSelect.addTest(DataFileReferenceTests("testIsReferenceValidDirectory"))
    suiteSelect.addTest(DataFileReferenceTests("testExternalFilePath"))
    suiteSelect.addTest(DataFileReferenceTests("testGetFilePathExists"))
    suiteSelect.addTest(DataFileReferenceTests("testVersioningAndSearchTargets"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    if True:  # pylint: disable=using-constant-test
        mySuite = suiteComponentAccessorsTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        unittest.TextTestRunner(verbosity=2).run(suiteDataFileReferenceTests())
