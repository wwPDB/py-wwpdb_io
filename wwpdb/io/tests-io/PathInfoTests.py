##
# File:    PathInfoTests.py
# Date:    26-Feb-2013
#
# Updates:
#   27-Aug-2013  jdw verify after milestone addition to api.
#   28-Jun-2014  jdw add template examples
#   23-Oct-2017  jdw update logging
##
"""
Skeleton examples for creating standard file names for sequence resources and data files.

 **** A file source must be created to support these examples  ****

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import time
import unittest
import os
import platform

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TESTOUTPUT = os.path.join(HERE, 'test-output', platform.python_version())
if not os.path.exists(TESTOUTPUT):
    os.makedirs(TESTOUTPUT)
mockTopPath = os.path.join(TOPDIR, 'wwpdb', 'mock-data')

# Must create config file before importing ConfigInfo
from wwpdb.utils.testing.SiteConfigSetup import SiteConfigSetup

SiteConfigSetup().setupEnvironment(TESTOUTPUT, mockTopPath)

from wwpdb.utils.config.ConfigInfo import getSiteId
from wwpdb.io.locator.PathInfo import PathInfo

import logging

FORMAT = '[%(levelname)s]-%(module)s.%(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger()


class PathInfoTests(unittest.TestCase):

    def setUp(self):
        #
        self.__verbose = True
        self.__siteId = getSiteId(defaultSiteId=None)

        self.__startTime = time.time()
        logger.debug("Starting %s at %s" % (self.id(),
                                            time.strftime("%Y %m %d %H:%M:%S", time.localtime())))

    def tearDown(self):
        endTime = time.time()
        logger.debug("Completed %s at %s (%.4f seconds)\n" % (self.id(),
                                                              time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                              endTime - self.__startTime))

    def testGetStandardPaths(self):
        """ Test getting standard file names within session paths.
        """
        ok = True
        # fileSource, id, partionId, versionId
        tests = [('archive', "D_1000000000", None, 1, 'latest'),
                 ('archive', "D_1000000000", None, 'latest', 'latest'),
                 ('archive', "D_1000000000", None, 'next', 'latest'),
                 ('archive', "D_1000000000", None, 'previous', 'latest')]
        eId = '1'
        for (fs, dataSetId, wfInst, pId, vId) in tests:
            logger.debug(
                "File source %s dataSetId %s  partno  %s wfInst %s version %s" % (fs, dataSetId, pId, wfInst, vId))

            pI = PathInfo(siteId=self.__siteId)
            #
            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Model path (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find model file - default")

            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId,
                                         mileStone='deposit')
            logger.debug("Model path (deposit) (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find model file - deposit")

            fp = pI.getModelPdbxFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId,
                                         mileStone='upload')
            logger.debug("Model path (upload) (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find model file - upload")

            fp = pI.getModelPdbFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Model path (PDB):    %s" % fp)
            self.assertIsNotNone(fp, "Failed to find PDB model file")

            fp = pI.getPolyLinkFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Link dist  (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find PDBx model file")

            fp = pI.getSequenceStatsFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Sequence stats (PIC):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find sequence stats file")

            fp = pI.getReferenceSequenceFilePath(dataSetId, entityId=eId, wfInstanceId=wfInst, fileSource=fs,
                                                 versionId=vId)
            logger.debug("Reference match entity %s (PDBx):   %s" % (eId, fp))
            self.assertIsNotNone(fp, "Failed to find reference sequence file")

            fp = pI.getSequenceAssignmentFilePath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId)
            logger.debug("Sequence assignment (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find sequence assignment")

            fp = pI.getFilePath(dataSetId, wfInstanceId=wfInst, contentType='seqdb-match', formatType='pdbx',
                                fileSource=fs, versionId=vId, partNumber=pId, mileStone=None)
            logger.debug("Sequence match (getFilePath) (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find seq-db match")
            #
            fp = pI.getArchivePath(dataSetId)
            logger.debug("getArchivePath (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find dir path")

            fp = pI.getDepositPath(dataSetId)
            logger.debug("getDepositPath (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find deposit path")

            fp = pI.getInstancePath(dataSetId, wfInstanceId='W_099')
            logger.debug("getWfInstancePath (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find wf instance path")

            fp = pI.getInstanceTopPath(dataSetId,)
            logger.debug("getWfInstanceTopPath (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find wf Top instance path")
            #
            fp = pI.getDirPath(dataSetId, wfInstanceId=wfInst, fileSource=fs, versionId=vId, partNumber=pId,
                               mileStone=None)
            logger.debug("Sequence match (getDirPath) (PDBx):   %s" % fp)
            self.assertIsNotNone(fp, "Failed to find dir path")

            ft = pI.getFilePathVersionTemplate(dataSetId, wfInstanceId=wfInst, contentType='em-volume',
                                               formatType='map', fileSource="archive", partNumber=pId, mileStone=None)
            logger.debug("EM volume version template:   %r" % ft)
            ft = pI.getFilePathPartitionTemplate(dataSetId, wfInstanceId=wfInst, contentType='em-mask-volume',
                                                 formatType='map', fileSource="archive", mileStone=None)
            logger.debug("EM mask partition template:   %r" % ft)
            self.assertIsNotNone(ft, "Failed to mask model file")

        self.assertEqual(ok, True)

    def testSessionPath(self):
        tests = [('archive', "D_1000000000", 'session_test/12345')]
        for (fs, dataSetId, session_dir) in tests:
            logger.debug(
                "File source %s dataSetId %s  session dir %s" % (fs, dataSetId, session_dir))

            pI = PathInfo(siteId=self.__siteId, sessionPath=session_dir)
            session_path = pI.getDirPath(dataSetId=dataSetId, fileSource='session')
            self.assertIsNotNone(session_path, "Failed to get session path")

            session_download_path = pI.getWebDownloadPath(dataSetId=dataSetId)
            self.assertIsNotNone(session_download_path, "Failed to get session path")
            #


def suiteStandardPathTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(PathInfoTests("testGetStandardPaths"))
    suiteSelect.addTest(PathInfoTests("testSessionPath"))
    return suiteSelect


if __name__ == '__main__':
    if (True):
        mySuite = suiteStandardPathTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
