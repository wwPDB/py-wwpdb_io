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

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)  # pragma: no cover
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup  # noqa: E402

SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.io.locator.DataReference import ReferenceFileComponents, ReferenceFileInfo  # noqa: E402


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


def suiteComponentAccessorsTests():  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ReferenceFileComponentsTests("testAccessors"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    if True:
        mySuite = suiteComponentAccessorsTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
