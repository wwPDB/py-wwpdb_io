"""

File:    DataFileTests.py
Author:  jdw
Date:    21-Aug-2009
Version: 0.001

"""
import sys
import unittest
import time
import os
import os.path
import traceback
import platform

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(HERE)
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)  # pragma: no cover
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup  # noqa: E402

SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.utils.config.ConfigInfo import ConfigInfo  # noqa: E402
from wwpdb.io.file.DataFile import DataFile  # noqa: E402


class DataFileTests(unittest.TestCase):
    def setUp(self):
        cI = ConfigInfo()
        self.__testFilePath = cI.get("TEST_FILE_PATH")
        self.__testFile = cI.get("TEST_FILE")
        self.__testFileGzip = cI.get("TEST_FILE_GZIP")
        self.__testFileZlib = cI.get("TEST_FILE_ZLIB")
        self.__testFileBzip = cI.get("TEST_FILE_BZIP")
        self.__outPath = TESTOUTPUT
        self.__outFileList = ["OUTPUT.dat.gz", "OUTPUT.dat", "OUTPUT.dat.bz2", "OUTPUT.dat.Z"]
        self.lfh = sys.stdout

    def tearDown(self):
        pass

    def testPrintInfo(self):
        """"""
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            fPath = os.path.join(self.__testFilePath, self.__testFile)
            f1 = DataFile(fPath)
            f1.pr(self.lfh)
        except:  # noqa: E722  # pragma: no cover
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testCopyTimeModePreserve(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            fPath = os.path.join(self.__testFilePath, self.__testFile)
            f1 = DataFile(fPath)
            f1.pr(self.lfh)
            #
            f1.timeMode("preserve")
            for fn in self.__outFileList:
                fp = os.path.join(self.__outPath, fn)
                f1.copy(fp)
                f1.pr(self.lfh)
                self.lfh.write("Files are the same  = %s\n" % str(f1.compare()))
                self.lfh.write("Source newer than %s\n" % f1.newerThan(fp))
                f2 = DataFile(fp)
                if f2.srcFileExists():
                    f2.remove()
        except:  # noqa: E722  # pragma: no cover
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testCopyTimeModeToday(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            fPath = os.path.join(self.__testFilePath, self.__testFile)
            f1 = DataFile(fPath)
            f1.pr(self.lfh)
            #
            f1.timeMode("today")
            for fn in self.__outFileList:
                fp = os.path.join(self.__outPath, fn)
                f1.copy(fp)
                f1.pr(self.lfh)
                self.lfh.write("Files are the same  = %s\n" % str(f1.compare()))
                self.lfh.write("Source newer than %s\n" % f1.newerThan(fp))
                f2 = DataFile(fp)
                if f2.srcFileExists():
                    f2.remove()
        except:  # noqa: E722  # pragma: no cover
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testCopyTimeModeNone(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            fPath = os.path.join(self.__testFilePath, self.__testFile)
            f1 = DataFile(fPath)
            f1.pr(self.lfh)
            #
            f1.timeMode(None)
            for fn in self.__outFileList:
                fp = os.path.join(self.__outPath, fn)
                f1.copy(fp)
                f1.pr(self.lfh)
                self.lfh.write("Files are the same  = %s\n" % str(f1.compare()))
                self.lfh.write("Source newer than %s\n" % str(f1.newerThan(fp)))
                f2 = DataFile(fp)
                if f2.srcFileExists():
                    f2.remove()
        except:  # noqa: E722  # pragma: no cover
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testSymbolicLinks(self):
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            fList = [self.__testFile, self.__testFileGzip, self.__testFileZlib, self.__testFileBzip]
            for fn in fList:
                fPath = os.path.join(self.__testFilePath, fn)
                f1 = DataFile(fPath)
                fp = os.path.join(self.__outPath, fn)
                f1.symLinkRelative(fp)
                f1.pr()
                self.lfh.write("Files are the same  = %s\n" % str(f1.compare()))
                self.lfh.write("Source newer than %s\n" % str(f1.newerThan(fp)))
                f2 = DataFile(fp)
                if f2.srcFileExists():
                    f2.remove()
        except:  # noqa: E722  # pragma: no cover
            traceback.print_exc(file=sys.stdout)
            self.fail()

    @unittest.skip("Not sending email during tests")
    def testFileEMail(self):  # pragma: no cover
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            fPath = os.path.join(self.__testFilePath, self.__testFile)
            f1 = DataFile(fPath)
            f1.eMail("jwest@rcsb.rutgers.edu", "jwest@rcsb.rutgers.edu", "IGNORE THIS TEST MESSAGE")
        except:  # noqa: E722
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testTimes(self):
        """Tests accessing times"""
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        fList = [self.__testFile, self.__testFileGzip, self.__testFileZlib, self.__testFileBzip]
        for fn in fList:
            fPath = os.path.join(self.__testFilePath, fn)
            f1 = DataFile(fPath)
            self.assertIsNotNone(f1.srcModTimeStamp())

        # Test non existant case
        f1 = DataFile(os.path.join(TESTOUTPUT, "nonexistant"))
        self.assertIsNone(f1.srcModTimeStamp())

        # newerThan testing
        f1path = os.path.join(TESTOUTPUT, "file1.tst")
        f2path = os.path.join(TESTOUTPUT, "file2.tst")
        for f in [f1path, f2path]:
            if os.path.exists(f):
                os.remove(f)
            # touch file
            with open(f, "w") as f:
                pass
            # So timestamp not same
            time.sleep(1.2)

        d1 = DataFile(f1path)
        self.assertIsNone(d1.newerThan(None))
        self.assertIsNone(d1.newerThan(os.path.join(TESTOUTPUT, "nonexistant")))
        self.assertFalse(d1.newerThan(f2path))
        d2 = DataFile(f2path)
        self.assertTrue(d2.newerThan(f1path))

        # Compare same times
        self.assertFalse(d1.newerThan(f1path))

        # f1 is still nonexistant
        self.assertIsNone(f1.newerThan(f2path))

    def testSymlink(self):
        """Tests symlink creation"""
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        # Test non existant case

        f1path = os.path.join(TESTOUTPUT, "linkorigin.tst")
        f2path = os.path.join(TESTOUTPUT, "symlinkdst.tst")
        for f in [f1path, f2path]:
            if os.path.exists(f):
                os.remove(f)

        with open(f1path, "w") as f:
            pass

        d1 = DataFile(f1path)
        d1.symLink(f2path)

    def testMove(self):
        """Tests moving file -- and timemodes"""
        self.lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))

        f1path = os.path.join(TESTOUTPUT, "startfile.tst")
        f2path = os.path.join(TESTOUTPUT, "movedest.tst")
        f3path = os.path.join(TESTOUTPUT, "appendest.tst")
        if os.path.exists(f3path):
            os.remove(f3path)

        f1 = DataFile(os.path.join(TESTOUTPUT, "nonexistant"))
        self.assertEqual(f1.srcFileSize(), 0)
        # For test coverage
        f1.src(f1path)

        f3len = 0
        for tmode in ["preserve", "today", "yesterday", "tomorrow", "lastweek"]:
            for f in [f1path, f2path]:
                if os.path.exists(f):
                    os.remove(f)

            with open(f1path, "w") as f:
                f.write(tmode)
                pass

            d1 = DataFile(f1path)
            d1.timeMode(tmode)
            self.assertTrue(d1.setSrcFileMode(0o644))

            self.assertEqual(d1.srcFileSize(), len(tmode))
            # Pre copy - no dst set
            self.assertEqual(d1.dstFileSize(), 0)

            # Test append
            d1.append(f3path)
            f3len += len(tmode)
            d3 = DataFile(f3path)
            self.assertEqual(d3.srcFileSize(), f3len)

            d1.move(f2path)
            self.assertTrue(d1.setDstFileMode(0o644))
            self.assertEqual(d1.dstFileSize(), len(tmode))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
