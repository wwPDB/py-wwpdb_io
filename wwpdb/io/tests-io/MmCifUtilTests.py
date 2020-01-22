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
from wwpdb.io.file.mmCIFUtil import mmCIFUtil  # noqa: E402
import platform

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")


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

        val = cifObj.GetBlockID()
        self.assertEqual(val, "4PDR", "Datablock name not correct")

        # This should return failure as block does not exist
        self.assertEqual(([], []), cifObj.GetValueAndItemByBlock("noblock", "pdbx_database_status"))

        # This should return failure as category does not exist
        self.assertEqual(([], []), cifObj.GetValueAndItemByBlock("4PDR", "unknowncat"))

        # This should return successful data
        self.assertNotEqual(([], []), cifObj.GetValueAndItem("pdbx_database_status"))

        # Update tests - no diagostics returned
        cifObj.UpdateSingleRowValue("unknowncat", "status_code", 0, "HPUB")
        cifObj.UpdateSingleRowValue("pdbx_database_status", "status_code", 0, "HPUB")
        cifObj.UpdateMultipleRowsValue("unknowncat", "status_code", "HPUB")
        cifObj.UpdateMultipleRowsValue("pdbx_database_status", "status_code", "HPUB")

        cifObj.AddBlock("second")
        cifObj.AddCategory("cat", ["first", "second"])
        cifObj.InsertData("unknowncat", [["1", "2"]])
        cifObj.InsertData("cat", [["1", "2"]])
        self.assertEqual(["cat"], cifObj.GetCategories())
        self.assertEqual(["first", "second"], cifObj.GetAttributes("cat"))
        self.assertIsNotNone(cifObj.category_as_dict("cat"))
        self.assertIsNotNone(cifObj.block_as_dict())

        # Does nothing
        cifObj.WriteCif()

        testout = os.path.join(TESTOUTPUT, "cifout.cif")
        cifObj.WriteCif(testout)

        # Raises exception internally - outputs error
        cifObj = mmCIFUtil(filePath="nonexistantfile")


def mmcifStandardTests():  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(MmCifUtilTests("testRead"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    mySuite = mmcifStandardTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
