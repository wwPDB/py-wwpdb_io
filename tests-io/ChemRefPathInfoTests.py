##
# File:    MmCifUtilTests.py
# Date:    16-Aug-2019
#
# Updates:
##
"""
Simple tests for wwpdb.io.locator.ChemRefPathInfo.py
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"

import os
import platform
import unittest

from wwpdb.io.locator.ChemRefPathInfo import ChemRefPathInfo  # noqa: E402

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(HERE)
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")


class ChemRefPathInfoTests(unittest.TestCase):
    def setUp(self):
        self.crpi = ChemRefPathInfo()

    def testCCDHash(self):
        """Test return of CCD hash"""
        self.assertEqual(self.crpi.getCcdHash("ABC"), "A")
        self.assertEqual(self.crpi.getCcdHash("abc"), "A")
        # For now
        self.assertEqual(self.crpi.getCcdHash("AAPTR"), "TR")
        self.assertEqual(self.crpi.getCcdHash("DT"), "D")
        self.assertEqual(self.crpi.getCcdHash(None), None)
        self.assertEqual(self.crpi.getCcdHash("aapt"), "PT")

    def testGetIdType(self):
        """Test identifier based on idCode"""
        self.assertEqual(self.crpi.getIdType("A"), "CC")
        self.assertEqual(self.crpi.getIdType("ABC"), "CC")
        self.assertEqual(self.crpi.getIdType("AAPTR"), "CC")

        self.assertEqual(self.crpi.getIdType("PRDCC_1234"), "PRDCC")
        self.assertEqual(self.crpi.getIdType("PRD_1234"), "PRD")
        self.assertEqual(self.crpi.getIdType("FAM_1234"), "PRD_FAMILY")


def chemRefStandardTests():  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ChemRefPathInfoTests("testCCDHash"))
    suiteSelect.addTest(ChemRefPathInfoTests("testGetIdType"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    mySuite = chemRefStandardTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
