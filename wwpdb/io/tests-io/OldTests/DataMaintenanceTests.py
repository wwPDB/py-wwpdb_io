"""

File:    DataMaintenanceTests.py
Author:  jdw
Date:    13-June-2015
Version: 0.001

        Driver routines for testing purging and recovering selected content types and milestone files.

Updates:

  24-Oct-2016  jdw add test mode -

"""
import sys
import unittest
import os
import os.path
import traceback
import shutil
import scandir

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId
from wwpdb.io.file.DataMaintenance import DataMaintenance


class DataMaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.__lfh = sys.stderr
        self.__verbose = True
        # Get siteId from the environment -
        self.__siteId = getSiteId()
        self.__cI = ConfigInfo(siteId=self.__siteId)
        # In test mode, no deletions are performed -
        self.__testMode = True
        #
        #  An data set ID list must be set --
        self.__idListPath = "RELEASED.LIST"
        #
        self.__milestoneL = []
        self.__milestoneL.append(None)
        self.__milestoneL.extend(self.__cI.get("CONTENT_MILESTONE_LIST"))
        self.__cTBD = self.__cI.get("CONTENT_TYPE_BASE_DICTIONARY")
        self.__cTD = self.__cI.get("CONTENT_TYPE_DICTIONARY")
        self.__cTL = sorted(self.__cTBD.keys())
        # Example list of candidate content types for purging  -- this is based on system V15x for X-ray content types
        self.__cTypesOtherL = [
            "assembly-assign",
            "assembly-model",
            "assembly-model-xyz",
            "assembly-report",
            "chem-comp-assign",
            "chem-comp-assign-details",
            "chem-comp-assign-final",
            "chem-comp-depositor-info",
            "chem-comp-link",
            "component-image",
            "dcc-report",
            "dict-check-report",
            "dict-check-report-r4",
            "format-check-report",
            "geometry-check-report",
            "merge-xyz-report",
            "misc-check-report",
            "notes-from-annotator",
            "polymer-linkage-distances",
            "polymer-linkage-report",
            "secondary-structure-topology",
            "seq-align-data",
            "seq-assign",
            "seq-data-stats",
            "seqdb-match",
            "sequence-fasta",
            "sf-convert-report",
            "site-assign",
            "special-position-report",
            "validation-data",
            "validation-report",
            "validation-report-depositor",
            "validation-report-full",
            "validation-report-slider",
        ]
        #
        # Test snapshot directory required for recovery tests -
        self.__snapShotPath = "/net/wwpdb_da_data_archive/.snapshot/nightly.1/data"

    def tearDown(self):
        pass

    def __getIdList(self, fPath):
        if not os.access(fPath, os.R_OK):
            self.__lfh.write("__getIdList() Missing data set ID list file %s\n" % fPath)
            self.fail()
        #
        ifh = open(fPath, "r")
        fL = []
        #  D_10 00 00 00 01
        for line in ifh:
            tId = line[:-1]
            if len(tId) == 12 and tId.startswith("D_"):
                fL.append(tId)
        ifh.close()
        return fL

    def __getRecoveryInfo(self, purgeType="exp"):
        """Return the list of tuple describing content type and milestones to be recovered.

        return [{fileSource,contentType,formatType,mileStone,purgeType},]
        """
        rL = []
        if purgeType in ["exp"]:
            for ct in ["model"]:
                for fs in ["archive", "deposit"]:
                    for fm in ["pdbx", "pdb"]:
                        for milestone in self.__milestoneL:
                            if milestone in ["release", "annotate", "review"]:
                                rL.append({"fileSource": fs, "contentType": ct, "formatType": fm, "mileStone": milestone, "purgeType": "exp"})
            for ct in ["structure-factors"]:
                for fs in ["archive", "deposit"]:
                    for fm in ["pdbx", "mtz"]:
                        for milestone in self.__milestoneL:
                            if milestone in ["release", "annotate", "review"]:
                                rL.append({"fileSource": fs, "contentType": ct, "formatType": fm, "mileStone": milestone, "purgeType": "exp"})
        elif purgeType in ["other", "report"]:
            for ct in self.__cTypesOtherL:
                if ct not in ["validation-report", "validation-data", "validation-report-full"]:
                    continue
                for fs in ["archive", "deposit"]:
                    for fm in self.__cTD[ct][0]:
                        for milestone in self.__milestoneL:
                            if milestone in ["release", "annotate", "review"]:
                                rL.append({"fileSource": fs, "contentType": ct, "formatType": fm, "mileStone": milestone, "purgeType": "other"})
        return rL

    def testRecoverProductionList(self):
        """Test case for selected recovery of selected content types and milestone files from snapshot directory"""
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            idList = self.__getIdList(self.__idListPath)
            dm = DataMaintenance(siteId=self.__siteId, testMode=self.__testMode, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                recL = []
                for pType in ["exp", "other"]:
                    pTL = self.__getRecoveryInfo(purgeType=pType)
                    for pT in pTL:
                        vfL = dm.getVersionFileListSnapshot(
                            basePath=self.__snapShotPath,
                            dataSetId=id,
                            wfInstanceId=None,
                            fileSource=pT["fileSource"],
                            contentType=pT["contentType"],
                            formatType=pT["formatType"],
                            partitionNumber="1",
                            mileStone=pT["mileStone"],
                        )

                        self.__lfh.write("\n+testRecoverProductionList - id %13s cType %s\n" % (id, pT["contentType"]))
                        for ii, p in enumerate(vfL):
                            self.__lfh.write("+testRecoverProductionList- %4d  pair - %r\n" % (ii, p))
                        recL.extend(vfL)

                if len(recL) > 0:
                    for ii, p in enumerate(recL):
                        self.__lfh.write("+testRecoverProductionList- %4d  pairL - %r\n" % (ii, p))
                        shutil.copyfile(p[0], p[1])

        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def __getPurgeInfo(self, purgeType="exp"):
        """Return a list of tuples describing content types and milestone data files to be purged -

        return [{fileSource,contentType,formatType,mileStone,purgeType},]
        """
        rL = []
        if purgeType in ["exp"]:
            for ct in ["model"]:
                for fs in ["archive", "deposit"]:
                    for fm in ["pdbx", "pdb"]:
                        for milestone in self.__milestoneL:
                            rL.append({"fileSource": fs, "contentType": ct, "formatType": fm, "mileStone": milestone, "purgeType": "exp"})
            for ct in ["structure-factors", "em-structure-factors"]:
                for fs in ["archive", "deposit"]:
                    for fm in ["pdbx", "mtz"]:
                        for milestone in self.__milestoneL:
                            rL.append({"fileSource": fs, "contentType": ct, "formatType": fm, "mileStone": milestone, "purgeType": "exp"})
            for ct in ["nmr-chemical-shifts", "nmr-chemical-shifts-raw", "nmr-chemical-shifts-auth"]:
                for fs in ["archive", "deposit"]:
                    for fm in ["pdbx", "nmr-star"]:
                        for milestone in self.__milestoneL:
                            rL.append({"fileSource": fs, "contentType": ct, "formatType": fm, "mileStone": milestone, "purgeType": "exp"})
            for ct in ["em-volume", "em-mask-volume", "em-additional-volume"]:
                for fs in ["archive", "deposit"]:
                    for fm in ["map", "ccp4", "mrc2000"]:
                        for milestone in self.__milestoneL:
                            rL.append({"fileSource": fs, "contentType": ct, "formatType": fm, "mileStone": milestone, "purgeType": "exp"})
        elif purgeType in ["other", "report"]:
            for ct in self.__cTypesOtherL:
                for fs in ["archive", "deposit"]:
                    for fm in self.__cTD[ct][0]:
                        for milestone in self.__milestoneL:
                            rL.append({"fileSource": fs, "contentType": ct, "formatType": fm, "mileStone": milestone, "purgeType": "other"})

        return rL

    def __removePathList(self, pthList):
        #
        for pth in pthList:
            try:
                if self.__testMode:
                    self.__lfh.write("__removePathList() TEST MODE skip removing path %s\n" % pth)
                else:
                    os.remove(pth)
            except:
                pass

    def testCreatePurgeProductionList(self):
        """Test case for generating canditate files for purge -"""
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            idList = self.__getIdList(self.__idListPath)
            dm = DataMaintenance(siteId=self.__siteId, testMode=self.__testMode, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                rmLL = []
                for pType in ["exp", "other"]:
                    pTL = self.__getPurgeInfo(purgeType=pType)
                    for pT in pTL:
                        latest, rmL, gzL = dm.getPurgeCandidates(
                            id,
                            wfInstanceId=None,
                            fileSource=pT["fileSource"],
                            contentType=pT["contentType"],
                            formatType=pT["formatType"],
                            partitionNumber="1",
                            mileStone=pT["mileStone"],
                            purgeType=pT["purgeType"],
                        )
                        if latest is None:
                            continue
                        self.__lfh.write("\n+testPurgeCandidatesList - id %13s cType %s LATEST version %s\n" % (id, pT["contentType"], latest))
                        for ii, p in enumerate(rmL):
                            self.__lfh.write("+testPurgeCandidateList- %4d  rm - %r\n" % (ii, p))
                        for ii, p in enumerate(gzL):
                            self.__lfh.write("+testPurgeCandidateList- %4d  gz - %r\n" % (ii, p))
                        if len(rmL) > 0:
                            rmLL.extend(rmL)

                rmLL.extend(dm.getLogFiles(id, fileSource="deposit"))
                rmLL.extend(dm.getLogFiles(id, fileSource="archive"))
                if len(rmLL) > 0:
                    for ii, p in enumerate(rmLL):
                        self.__lfh.write("+testPurgeCandidateList- %4d  rmLL - %r\n" % (ii, p))

        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testPurgeProductionList(self):
        """Preliminary version of purge operations post release -"""
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            idList = self.__getIdList(self.__idListPath)
            dm = DataMaintenance(siteId=self.__siteId, testMode=self.__testMode, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                rmLL = []
                for pType in ["exp", "other"]:
                    pTL = self.__getPurgeInfo(purgeType=pType)
                    for pT in pTL:
                        latest, rmL, gzL = dm.getPurgeCandidates(
                            id,
                            wfInstanceId=None,
                            fileSource=pT["fileSource"],
                            contentType=pT["contentType"],
                            formatType=pT["formatType"],
                            partitionNumber="1",
                            mileStone=pT["mileStone"],
                            purgeType=pT["purgeType"],
                        )
                        if latest is None:
                            continue
                        self.__lfh.write("\n+testPurgeCandidatesList - id %13s cType %s LATEST version %s\n" % (id, pT["contentType"], latest))
                        for ii, p in enumerate(rmL):
                            self.__lfh.write("+testPurgeCandidateList- %4d  rm - %r\n" % (ii, p))
                        for ii, p in enumerate(gzL):
                            self.__lfh.write("+testPurgeCandidateList- %4d  gz - %r\n" % (ii, p))
                        if len(rmL) > 0:
                            rmLL.extend(rmL)

                rmLL.extend(dm.getLogFiles(id, fileSource="deposit"))
                rmLL.extend(dm.getLogFiles(id, fileSource="archive"))
                if len(rmLL) > 0:
                    for ii, p in enumerate(rmLL):
                        self.__lfh.write("+testPurgeCandidateList- %4d  rmLL - %r\n" % (ii, p))
                    self.__removePathList(rmLL)

        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testPurgeCandidatesList(self):
        """"""
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            idList = self.__getIdList(self.__idListPath)
            dm = DataMaintenance(siteId=self.__siteId, testMode=self.__testMode, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                latest, rmL, gzL = dm.getPurgeCandidates(id, wfInstanceId=None, fileSource="archive", contentType="model", formatType="pdbx", partitionNumber="1", mileStone=None)
                self.__lfh.write("\n\n+testPurgeCandidatesList - id %s LATEST version %s\n" % (id, latest))
                for ii, p in enumerate(rmL):
                    self.__lfh.write("+testPurgeCandidateList- %r  rm - %r\n" % (ii, p))
                for ii, p in enumerate(gzL):
                    self.__lfh.write("+testPurgeCandidateList- %r  gz - %r\n" % (ii, p))
            self.__lfh.write("%s\n" % "\n".join(self.__cTL))

        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def testVersionList(self):
        """"""
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        try:
            idList = self.__getIdList(self.__idListPath)
            dm = DataMaintenance(siteId=self.__siteId, testMode=self.__testMode, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                pL = dm.getVersionFileList(id, wfInstanceId=None, fileSource="archive", contentType="model", formatType="pdbx", partitionNumber="1", mileStone=None)
                self.__lfh.write("\n\n+testVersionList- id %s file list\n" % (id))
                for ii, p in enumerate(pL):
                    self.__lfh.write("+testVersionList- %r  %r\n" % (ii, p))
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()

    def __makeEntryPathList(self, archivePath):
        """Return the list of entries in the archive directory names and paths -"""
        pathList = []
        dataList = []
        for root, dirs, files in scandir.walk(archivePath, topdown=False):
            for dir in dirs:
                if dir.startswith("D_") and len(dir) == 12:
                    pathList.append(os.path.join(root, dir))
                    dataList.append(dir)
        return dataList, pathList

    def __splitFilePath(self, pth):
        id = None
        contentType = None
        fileFormat = None
        partNo = None
        versionNo = None
        try:
            dn, fn = os.path.split(pth)
            fFields = fn.split(".")
            fileName = fFields[0]
            fileFormat = fFields[1]
            if len(fFields) > 2:
                versionNo = int(fFields[2][1:])
            else:
                versionNo = int(0)

            fParts = fileName.split("_")
            if len(fParts) == 4:
                id = fParts[0] + "_" + fParts[1]
                contentType = fParts[2]
                partNo = int(fParts[3][1:])
            else:
                if len(fParts) > 2:
                    id = fParts[0] + "_" + fParts[1]
                else:
                    id = fileName
                if len(fParts) > 3:
                    contentType = fParts[2]
                else:
                    contentType = None
                partNo = None
            return id, contentType, fileFormat, partNo, versionNo
        except:
            traceback.print_exc(file=sys.stdout)
        return id, contentType, fileFormat, partNo, versionNo

    def testGetFileInventory(self):
        """"""
        self.__lfh.write("\nStarting %s %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name))
        archivePath = self.__cI.get("SITE_ARCHIVE_STORAGE_PATH")
        try:
            idList, pathList = self.__makeEntryPathList(archivePath)
            dm = DataMaintenance(siteId=self.__siteId, testMode=self.__testMode, verbose=self.__verbose, log=self.__lfh)
            for id in idList:
                dirPath = os.path.join(archivePath, "archive", id, "*")
                self.__lfh.write("+testGetFileInventoryList- inventory in directory  %s\n" % (dirPath))
                pL = dm.getMiscFileList(fPatternList=[dirPath], sortFlag=True)
                self.__lfh.write("\n\n+testGetFileInventoryList- id %s file list\n" % (id))
                for ii, p in enumerate(pL):
                    tup0 = self.__splitFilePath(p[0])
                    retR = [t for t in tup0]
                    retR.append(p[1])
                    retR.append(p[2])
                    self.__lfh.write("+testGetFileInventoryList- %r  %r\n" % (ii, retR))
        except:
            traceback.print_exc(file=sys.stdout)
            self.fail()


def suiteMiscTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataMaintenanceTests("testVersionList"))
    suiteSelect.addTest(DataMaintenanceTests("testPurgeCandidatesList"))
    return suiteSelect


def suiteProductionPurgeListTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataMaintenanceTests("testCreatePurgeProductionList"))
    return suiteSelect


def suiteProductionPurgeTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataMaintenanceTests("testPurgeProductionList"))
    return suiteSelect


def suiteRecoverProductionTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataMaintenanceTests("testRecoverProductionList"))
    return suiteSelect


def suiteGetFileInventoryTests():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(DataMaintenanceTests("testGetFileInventory"))
    return suiteSelect


if __name__ == "__main__":
    #
    if True:
        mySuite = suiteMiscTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteProductionPurgeListTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteProductionPurgeTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

        mySuite = suiteGetFileInventoryTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)

    if False:
        mySuite = suiteRecoverProductionTests()
        unittest.TextTestRunner(verbosity=2).run(mySuite)
