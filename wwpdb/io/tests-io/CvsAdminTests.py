##
#
# File:    CvsAdminTests.py
# Author:  j. westbrook
# Date:    11-April-2011
# Version: 0.001
#
# Update:
# 12-April-2011 jdw - revision checkout test cases.
# 29-Nov  -2012 jdw - refactor CvsAdmin and CvsSandBoxAdmin classes
#  2-Dec  -2012 jdw - add commit tests
# 28-Jan  -2013 jdw - revise tests for change in return prototype.
##
"""
Test cases for the CvsAdmin module.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.001"

# Disable checks for use of _getframe
# pylint: disable=protected-access

import sys
import unittest
import os
import os.path
import traceback
import shutil

from wwpdb.io.cvs.CvsAdmin import CvsAdmin, CvsSandBoxAdmin
from wwpdb.utils.testing.Features import Features


@unittest.skipUnless(Features().haveCvsTestServer(), "Needs CVS server for testing")
class CvsAdminTests(unittest.TestCase):
    def setUp(self):
        self.__lfh = sys.stdout
        #
        self.__testFilePath = "ligand-dict-v3/A/ATP/ATP.cif"
        self.__testDirPath = "ligand-dict-v3/A/ATP/"
        #
        self.__cvsRepositoryPath = "/cvs-ligands"
        self.__cvsRepositoryHost = os.getenv("CVS_TEST_SERVER")

        self.__realProjectName = "prd-v3"
        self.__testProjectName = "test-project-v1"
        self.__testFilePath2 = os.path.abspath("./data/TEST-FILE.DAT")

        self.__cvsUser = os.getenv("CVS_TEST_USER")
        self.__cvsPassword = os.getenv("CVS_TEST_PW")

    def tearDown(self):
        pass

    def testCvsHistory(self):
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text = ""
            vc = CvsAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            ok, text = vc.getHistory(cvsPath=self.__testFilePath)
            self.__lfh.write("CVS history status %r for %s is:\n%s\n" % (ok, self.__testFilePath, text))
            #
            ok, revList = vc.getRevisionList(cvsPath=self.__testFilePath)
            self.__lfh.write("CVS revision list status %r for %s is:\n%r\n" % (ok, self.__testFilePath, revList))
            vc.cleanup()
        except Exception as e:
            self.__lfh.write("Exception in %s %s\n" % (self.__class__.__name__, str(e)))
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testCvsCheckOutFile(self):
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text = ""
            vc = CvsAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            ok, text = vc.checkOutFile(cvsPath=self.__testFilePath, outPath="ATP-latest.cif")
            self.__lfh.write("\nCVS checkout status %r output %s is:\n%s\n" % (ok, self.__testFilePath, text))
            #
            vc.cleanup()
        except Exception as e:
            self.__lfh.write("Exception in %s %s\n" % (self.__class__.__name__, str(e)))
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testCvsCheckOutRevisions(self):
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text = ""
            vc = CvsAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)

            ok, revList = vc.getRevisionList(cvsPath=self.__testFilePath)
            self.__lfh.write("CVS revision list status %r for %s is:\n%r\n" % (ok, self.__testFilePath, revList))

            (_pth, fn) = os.path.split(self.__testFilePath)
            (base, ext) = os.path.splitext(fn)

            for revId in revList:
                rId = revId[0]
                outPath = base + "-" + rId + "." + ext
                ok, text = vc.checkOutFile(cvsPath=self.__testFilePath, outPath=outPath, revId=rId)
                self.__lfh.write("CVS checkout status %r output %s is:\n%s\n" % (ok, self.__testFilePath, text))
            #
            vc.cleanup()
        except Exception as e:
            self.__lfh.write("Exception in %s %s\n" % (self.__class__.__name__, str(e)))
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testCvsCheckOutProject(self):
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text = ""
            vc = CvsSandBoxAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            #
            vc.setSandBoxTopPath("./CVSWORK")
            ok, text = vc.checkOut(projectPath=self.__testProjectName)
            self.__lfh.write("CVS checkout status %r output is:\n%s\n" % (ok, text))
            #
            vc.cleanup()
        except Exception as e:
            self.__lfh.write("Exception in %s %s\n" % (self.__class__.__name__, str(e)))
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testCvsUpdateProject(self):
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text = ""
            vc = CvsSandBoxAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            #
            vc.setSandBoxTopPath("./CVSWORK")
            ok, text = vc.update(projectDir=self.__testProjectName)
            self.__lfh.write("CVS update status %r output is:\n%s\n" % (ok, text))
            #
            vc.cleanup()
        except Exception as e:
            self.__lfh.write("Exception in %s %s\n" % (self.__class__.__name__, str(e)))
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testCvsAddCommit(self):
        """
        """
        self.__lfh.write("Starting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            text = ""
            vc = CvsSandBoxAdmin(tmpPath="./")
            vc.setRepositoryPath(host=self.__cvsRepositoryHost, path=self.__cvsRepositoryPath)
            vc.setAuthInfo(user=self.__cvsUser, password=self.__cvsPassword)
            #
            vc.setSandBoxTopPath("./CVSWORK")
            ok, text = vc.checkOut(projectPath=self.__testProjectName)
            self.__lfh.write("CVS update status %r output is:\n%s\n" % (ok, text))
            #
            projPath = os.path.join(vc.getSandBoxTopPath(), self.__testProjectName)
            dstDir = "D1"
            dstPath = os.path.join(projPath, dstDir)
            if not os.access(dstPath, os.F_OK):
                os.mkdir(dstPath)
            fPath1 = os.path.join(dstPath, "F1.DAT")
            shutil.copy2(self.__testFilePath2, fPath1)
            fPath2 = os.path.join(dstPath, "F2.DAT")
            shutil.copy2(self.__testFilePath2, fPath2)
            #
            vc.add(self.__testProjectName, dstDir)

            rPath1 = os.path.join(dstDir, "F1.DAT")
            rPath2 = os.path.join(dstDir, "F2.DAT")
            vc.add(self.__testProjectName, rPath1)
            ok, text = vc.add(self.__testProjectName, rPath2)
            self.__lfh.write("CVS add status %r  output is:\n%s\n" % (ok, text))

            vc.commit(self.__testProjectName, rPath1)
            ok, text = vc.commit(self.__testProjectName, rPath2)
            self.__lfh.write("CVS commit status %r output is:\n%s\n" % (ok, text))

            #
            vc.remove(self.__testProjectName, rPath2)
            ok, text = vc.remove(self.__testProjectName, rPath1)
            self.__lfh.write("CVS remove status %r output is:\n%s\n" % (ok, text))

            vc.remove(self.__testProjectName, dstDir)

            ok, text = vc.update(projectDir=self.__testProjectName, prune=True)
            self.__lfh.write("CVS update status %r output is:\n%s\n" % (ok, text))

            #
            vc.cleanup()
        except Exception as e:
            self.__lfh.write("Exception in  %s %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, str(e)))
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suiteCvsTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(CvsAdminTests("testCvsHistory"))
    suiteSelect.addTest(CvsAdminTests("testCvsCheckOutFile"))
    suiteSelect.addTest(CvsAdminTests("testCvsCheckOutRevisions"))
    return suiteSelect


def suiteCvsSandBoxTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(CvsAdminTests("testCvsCheckOutProject"))
    suiteSelect.addTest(CvsAdminTests("testCvsUpdateProject"))
    suiteSelect.addTest(CvsAdminTests("testCvsAddCommit"))
    return suiteSelect


if __name__ == "__main__":
    if False:  # pylint: disable=using-constant-test
        mySuite = suiteCvsTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
        #
        mySuite = suiteCvsSandBoxTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    mySuite = suiteCvsSandBoxTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
