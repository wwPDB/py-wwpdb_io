##
# File:    ReleasePathInfoTests.py
# Date:    1-Nov-2019
#
# Updates:
##
"""
Tests to ensure access to for_release directories

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"

import unittest
import os
import platform
import logging

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup  # noqa: E402

SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.utils.config.ConfigInfo import getSiteId  # noqa: E402
from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo  # noqa: E402

FORMAT = "[%(levelname)s]-%(module)s.%(funcName)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger()


class ReleasePathInfoTests(unittest.TestCase):
    def setUp(self):
        #
        self.__siteId = getSiteId(defaultSiteId=None)

    def testGetReleasePaths(self):
        """ Test getting standard file names within session paths.
        """
        tests = [
            # subdir, vers
            [None, None],
            ["modified", None],
            ["val_reports", None],
            [None, "previous"],
            [None, "current"],
            ["modified", "previous"],
        ]
        for (subdir, vers) in tests:
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

    def testGetReleasePathsExceptions(self):
        """ Test expected exceptions """
        rpi = ReleasePathInfo(self.__siteId)

        with self.assertRaises(NameError):
            rpi.getForReleasePath(version="something")

        with self.assertRaises(NameError):
            rpi.getForReleasePath(subdir="something")

        with self.assertRaises(NameError):
            rpi.getForReleasePath(version="some", subdir="something")


def suiteStandardPathTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ReleasePathInfoTests("testGetReleasePaths"))
    suiteSelect.addTest(ReleasePathInfoTests("testGetReleasePathsExceptions"))
    return suiteSelect


if __name__ == "__main__":
    if True:
        mySuite = suiteStandardPathTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
