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


import sys
import unittest
import traceback
import os
import os.path
import platform
from unittest.mock import patch

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)  # pragma: no cover
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup  # noqa: E402

SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.utils.config.ConfigInfo import ConfigInfo  # noqa: E402
from wwpdb.io.locator.DataReference import ReferenceFileComponents, ReferenceFileInfo, DataFileReference  # noqa: E402


class MyConfigInfo(ConfigInfo):
    def __init__(self, siteId=None, verbose=True, log=sys.stderr):
        super(MyConfigInfo, self).__init__(siteId=siteId, verbose=verbose, log=log)

    def get(self, keyWord, default=None):
        if keyWord == "SITE_ARCHIVE_UI_STORAGE_PATH":
            val = os.path.join(TESTOUTPUT, "ui-path")
        else:
            val = super(MyConfigInfo, self).get(keyWord, default)
        return val


class ReferenceFileComponentsTests(unittest.TestCase):
    def setUp(self):
        self.__verbose = True
        self.__lfh = sys.stderr
        #
        self.__fileNameList = ["D_111111_sf_P1.cif.V3", "D_111111_sf_P1.mtz.V3", "D_111111_model_P1.pdb.V3", "D_111111_model_P1.pdb.V3"]

    def tearDown(self):
        pass

    def testAccessors(self):
        """Test file component accessors"""
        self.__lfh.write("\n------------------------ ")
        self.__lfh.write("Starting test function  %s" % sys._getframe().f_code.co_name)
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
        except:  # noqa: E722  # pragma: no cover
            traceback.print_exc(file=self.__lfh)
            self.fail()


class DataFileReferenceTests(unittest.TestCase):
    def setUp(self):
        self.__verbose = True
        self.__lfh = sys.stderr
        #

    def __getdfr(self, loc="deposit"):
        dfr = DataFileReference(verbose=self.__verbose, log=self.__lfh)
        dfr.setContentTypeAndFormat("model", "pdbx")
        dfr.setStorageType(loc)
        dfr.setVersionId("1")
        dfr.setDepositionDataSetId("D_12345")
        return dfr

    def testDepositUIDefault(self):
        """Test equivalence of deposit-ui and deposit under normal circumstances"""
        dfr = self.__getdfr()
        pth = dfr.getDirPathReference()
        dfr = self.__getdfr("deposit-ui")
        pth2 = dfr.getDirPathReference()
        self.assertEqual(pth, pth2)

    def testUploadsUIDefault(self):
        """Test uploads should not have /deposit-ui/ in path"""
        dfr = self.__getdfr("uploads")
        pth = dfr.getDirPathReference()
        self.assertNotIn("/deposit-ui/", pth)

    def testTempDepUIDefault(self):
        """Test tempdep should not have /deposit-ui/ in path"""
        dfr = self.__getdfr("tempdep")
        pth = dfr.getDirPathReference()
        self.assertNotIn("/ui-path/tempdep/", pth)

    @patch("wwpdb.io.locator.DataReference.ConfigInfo", side_effect=MyConfigInfo)
    def testTempDepUISep(self, mock1):
        """Test tempdep should not have /deposit-ui/ in path"""
        dfr = self.__getdfr("tempdep")
        pth = dfr.getDirPathReference()
        self.assertIn("/ui-path/tempdep/", pth)
        self.assertTrue(mock1.called, "Patch did not work")

    @patch("wwpdb.io.locator.DataReference.ConfigInfo", side_effect=MyConfigInfo)
    def testDepositUISep(self, mock1):
        """Test deposit-ui and deposit should be different"""
        dfr = self.__getdfr()
        pth = dfr.getDirPathReference()

        self.assertTrue(mock1.called, "Patch did not work")

        dfr = self.__getdfr("deposit-ui")
        pth2 = dfr.getDirPathReference()
        self.assertNotEqual(pth, pth2)

    @patch("wwpdb.io.locator.DataReference.ConfigInfo", side_effect=MyConfigInfo)
    def testUploadsUISep(self, mock1):
        """Test uploads should have /deposit-ui/ in path"""
        dfr = self.__getdfr("uploads")
        pth = dfr.getDirPathReference()
        self.assertIn("/deposit-ui/", pth)
        self.assertTrue(mock1.called, "Patch did not work")


def suiteComponentAccessorsTests():  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ReferenceFileComponentsTests("testAccessors"))
    return suiteSelect


def suiteDataFileReferenceTests():  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataFileReferenceTests("testDepositUIDefault"))
    suiteSelect.addTest(DataFileReferenceTests("testDepositUISep"))
    suiteSelect.addTest(DataFileReferenceTests("testUploadsUIDefault"))
    suiteSelect.addTest(DataFileReferenceTests("testUploadsUISep"))
    suiteSelect.addTest(DataFileReferenceTests("testTempDepUIDefault"))
    suiteSelect.addTest(DataFileReferenceTests("testTempDepUISep"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    if True:
        mySuite = suiteComponentAccessorsTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        unittest.TextTestRunner(verbosity=2).run(suiteDataFileReferenceTests())
