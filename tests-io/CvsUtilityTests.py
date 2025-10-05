##
#
# File:    CvsUtilityTests.py
# Author:  j. westbrook
# Date:    11-April-2011
# Version: 0.001
#
# Update:
# 12-April-2011 jdw - revision checkout test cases.
##
"""
Test cases for the CvsUtiltity module.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.001"

# Disable checks for use of _getframe
# pylint: disable=protected-access
# ruff: noqa: SLF001

import logging
import os
import os.path
import sys
import unittest

from wwpdb.io.cvs.CvsUtility import CvsWrapper
from wwpdb.utils.testing.Features import Features


@unittest.skipUnless(Features().haveCvsTestServer(), "Needs CVS server for testing")
class CvsUtilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__logger = logging.getLogger("wwpdb.utils.rcsb")
        #
        self.__testFilePath = "ligand-dict-v3/A/ATP/ATP.cif"
        #
        self.__cvsRepositoryPath = "/cvs-ligands"
        self.__cvsRepositoryHost = os.getenv("CVS_TEST_SERVER")

        self.__cvsUser = os.getenv("CVS_TEST_USER")
        self.__cvsPassword = os.getenv("CVS_TEST_PW")

    def tearDown(self) -> None:
        pass

    def testCvsHistory(self) -> None:
        """"""
        self.__logger.info("Starting %s %s", self.__class__.__name__, sys._getframe().f_code.co_name)
        try:
            text = ""
            vc = CvsWrapper(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            text = vc.getHistory(cvsPath=self.__testFilePath)
            self.__logger.debug("CVS history for %s is:\n%s\n", self.__testFilePath, text)
            #
            revList = vc.getRevisionList(cvsPath=self.__testFilePath)
            self.__logger.debug("CVS revision list for %s is:\n%r\n", self.__testFilePath, revList)
            vc.cleanup()
        except Exception as e:
            self.__logger.exception("Exception in %s %s", self.__class__.__name__, str(e))
            self.fail()

    def testCvsCheckOutFile(self) -> None:
        """"""
        self.__logger.info("Starting %s %s", self.__class__.__name__, sys._getframe().f_code.co_name)
        try:
            text = ""
            vc = CvsWrapper(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            text = vc.checkOutFile(cvsPath=self.__testFilePath, outPath="ATP-latest.cif")
            self.__logger.debug("CVS checkout output %s is:\n%s\n", self.__testFilePath, text)
            #
            vc.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            self.__logger.exception("Exception in %s", self.__class__.__name__)
            self.fail()

    def testCvsCheckOutRevisions(self) -> None:
        """"""
        self.__logger.info("Starting %s %s", self.__class__.__name__, sys._getframe().f_code.co_name)
        try:
            text = ""
            vc = CvsWrapper(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)

            revList = vc.getRevisionList(cvsPath=self.__testFilePath)
            self.__logger.debug("CVS revision list for %s is:\n%r\n", self.__testFilePath, revList)

            (_pth, fn) = os.path.split(self.__testFilePath)
            (base, ext) = os.path.splitext(fn)

            for revId in revList:
                rId = revId[0]
                outPath = base + "-" + rId + "." + ext
                text = vc.checkOutFile(cvsPath=self.__testFilePath, outPath=outPath, revId=rId)
                self.__logger.debug("CVS checkout output %s is:\n%s\n", self.__testFilePath, text)
            #
            vc.cleanup()
        except:  # noqa: E722 pylint: disable=bare-except
            self.__logger.exception("Exception in %s", self.__class__.__name__)
            self.fail()


if __name__ == "__main__":
    logger = logging.getLogger("wwpdb.utils.rcsb")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("CvsUtilityTests.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    #
    unittest.main()
