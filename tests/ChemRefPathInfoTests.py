##
# File:    ChemRefPathInfoTests.py
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
    def setUp(self) -> None:
        self.crpi = ChemRefPathInfo()
        self.crpiTest = ChemRefPathInfo(testMode=True)

    def testCCDHash(self) -> None:
        """Test return of CCD hash"""
        self.assertEqual(self.crpi.getCcdHash("ABC"), "A")
        self.assertEqual(self.crpi.getCcdHash("abc"), "A")
        # For now
        self.assertEqual(self.crpi.getCcdHash("AAPTR"), "TR")
        self.assertEqual(self.crpi.getCcdHash("DT"), "D")
        self.assertEqual(self.crpi.getCcdHash(None), None)
        self.assertEqual(self.crpi.getCcdHash("aapt"), "PT")
        self.assertEqual(self.crpi.getCcdHash(""), None)

    def testGetIdType(self) -> None:
        """Test identifier based on idCode"""
        self.assertEqual(self.crpi.getIdType("A"), "CC")
        self.assertEqual(self.crpi.getIdType("ABC"), "CC")
        self.assertEqual(self.crpi.getIdType("AAPTR"), "CC")

        self.assertEqual(self.crpi.getIdType("PRDCC_1234"), "PRDCC")
        self.assertEqual(self.crpi.getIdType("PRD_1234"), "PRD")
        self.assertEqual(self.crpi.getIdType("FAM_1234"), "PRD_FAMILY")

        # Longer id with no recognized prefix is unresolvable
        self.assertIsNone(self.crpi.getIdType("ABCDEF"))
        self.assertIsNone(self.crpi.getIdType(""))

    def testGetFilePath(self) -> None:
        """Test computation of repository file path from idCode - with and without explicit id_type"""
        self.assertEqual(self.crpi.getFilePath("ABC"), os.path.join("components", "ligand-dict-v3", "A", "ABC", "ABC.cif"))
        self.assertEqual(self.crpi.getFilePath("abc"), os.path.join("components", "ligand-dict-v3", "A", "ABC", "ABC.cif"))
        self.assertEqual(self.crpi.getFilePath("PRD_000001"), os.path.join("components", "prd-v3", "1", "PRD_000001.cif"))
        self.assertEqual(self.crpi.getFilePath("PRDCC_000001"), os.path.join("components", "prdcc-v3", "1", "PRDCC_000001.cif"))
        self.assertEqual(self.crpi.getFilePath("FAM_000001"), os.path.join("components", "family-v3", "1", "FAM_000001.cif"))

        # explicit id_type overrides inference
        self.assertEqual(self.crpi.getFilePath("ABC", id_type="CC"), self.crpi.getFilePath("ABC"))
        self.assertEqual(self.crpi.getFilePath("PRD_000001", id_type="PRD"), self.crpi.getFilePath("PRD_000001"))

        # unresolvable id type (long, unrecognized prefix)
        self.assertIsNone(self.crpi.getFilePath("ABCDEF"))
        self.assertIsNone(self.crpi.getFilePath(""))

    def testGetFileDir(self) -> None:
        """Test computation of repository directory from idCode"""
        self.assertEqual(self.crpi.getFileDir("ABC"), os.path.join("components", "ligand-dict-v3", "A", "ABC"))
        self.assertEqual(self.crpi.getFileDir("PRD_000001"), os.path.join("components", "prd-v3", "1"))
        self.assertEqual(self.crpi.getFileDir("PRDCC_000001"), os.path.join("components", "prdcc-v3", "1"))
        self.assertEqual(self.crpi.getFileDir("FAM_000001"), os.path.join("components", "family-v3", "1"))

        # unresolvable id type yields no directory
        self.assertIsNone(self.crpi.getFileDir("ABCDEF"))

    def testGetProjectPath(self) -> None:
        """Test computation of project path from idCode or explicit id_type"""
        self.assertEqual(self.crpi.getProjectPath("ABC"), os.path.join("components", "ligand-dict-v3"))
        self.assertEqual(self.crpi.getProjectPath("PRD_000001"), os.path.join("components", "prd-v3"))
        self.assertEqual(self.crpi.getProjectPath("PRDCC_000001"), os.path.join("components", "prdcc-v3"))
        self.assertEqual(self.crpi.getProjectPath("FAM_000001"), os.path.join("components", "family-v3"))

        # explicit id_type without/overriding idCode
        self.assertEqual(self.crpi.getProjectPath(id_type="CC"), os.path.join("components", "ligand-dict-v3"))
        self.assertEqual(self.crpi.getProjectPath("ABC", id_type="PRD"), os.path.join("components", "prd-v3"))

        # unresolvable id type
        self.assertIsNone(self.crpi.getProjectPath("ABCDEF"))

    def testGetCvsProjectInfo(self) -> None:
        """Test computation of the CVS project name and relative path from idCode"""
        self.assertEqual(self.crpi.getCvsProjectInfo("ABC"), ("ligand-dict-v3", os.path.join("A", "ABC", "ABC.cif")))
        self.assertEqual(self.crpi.getCvsProjectInfo("PRD_000001"), ("prd-v3", os.path.join("1", "PRD_000001.cif")))
        self.assertEqual(self.crpi.getCvsProjectInfo("PRDCC_000001"), ("prdcc-v3", os.path.join("1", "PRDCC_000001.cif")))
        self.assertEqual(self.crpi.getCvsProjectInfo("FAM_000001"), ("family-v3", os.path.join("1", "FAM_000001.cif")))

        # explicit id_type overrides inference
        self.assertEqual(self.crpi.getCvsProjectInfo("PRD_000001", id_type="PRD"), self.crpi.getCvsProjectInfo("PRD_000001"))

        # unresolvable id type returns (None, None)
        self.assertEqual(self.crpi.getCvsProjectInfo("ABCDEF"), (None, None))

    def testAssignIdCodeFromFileName(self) -> None:
        """Test recovery of an idCode from a repository file path"""
        self.assertEqual(self.crpi.assignIdCodeFromFileName("/some/path/to/ABC.cif"), "ABC")
        self.assertEqual(self.crpi.assignIdCodeFromFileName("/some/path/to/prd_000001.cif"), "PRD_000001")
        # too short a path is rejected
        self.assertIsNone(self.crpi.assignIdCodeFromFileName("ab.c"))
        self.assertIsNone(self.crpi.assignIdCodeFromFileName(None))

    def testAssignCvsProjectName(self) -> None:
        """Test assignment of CVS project name for each repository type, with and without testMode"""
        self.assertIsNotNone(self.crpi.assignCvsProjectName("CC"))
        self.assertIsNotNone(self.crpi.assignCvsProjectName("PRDCC"))
        self.assertIsNotNone(self.crpi.assignCvsProjectName("PRD"))
        self.assertIsNotNone(self.crpi.assignCvsProjectName("PRD_FAMILY"))

        # Unrecognized type or missing type yields None
        self.assertIsNone(self.crpi.assignCvsProjectName(None))
        self.assertIsNone(self.crpi.assignCvsProjectName("BOGUS"))  # type: ignore[arg-type]

        # testMode uses surrogate project names
        self.assertEqual(self.crpiTest.assignCvsProjectName("CC"), "test-ligand-v1")
        self.assertEqual(self.crpiTest.assignCvsProjectName("PRDCC"), "test-project-v1")
        self.assertEqual(self.crpiTest.assignCvsProjectName("PRD"), "test-project-v1")
        self.assertEqual(self.crpiTest.assignCvsProjectName("PRD_FAMILY"), "test-project-v1")
        self.assertIsNone(self.crpiTest.assignCvsProjectName(None))
        self.assertIsNone(self.crpiTest.assignCvsProjectName("BOGUS"))  # type: ignore[arg-type]


def chemRefStandardTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ChemRefPathInfoTests("testCCDHash"))
    suiteSelect.addTest(ChemRefPathInfoTests("testGetIdType"))
    suiteSelect.addTest(ChemRefPathInfoTests("testGetFilePath"))
    suiteSelect.addTest(ChemRefPathInfoTests("testGetFileDir"))
    suiteSelect.addTest(ChemRefPathInfoTests("testGetProjectPath"))
    suiteSelect.addTest(ChemRefPathInfoTests("testGetCvsProjectInfo"))
    suiteSelect.addTest(ChemRefPathInfoTests("testAssignIdCodeFromFileName"))
    suiteSelect.addTest(ChemRefPathInfoTests("testAssignCvsProjectName"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    mySuite = chemRefStandardTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
