##
# File:    LocalFTPPathInfoTests.py
# Date:    30-Jul-2026
#
# Updates:
##
"""
Test cases for LocalFTPPathInfo()

"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"

import os
import platform
import unittest

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

from wwpdb.io.locator.localFTPPathInfo import LocalFTPPathInfo  # noqa: E402


class LocalFTPPathInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__siteId = getSiteId(defaultSiteId=None)
        self.__pdbRoot = "/mock/pdb/ftp/root"
        self.__emdbRoot = "/mock/emdb/ftp/root"

    def testDefaultRootsUnset(self) -> None:
        """Without any configured/overridden roots, path getters return empty string."""
        lfpi = LocalFTPPathInfo(self.__siteId)
        # Mock config does not define these - defensively clear in case a site config does.
        lfpi.set_ftp_pdb_root(None)
        lfpi.set_ftp_emdb_root(None)

        self.assertEqual(lfpi.get_ftp_pdb(), "")
        self.assertEqual(lfpi.get_ftp_emdb(), "")
        self.assertEqual(lfpi.get_model_path(), "mmCIF")
        self.assertEqual(lfpi.get_sf_path(), "structure_factors")
        self.assertEqual(lfpi.get_cs_path(), "nmr_chemical_shifts")
        self.assertEqual(lfpi.get_nmr_data_path(), "nmr_data")

    def testSetFtpPdbRoot(self) -> None:
        """set_ftp_pdb_root() only updates the root when given a truthy value."""
        lfpi = LocalFTPPathInfo(self.__siteId)
        lfpi.set_ftp_pdb_root(self.__pdbRoot)

        self.assertEqual(lfpi.get_ftp_pdb(), os.path.join(self.__pdbRoot, "pdb", "data", "structures", "all"))

        # Falsy values (None or empty string) are ignored and do not clear an existing root
        lfpi.set_ftp_pdb_root(None)
        self.assertEqual(lfpi.get_ftp_pdb_root(), self.__pdbRoot)
        lfpi.set_ftp_pdb_root("")
        self.assertEqual(lfpi.get_ftp_pdb_root(), self.__pdbRoot)

    def testSetFtpEmdbRoot(self) -> None:
        """set_ftp_emdb_root() updates the root for any non-None value, including empty string."""
        lfpi = LocalFTPPathInfo(self.__siteId)
        lfpi.set_ftp_emdb_root(self.__emdbRoot)
        self.assertEqual(lfpi.get_ftp_emdb_root(), self.__emdbRoot)
        self.assertEqual(lfpi.get_ftp_emdb(), os.path.join(self.__emdbRoot, "emdb", "structures"))

        # None is ignored...
        lfpi.set_ftp_emdb_root(None)
        self.assertEqual(lfpi.get_ftp_emdb_root(), self.__emdbRoot)

        # ...but empty string is not - unlike set_ftp_pdb_root()
        lfpi.set_ftp_emdb_root("")
        self.assertEqual(lfpi.get_ftp_emdb_root(), "")
        self.assertEqual(lfpi.get_ftp_emdb(), "")

    def testGetContentPaths(self) -> None:
        """Test the per-content-type path getters once a pdb ftp root is configured."""
        lfpi = LocalFTPPathInfo(self.__siteId)
        lfpi.set_ftp_pdb_root(self.__pdbRoot)
        ftpPdb = lfpi.get_ftp_pdb()

        self.assertEqual(lfpi.get_model_path(), os.path.join(ftpPdb, "mmCIF"))
        self.assertEqual(lfpi.get_sf_path(), os.path.join(ftpPdb, "structure_factors"))
        self.assertEqual(lfpi.get_cs_path(), os.path.join(ftpPdb, "nmr_chemical_shifts"))
        self.assertEqual(lfpi.get_nmr_data_path(), os.path.join(ftpPdb, "nmr_data"))

    def testGetFileNames(self) -> None:
        """Test the full path + file name getters for a given accession."""
        lfpi = LocalFTPPathInfo(self.__siteId)
        lfpi.set_ftp_pdb_root(self.__pdbRoot)
        accession = "1abc"

        self.assertEqual(lfpi.get_model_fname(accession), os.path.join(lfpi.get_model_path(), "1abc.cif.gz"))
        self.assertEqual(lfpi.get_structure_factors_fname(accession), os.path.join(lfpi.get_sf_path(), "r1abcsf.ent.gz"))
        self.assertEqual(lfpi.get_chemical_shifts_fname(accession), os.path.join(lfpi.get_cs_path(), "1abc_cs.str.gz"))
        self.assertEqual(lfpi.get_nmr_data_fname(accession), os.path.join(lfpi.get_nmr_data_path(), "1abc_nmr-data.str.gz"))

    def testGetFileNamesNoRoot(self) -> None:
        """Without a configured root, file name getters still return a relative path."""
        lfpi = LocalFTPPathInfo(self.__siteId)
        lfpi.set_ftp_pdb_root(None)
        accession = "1abc"

        self.assertEqual(lfpi.get_model_fname(accession), os.path.join("mmCIF", "1abc.cif.gz"))
        self.assertEqual(lfpi.get_structure_factors_fname(accession), os.path.join("structure_factors", "r1abcsf.ent.gz"))
        self.assertEqual(lfpi.get_chemical_shifts_fname(accession), os.path.join("nmr_chemical_shifts", "1abc_cs.str.gz"))
        self.assertEqual(lfpi.get_nmr_data_fname(accession), os.path.join("nmr_data", "1abc_nmr-data.str.gz"))


def suiteLocalFTPPathInfoTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(LocalFTPPathInfoTests("testDefaultRootsUnset"))
    suiteSelect.addTest(LocalFTPPathInfoTests("testSetFtpPdbRoot"))
    suiteSelect.addTest(LocalFTPPathInfoTests("testSetFtpEmdbRoot"))
    suiteSelect.addTest(LocalFTPPathInfoTests("testGetContentPaths"))
    suiteSelect.addTest(LocalFTPPathInfoTests("testGetFileNames"))
    suiteSelect.addTest(LocalFTPPathInfoTests("testGetFileNamesNoRoot"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    mySuite = suiteLocalFTPPathInfoTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
