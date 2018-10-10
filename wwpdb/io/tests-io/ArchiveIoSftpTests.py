##
# File:    ArchiveIoSftp.py
# Author:  jdw
# Date:    10-Oct-2017
# Version: 0.001
#
# Updates:
#
##
"""
Archive data transfer operation utilities using SFTP protocol

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

#
#
import sys
import os.path
import time
import unittest
import logging
logger = logging.getLogger(__name__)
#
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.io.sftp.ArchiveIoSftp import ArchiveIoSftp
from wwpdb.utils.testing.Features import Features


@unittest.skipUnless(Features().haveSftpTestServer(), "Needs SFTP server for testing")
class ArchiveIoSftpTests(unittest.TestCase):

    def setUp(self):
        self.__lfh = sys.stderr
        self.__verbose = False
        #
        self.__serverId = 'BACKUP_SERVER_RDI2'
        self.__cI = ConfigInfo(siteId=getSiteId(), verbose=self.__verbose, log=self.__lfh)
        cD = self.__cI.get(self.__serverId, {})
        self.__hostName = cD.get('HOST_NAME')
        self.__userName = cD.get('HOST_USERNAME')
        self.__hostPort = int(cD.get('HOST_PORT'))
        self.__protocol = cD.get('HOST_PROTOCOL')
        self.__rootPath = cD.get('HOST_ROOT_PATH')
        self.__keyFilePath = cD.get('HOST_KEY_FILE_PATH')
        self.__keyFileType = cD.get('HOST_KEY_FILE_TYPE')
        #
        self.__testLocalFilePath = './data/TEST-FILE.DAT'
        self.__testLocalOutputFilePath = './JUNK.JUNK'
        #
        self.__startTime = time.time()
        logger.debug("Starting %s at %s" % (self.id(),
                                            time.strftime("%Y %m %d %H:%M:%S", time.localtime())))

    def tearDown(self):
        endTime = time.time()
        logger.debug("Completed %s at %s (%.4f seconds)\n" % (self.id(),
                                                              time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                              endTime - self.__startTime))

    def testSftpConnect(self):
        """Test case - for connection-
        """

        try:
            aio = ArchiveIoSftp()
            ok = aio.connect(self.__hostName, self.__userName, self.__hostPort, keyFilePath=self.__keyFilePath, keyFileType=self.__keyFileType)
            aio.close()
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()
#

    def testSftpStatOps(self):
        """Test case -  get directory list and stat details-
        """
        try:
            aio = ArchiveIoSftp(serverId=self.__serverId)
            ok = aio.connectToServer()
            result = aio.listdir('.')
            logger.info("listdir: %r" % result)
            result = aio.stat('.')
            logger.info("stat: %r" % result)
            ok = aio.close()
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testSftpDirOps(self):
        """Test case -  create and remove directory -
        """
        try:
            aio = ArchiveIoSftp(serverId=self.__serverId)
            ok = aio.connectToServer()
            testPath = os.path.join(self.__rootPath, 'test')
            ok = aio.mkdir(testPath)
            result = aio.listdir(self.__rootPath)
            logger.debug("listdir: %r" % result)
            result = aio.stat(testPath)
            logger.info("stat good: %r" % result)
            ok = aio.rmdir(testPath)
            result = aio.listdir(self.__rootPath)
            logger.debug("listdir after remove: %r" % result)
            #
            testPathBad = os.path.join(self.__rootPath, 'test_bad')
            result = aio.listdir(testPathBad)
            logger.debug("listdir bad : %r" % result)
            result = aio.stat(testPathBad)
            logger.info("bad stat: %r" % result)

            ok = aio.close()
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()

    def testSftpTransferOps(self):
        """Test case -  transfer and remove files and directories -
        """
        try:
            aio = ArchiveIoSftp(serverId=self.__serverId)
            ok = aio.connectToServer()
            testDirPath = os.path.join(self.__rootPath, 'test')
            testFilePath1 = os.path.join(testDirPath, 'TEST-FILE-1.DAT')
            testFilePath2 = os.path.join(testDirPath, 'TEST-FILE-2.DAT')
            ok = aio.mkdir(testDirPath)
            ok = aio.put(self.__testLocalFilePath, testFilePath1)
            ok = aio.put(self.__testLocalFilePath, testFilePath2)
            #
            aio.get(testFilePath1, self.__testLocalOutputFilePath)
            aio.get(testFilePath2, self.__testLocalOutputFilePath)
            #
            result = aio.listdir(testDirPath)
            logger.debug("listdir: %r" % result)
            ok = aio.remove(testFilePath1)
            ok = aio.remove(testFilePath2)
            #
            result = aio.listdir(testDirPath)
            logger.debug("listdir: %r" % result)
            #
            ok = aio.rmdir(testDirPath)
            result = aio.listdir(self.__rootPath)
            logger.debug("listdir after remove: %r" % result)
            ok = aio.close()
            self.assertEqual(ok, True)
        except Exception as e:
            logger.exception("Failing with %s" % str(e))
            self.fail()


def suiteSftpTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ArchiveIoSftpTests("testSftpConnect"))
    suiteSelect.addTest(ArchiveIoSftpTests("testSftpStatOps"))
    suiteSelect.addTest(ArchiveIoSftpTests("testSftpDirOps"))
    suiteSelect.addTest(ArchiveIoSftpTests("testSftpTransferOps"))
    return suiteSelect


if __name__ == '__main__':
    if (True):
        mySuite = suiteSftpTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
