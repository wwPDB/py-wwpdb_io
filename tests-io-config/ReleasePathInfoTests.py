##
# File:    ReleasePathInfoTests.py
# Date:    1-Nov-2019
#
# Updates:
##
"""
Tests to ensure access to for_release directories

"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"

# ruff: noqa: PT027
import logging
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

from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo  # noqa: E402
from wwpdb.utils.config.ConfigInfo import getSiteId  # noqa: E402

FORMAT = "[%(levelname)s]-%(module)s.%(funcName)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger()


class ReleasePathInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        #
        self.__siteId = getSiteId(defaultSiteId=None)

    def testGetReleasePaths(self) -> None:
        """Test getting standard file names within session paths."""
        tests: list[list[str | None]] = [
            # subdir, vers
            [None, None],
            ["modified", None],
            ["val_reports", None],
            [None, "previous"],
            [None, "current"],
            ["modified", "previous"],
        ]
        for subdir, vers in tests:
            rpi = ReleasePathInfo(self.__siteId)
            if vers and subdir:
                ret = rpi.getForReleasePath(subdir=subdir, version=vers)
            elif vers:
                ret = rpi.getForReleasePath(version=vers)
            elif subdir:
                ret = rpi.getForReleasePath(subdir=subdir)
            else:
                ret = rpi.getForReleasePath()

            self.assertIsNotNone(ret)
            # print(ret)

    def testGetEMReleaseSubPaths(self) -> None:
        """Test getting standard file names within session paths."""
        emsub = [
            "header",
            "map",
            "fsc",
            "images",
            "masks",
            "other",
            "validation",
        ]
        for emsubdir in emsub:
            rpi = ReleasePathInfo(self.__siteId)
            ret = rpi.getForReleasePath(subdir="emd", accession="EMD-1000", em_sub_path=emsubdir)
            # print(ret)
            self.assertIsNotNone(ret)

    def testGetReleasePathsExceptions(self) -> None:
        """Test expected exceptions"""
        rpi = ReleasePathInfo(self.__siteId)

        with self.assertRaises(NameError):
            rpi.getForReleasePath(version="something")

        with self.assertRaises(NameError):
            rpi.getForReleasePath(subdir="something")

        with self.assertRaises(NameError):
            rpi.getForReleasePath(version="some", subdir="something")

        with self.assertRaises(NameError):
            rpi.getForReleasePath(subdir="emd", accession="EMD-1000", em_sub_path="something")


class ReleasePathInfoPreviousTests(unittest.TestCase):
    def setUp(self) -> None:
        self.RPI = ReleasePathInfo()

    def test_for_release(self) -> None:
        ret = self.RPI.get_for_release_path()
        self.assertIsNotNone(ret)

    def test_for_release_added(self) -> None:
        rel_path = self.RPI.get_for_release_path()
        ret = self.RPI.get_added_path()
        self.assertIsNotNone(ret)
        self.assertNotEqual(ret, rel_path)
        self.assertTrue("added" in ret)

    def test_for_release_added_previous(self) -> None:
        rel_path = self.RPI.get_for_release_path()
        ret = self.RPI.get_previous_added_path()
        self.assertIsNotNone(ret)
        self.assertNotEqual(ret, rel_path)
        self.assertTrue("added" in ret)
        self.assertTrue(self.RPI.previous_folder_name in ret)

    def test_for_release_modified(self) -> None:
        rel_path = self.RPI.get_for_release_path()
        ret = self.RPI.get_modified_path()
        self.assertIsNotNone(ret)
        self.assertNotEqual(ret, rel_path)
        self.assertTrue("modified" in ret)

    def test_for_release_modified_previous(self) -> None:
        rel_path = self.RPI.get_for_release_path()
        ret = self.RPI.get_previous_modified_path()
        self.assertIsNotNone(ret)
        self.assertNotEqual(ret, rel_path)
        self.assertTrue("modified" in ret)
        self.assertTrue(self.RPI.previous_folder_name in ret)

    def test_for_release_emd_header(self) -> None:
        rel_path = self.RPI.get_for_release_path()
        ret = self.RPI.get_emd_subfolder_path(accession="EMD-1223", subfolder="header")
        self.assertIsNotNone(ret)
        self.assertNotEqual(ret, rel_path)
        self.assertTrue("emd" in ret)

    def test_for_release_emd_header_previous(self) -> None:
        rel_path = self.RPI.get_for_release_path()
        ret = self.RPI.get_previous_emd_subfolder_path(accession="EMD-1234", subfolder="header")
        self.assertIsNotNone(ret)
        self.assertNotEqual(ret, rel_path)
        self.assertTrue("emd" in ret)
        self.assertTrue(self.RPI.previous_folder_name in ret)


def suiteStandardPathTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ReleasePathInfoTests("testGetReleasePaths"))
    suiteSelect.addTest(ReleasePathInfoTests("testGetEMReleaseSubPaths"))
    suiteSelect.addTest(ReleasePathInfoTests("testGetReleasePathsExceptions"))
    return suiteSelect


def suitePreviousPathTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ReleasePathInfoPreviousTests("test_for_release"))
    suiteSelect.addTest(ReleasePathInfoPreviousTests("test_for_release_added"))
    suiteSelect.addTest(ReleasePathInfoPreviousTests("test_for_release_added_previous"))
    suiteSelect.addTest(ReleasePathInfoPreviousTests("test_for_release_modified"))
    suiteSelect.addTest(ReleasePathInfoPreviousTests("test_for_release_modified_previous"))
    suiteSelect.addTest(ReleasePathInfoPreviousTests("test_for_release_emd_header"))
    suiteSelect.addTest(ReleasePathInfoPreviousTests("test_for_release_emd_header_previous"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    if True:  # pylint: disable=using-constant-test
        mySuite = suiteStandardPathTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
    if True:  # pylint: disable=using-constant-test
        mySuite = suitePreviousPathTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
