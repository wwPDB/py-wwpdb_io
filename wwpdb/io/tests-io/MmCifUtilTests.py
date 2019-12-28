##
# File:    MmCifUtilTests.py
# Date:    16-Aug-2019
#
# Updates:
##
"""
Simple tests for wwpdb.io.file.mmCIFUtil
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"

import unittest
import os
import platform

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup  # noqa: E402,F401

from wwpdb.io.file.mmCIFUtil import mmCIFUtil  # noqa: E402


class MmCifUtilTests(unittest.TestCase):
    def setUp(self):
        self._fpathin = os.path.join(mockTopPath, "MODELS", "4pdr.cif")

    def testRead(self):
        cifObj = mmCIFUtil(filePath=self._fpathin)
        self.assertIsNotNone(cifObj, "mmCIF returned None")

        table = cifObj.GetValue("entity")
        self.assertIsNotNone(table, "category not found")

        val = cifObj.GetSingleValue("pdbx_database_status", "status_code")
        self.assertEqual(val, "REL", "Status code not correct")


def mmcifStandardTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(MmCifUtilTests("testRead"))
    return suiteSelect


if __name__ == "__main__":
    if True:
        mySuite = mmcifStandardTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
