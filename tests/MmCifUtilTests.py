##
# File:    MmCifUtilTests.py
# Date:    16-Aug-2019
#
# Updates:
#   29-Sep-2026  Expanded coverage - synthetic multi-block files, value
#                filtering, update/insert/remove, write round trip, dict views
##
"""
Tests for wwpdb.io.file.mmCIFUtil

Tests interact with mmCIFUtil only through its public methods and observe
behavior through return values, the filesystem, or the supplied log handle.
"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"

import io
import os
import platform
import shutil
import tempfile
import unittest
from typing import Any, Dict, List
from unittest.mock import patch

from wwpdb.io.file.mmCIFUtil import mmCIFUtil  # noqa: E402

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(HERE)
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Two data blocks. In the first block, the "pets" category has a row whose
# values are all missing ("?" / ".") so that it should be dropped, and a row
# with a single missing value that should be omitted from that row's dict.
MULTIBLOCK_CIF = """data_FIRST
#
_entry.id FIRST
#
loop_
_pets.id
_pets.name
_pets.kind
1 Rex   dog
2 Tom   .
3 ?     ?
4 Polly parrot
#
data_SECOND
#
_entry.id SECOND
#
_other.value 42
#
"""


class MmCifUtilTests(unittest.TestCase):  # pylint: disable=too-many-public-methods
    def setUp(self) -> None:
        self._fpathin = os.path.join(mockTopPath, "MODELS", "4pdr.cif")
        self._tmpdir = tempfile.mkdtemp()
        self._multipath = os.path.join(self._tmpdir, "multi.cif")
        with open(self._multipath, "w") as fout:
            fout.write(MULTIBLOCK_CIF)

    def tearDown(self) -> None:
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Original smoke test against the mock data tree
    # ------------------------------------------------------------------
    def testRead(self) -> None:
        cifObj = mmCIFUtil(filePath=self._fpathin)
        self.assertIsNotNone(cifObj, "mmCIF returned None")

        table = cifObj.GetValue("entity")
        self.assertIsNotNone(table, "category not found")

        val = cifObj.GetSingleValue("pdbx_database_status", "status_code")
        self.assertEqual(val, "REL", "Status code not correct")

        val2 = cifObj.GetBlockID()
        self.assertEqual(val2, "4PDR", "Datablock name not correct")

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

    # ------------------------------------------------------------------
    # Construction / reading
    # ------------------------------------------------------------------
    def testNoFilePath(self) -> None:
        """No file path - nothing is read and nothing is logged"""
        log = io.StringIO()
        cifObj = mmCIFUtil(verbose=True, log=log)
        self.assertIsNone(cifObj.GetBlockID())
        self.assertEqual(([], []), cifObj.GetValueAndItem("entry"))
        self.assertEqual([], cifObj.GetValue("entry"))
        self.assertEqual("", cifObj.GetSingleValue("entry", "id"))
        self.assertEqual("", log.getvalue())

    def testEmptyFile(self) -> None:
        """An empty file parses to no containers"""
        fpath = os.path.join(self._tmpdir, "empty.cif")
        with open(fpath, "w"):
            pass
        log = io.StringIO()
        cifObj = mmCIFUtil(log=log, filePath=fpath)
        self.assertIsNone(cifObj.GetBlockID())
        self.assertEqual("", log.getvalue())

    def testMissingFileLogged(self) -> None:
        """Read failure is reported to the supplied log handle"""
        log = io.StringIO()
        fpath = os.path.join(self._tmpdir, "doesnotexist.cif")
        cifObj = mmCIFUtil(log=log, filePath=fpath)
        self.assertIsNone(cifObj.GetBlockID())
        msg = log.getvalue()
        self.assertIn("Read %s failed" % fpath, msg)

    def testReaderExceptionLogged(self) -> None:
        """An exception raised by the parser is caught and logged"""
        log = io.StringIO()
        with patch("wwpdb.io.file.mmCIFUtil.PdbxReader") as mockReader:
            mockReader.return_value.read.side_effect = ValueError("boom")
            cifObj = mmCIFUtil(log=log, filePath=self._multipath)
        self.assertIsNone(cifObj.GetBlockID())
        self.assertIn("boom", log.getvalue())
        self.assertIn(self._multipath, log.getvalue())

    def testMultipleBlocks(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        # First block is the default
        self.assertEqual("FIRST", cifObj.GetBlockID())
        self.assertEqual("FIRST", cifObj.GetSingleValue("entry", "id"))

        # Second block accessible by name
        dList, iList = cifObj.GetValueAndItemByBlock("SECOND", "entry")
        self.assertEqual(["id"], iList)
        self.assertEqual([{"id": "SECOND"}], dList)

        dList, iList = cifObj.GetValueAndItemByBlock("SECOND", "other")
        self.assertEqual([{"value": "42"}], dList)

        # Category only in second block is not found in default block
        self.assertEqual([], cifObj.GetValue("other"))

    # ------------------------------------------------------------------
    # Value retrieval
    # ------------------------------------------------------------------
    def testMissingValuesFiltered(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        dList, iList = cifObj.GetValueAndItem("pets")
        self.assertEqual(["id", "name", "kind"], iList)
        expected: List[Dict[str, str]] = [
            {"id": "1", "name": "Rex", "kind": "dog"},
            {"id": "2", "name": "Tom"},
            {"id": "3"},
            {"id": "4", "name": "Polly", "kind": "parrot"},
        ]
        self.assertEqual(expected, dList)
        self.assertEqual(expected, cifObj.GetValue("pets"))

    def testAllMissingRowDropped(self) -> None:
        """Rows in which every value is '?' or '.' are omitted"""
        fpath = os.path.join(self._tmpdir, "missing.cif")
        with open(fpath, "w") as fout:
            fout.write("data_M\nloop_\n_c.a\n_c.b\n? .\nx y\n")
        cifObj = mmCIFUtil(filePath=fpath)
        dList, iList = cifObj.GetValueAndItem("c")
        self.assertEqual(["a", "b"], iList)
        self.assertEqual([{"a": "x", "b": "y"}], dList)

    def testGetSingleValue(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        # First row only
        self.assertEqual("Rex", cifObj.GetSingleValue("pets", "name"))
        # Unknown item
        self.assertEqual("", cifObj.GetSingleValue("pets", "noitem"))
        # Unknown category
        self.assertEqual("", cifObj.GetSingleValue("nocat", "name"))

    def testGetCategoriesAndAttributes(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        self.assertEqual(["entry", "pets"], cifObj.GetCategories())
        self.assertEqual(["id", "name", "kind"], cifObj.GetAttributes("pets"))

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------
    def testUpdateSingleRowValue(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        cifObj.UpdateSingleRowValue("pets", "name", 1, "Jerry")
        dList = cifObj.GetValue("pets")
        self.assertEqual("Rex", dList[0]["name"])
        self.assertEqual("Jerry", dList[1]["name"])
        # Unknown category is silently ignored
        cifObj.UpdateSingleRowValue("nocat", "name", 0, "X")
        self.assertEqual(["entry", "pets"], cifObj.GetCategories())

    def testUpdateMultipleRowsValue(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        cifObj.UpdateMultipleRowsValue("pets", "kind", "cat")
        dList = cifObj.GetValue("pets")
        self.assertEqual(4, len(dList))
        for row in dList:
            self.assertEqual("cat", row["kind"])
        # Unknown category is silently ignored
        cifObj.UpdateMultipleRowsValue("nocat", "kind", "cat")
        self.assertEqual(["entry", "pets"], cifObj.GetCategories())

    # ------------------------------------------------------------------
    # Construction of new content
    # ------------------------------------------------------------------
    def testBuildFromScratch(self) -> None:
        cifObj = mmCIFUtil()
        cifObj.AddBlock("NEW")
        self.assertEqual("NEW", cifObj.GetBlockID())
        self.assertEqual([], cifObj.GetCategories())

        cifObj.AddCategory("thing", ["id", "label"])
        self.assertEqual(["thing"], cifObj.GetCategories())
        self.assertEqual(["id", "label"], cifObj.GetAttributes("thing"))
        # A category without rows is falsy - so no item names are reported
        self.assertEqual(([], []), cifObj.GetValueAndItem("thing"))

        cifObj.InsertData("thing", [["1", "a"], ["2", "b"]])
        self.assertEqual([{"id": "1", "label": "a"}, {"id": "2", "label": "b"}], cifObj.GetValue("thing"))

        # Unknown category - no change
        cifObj.InsertData("nocat", [["3", "c"]])
        self.assertEqual(["thing"], cifObj.GetCategories())
        self.assertEqual(2, len(cifObj.GetValue("thing")))

    def testAddBlockToExisting(self) -> None:
        """A new block becomes current; existing blocks stay addressable"""
        cifObj = mmCIFUtil(filePath=self._multipath)
        cifObj.AddBlock("THIRD")
        self.assertEqual("THIRD", cifObj.GetBlockID())
        self.assertEqual([], cifObj.GetCategories())
        self.assertEqual([{"id": "FIRST"}], cifObj.GetValueAndItemByBlock("FIRST", "entry")[0])
        self.assertEqual([{"id": "SECOND"}], cifObj.GetValueAndItemByBlock("SECOND", "entry")[0])

    def testRemoveCategory(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        self.assertTrue(cifObj.RemoveCategory("pets"))
        self.assertEqual(["entry"], cifObj.GetCategories())
        self.assertEqual([], cifObj.GetValue("pets"))
        self.assertFalse(cifObj.RemoveCategory("pets"))

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    def testWriteCifNoPath(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        before = sorted(os.listdir(self._tmpdir))
        cifObj.WriteCif()
        cifObj.WriteCif("")
        self.assertEqual(before, sorted(os.listdir(self._tmpdir)))

    def testWriteCifRoundTrip(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        cifObj.UpdateSingleRowValue("pets", "name", 0, "Fido")
        cifObj.AddBlock("THIRD")
        cifObj.AddCategory("extra", ["a", "b"])
        cifObj.InsertData("extra", [["x", "y"]])
        outpath = os.path.join(self._tmpdir, "out.cif")
        cifObj.WriteCif(outpath)
        self.assertTrue(os.path.exists(outpath))

        newObj = mmCIFUtil(filePath=outpath)
        self.assertEqual("FIRST", newObj.GetBlockID())
        self.assertEqual("Fido", newObj.GetSingleValue("pets", "name"))
        self.assertEqual(cifObj.GetValueAndItemByBlock("FIRST", "pets"), newObj.GetValueAndItem("pets"))
        self.assertEqual([{"value": "42"}], newObj.GetValueAndItemByBlock("SECOND", "other")[0])
        self.assertEqual([{"a": "x", "b": "y"}], newObj.GetValueAndItemByBlock("THIRD", "extra")[0])

    # ------------------------------------------------------------------
    # Dictionary views
    # ------------------------------------------------------------------
    def testCategoryAsDict(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        expected: Dict[str, Any] = {
            "pets": {
                "Items": ["id", "name", "kind"],
                "Values": [
                    ["1", "Rex", "dog"],
                    ["2", "Tom", None],
                    ["3", None, None],
                    ["4", "Polly", "parrot"],
                ],
            }
        }
        self.assertEqual(expected, cifObj.category_as_dict("pets"))
        self.assertEqual(expected, cifObj.category_as_dict("pets", block="FIRST"))

        # Explicit other block
        self.assertEqual({"other": {"Items": ["value"], "Values": [["42"]]}}, cifObj.category_as_dict("other", block="SECOND"))

        # Unknown category / block
        empty: Dict[str, Any] = {"nocat": {"Items": [], "Values": []}}
        self.assertEqual(empty, cifObj.category_as_dict("nocat"))
        self.assertEqual({"pets": {"Items": [], "Values": []}}, cifObj.category_as_dict("pets", block="NOBLOCK"))

    def testBlockAsDict(self) -> None:
        cifObj = mmCIFUtil(filePath=self._multipath)
        data = cifObj.block_as_dict()
        self.assertEqual(["entry", "pets"], sorted(data.keys()))
        self.assertEqual({"Items": ["id"], "Values": [["FIRST"]]}, data["entry"])
        self.assertEqual(cifObj.category_as_dict("pets")["pets"], data["pets"])
        self.assertEqual(data, cifObj.block_as_dict(block="FIRST"))

    def testBlockAsDictOtherBlock(self) -> None:
        """Categories are taken from the current container, values from the named block"""
        cifObj = mmCIFUtil(filePath=self._multipath)
        data = cifObj.block_as_dict(block="SECOND")
        self.assertEqual({"Items": ["id"], "Values": [["SECOND"]]}, data["entry"])
        # "pets" does not exist in SECOND
        self.assertEqual({"Items": [], "Values": []}, data["pets"])


def mmcifStandardTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(MmCifUtilTests("testRead"))
    return suiteSelect


def mmcifFullTests() -> unittest.TestSuite:  # pragma: no cover
    return unittest.TestLoader().loadTestsFromTestCase(MmCifUtilTests)


if __name__ == "__main__":  # pragma: no cover
    mySuite = mmcifFullTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
