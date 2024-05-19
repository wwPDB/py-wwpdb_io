##
# File:  DataMaintenance.py
# Date:  13-Jun-2015
#
# Updates:
#    15-Jun-2015  jdw added some recover features
#    24-Oct-2016  jdw add test mode
#
##
"""
Collection of data maintenance utilities to support
purging data files for released entries.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.09"

import sys
import os
import shutil
import traceback
import glob
from datetime import datetime

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.io.locator.PathInfo import PathInfo


class DataMaintenance(object):

    """Collection of data maintenance utilities supporting
    purge and recovery of data files post release.

    This class duplicates some methods from class DataExchange for
    anticipated future use.

    """

    def __init__(self, siteId=None, testMode=False, verbose=False, log=sys.stderr):
        self.__verbose = verbose
        self.__lfh = log
        self.__siteId = siteId
        # In test mode no deletions are performed -
        self.__testMode = testMode
        self.__debug = False
        self.__sessionPath = None
        #
        self.__setup(siteId=siteId)

    def __setup(self, siteId=None):
        self.__siteId = siteId
        self.__cI = ConfigInfo(self.__siteId)
        self.__sessionPath = None
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)

    def setSessionPath(self, inputSessionPath=None):
        """Override the path to files with fileSource="session" """
        self.__sessionPath = inputSessionPath

    def purgeLogs(self, dataSetId):
        archivePath = self.__cI.get("SITE_ARCHIVE_STORAGE_PATH")
        dirPath = os.path.join(archivePath, "archive", dataSetId, "log")
        if self.__verbose:
            self.__lfh.write("+DataMaintenance.purgeLogs() - purging logs in directory  %s\n" % (dirPath))

        if os.access(dirPath, os.W_OK):
            fpattern = os.path.join(dirPath, "*log")
            if self.__verbose:
                self.__lfh.write("+DataMaintenance.purgeLogs() - purging pattern is %s\n" % (fpattern))

            pthList = glob.glob(fpattern)
            if self.__verbose:
                self.__lfh.write("+DataMaintenance.purgeLogs() candidate path length is %d\n" % len(pthList))
            #
            for pth in pthList:
                try:
                    if self.__testMode:
                        self.__lfh.write("+DataMaintenance.purgeLogs() TEST MODE skip remove %s\n" % pth)
                    else:
                        os.remove(pth)
                except:  # noqa: E722 pylint: disable=bare-except
                    pass
            #
        return pthList

    def reversePurge(self, dataSetId, contentType, formatType="pdbx", partitionNumber=1):
        fn = self.__getArchiveFileName(dataSetId, contentType=contentType, formatType=formatType, version="none", partitionNumber=partitionNumber)

        archivePath = self.__cI.get("SITE_ARCHIVE_STORAGE_PATH")
        dirPath = os.path.join(archivePath, "archive", dataSetId)
        if self.__verbose:
            self.__lfh.write("+DataMaintenance.__setup() - purging in directory  %s\n" % (dirPath))

        if len(dirPath) < 2:
            return []
        fpattern = os.path.join(dirPath, fn + ".V*")
        if self.__verbose:
            self.__lfh.write("+DataMaintenance.__setup() - purging pattern is %s\n" % (fpattern))

        pthList = glob.glob(fpattern)
        if self.__verbose:
            self.__lfh.write("+DataMaintenance.__reversePurge() candidate length is %d\n" % len(pthList))
        #
        fList = []
        for pth in pthList:
            if not pth.endswith(".V1"):
                fList.append(pth)

        for pth in fList:
            try:
                if self.__testMode:
                    self.__lfh.write("+DataMaintenance.reversePurge() TEST MODE skip remove %s\n" % pth)
                else:
                    os.remove(pth)
            except:  # noqa: E722 pylint: disable=bare-except
                pass
            #
        return fList

    def removeWorkflowDir(self, dataSetId):
        if (dataSetId is not None) and dataSetId.startswith("D_") and (len(dataSetId) > 10):
            workflowPath = self.__cI.get("SITE_ARCHIVE_STORAGE_PATH")
            dirPath = os.path.join(workflowPath, "workflow", dataSetId)
            if os.access(dirPath, os.W_OK):
                if self.__testMode:
                    self.__lfh.write("+DataMaintenance.removeWorkflowDir() TEST MODE skip remove %s\n" % dirPath)
                else:
                    shutil.rmtree(dirPath)
                return True
            else:
                return False
        else:
            return False

    def getLogFiles(self, dataSetId, fileSource="archive"):
        pL = []
        if fileSource in ["archive"]:
            dirPath = self.__pI.getArchivePath(dataSetId)
        elif fileSource in ["deposit"]:
            dirPath = self.__pI.getDepositPath(dataSetId)
        else:
            return pL
        fpattern = os.path.join(dirPath, "*.log")
        pthList = glob.glob(fpattern)
        return pthList

    def getPurgeCandidates(self, dataSetId, wfInstanceId=None, fileSource="archive", contentType="model", formatType="pdbx", partitionNumber="1", mileStone=None, purgeType="exp"):
        """Return the latest version, and candidates for removal and compression.

        purgeType = 'exp'    use strategy for experimental and model fileSource V<last>, V2, V1
                    'other'  use strategy for other file types -- V<last> & V1

        """
        latestV = None
        rmL = []
        gzL = []
        vtL = self.getVersionFileList(
            dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, contentType=contentType, formatType=formatType, partitionNumber=partitionNumber, mileStone=mileStone
        )
        n = len(vtL)
        if n > 0:
            latestV = vtL[0][0]
        if purgeType in ["exp"]:
            if n < 2:
                return latestV, rmL, gzL
            elif n == 2:
                gzL.append(vtL[1][0])
            elif n == 3:
                gzL.append(vtL[1][0])
                gzL.append(vtL[2][0])
            elif n > 3:
                gzL.append(vtL[n - 2][0])
                gzL.append(vtL[n - 1][0])
                for i in range(1, n - 2):
                    rmL.append(vtL[i][0])
            else:
                pass
        elif purgeType in ["report", "other"]:
            if n < 2:
                return latestV, rmL, gzL
            elif n == 2:
                gzL.append(vtL[1][0])
            elif n > 2:
                gzL.append(vtL[n - 1][0])
                for i in range(1, n - 1):
                    rmL.append(vtL[i][0])
            else:
                pass

        return latestV, rmL, gzL

    def getVersionFileListSnapshot(self, basePath, dataSetId, wfInstanceId=None, fileSource="archive", contentType="model", formatType="pdbx", partitionNumber="1", mileStone=None):
        """
        For the input content object return a list of file versions in a snapshot directory (recovery mode).

        Return:
              List of [(file path, modification date string,size),...]

        """
        pairL = []
        # basePath = '/net/wwpdb_da_data_archive/.snapshot/nightly.1/data'
        try:
            if fileSource == "archive":
                pth = self.__pI.getArchivePath(dataSetId)
                snPth = os.path.join(basePath, "archive", dataSetId)
            elif fileSource == "deposit":
                pth = self.__pI.getDepositPath(dataSetId)
                snPth = os.path.join(basePath, "deposit", dataSetId)
            else:
                pth = "."
                snPth = "."

            fPattern = self.__pI.getFilePathVersionTemplate(
                dataSetId=dataSetId,
                wfInstanceId=wfInstanceId,
                contentType=contentType,
                formatType=formatType,
                fileSource=fileSource,
                partNumber=partitionNumber,
                mileStone=mileStone,
            )
            _dir, fn = os.path.split(fPattern)
            altPattern = os.path.join(snPth, fn)
            srcL = self.__getFileListWithVersion([altPattern], sortFlag=True)
            for src in srcL:
                _d, f = os.path.split(src[0])
                dst = os.path.join(pth, f)
                if not os.access(dst, os.F_OK):
                    pairL.append((src[0], dst))

            return pairL

        except Exception as e:
            if self.__verbose:
                self.__lfh.write(
                    "+DataMaintenance.getVersionFileList() failing for data set %s instance %s file source %s err %s\n" % (dataSetId, wfInstanceId, fileSource, str(e))
                )
                traceback.print_exc(file=self.__lfh)
            return []

    ##

    def getVersionFileList(self, dataSetId, wfInstanceId=None, fileSource="archive", contentType="model", formatType="pdbx", partitionNumber="1", mileStone=None):
        """
        For the input content object return a list of file versions sorted by modification time.

        Return:
              List of [(file path, modification date string,size),...]

        """
        try:
            if fileSource == "session" and self.__sessionPath is not None:
                self.__pI.setSessionPath(self.__sessionPath)

            fPattern = self.__pI.getFilePathVersionTemplate(
                dataSetId=dataSetId,
                wfInstanceId=wfInstanceId,
                contentType=contentType,
                formatType=formatType,
                fileSource=fileSource,
                partNumber=partitionNumber,
                mileStone=mileStone,
            )
            return self.__getFileListWithVersion([fPattern], sortFlag=True)
        except Exception as e:
            if self.__verbose:
                self.__lfh.write(
                    "+DataMaintenance.getVersionFileList() failing for data set %s instance %s file source %s err %r\n" % (dataSetId, wfInstanceId, fileSource, str(e))
                )
                traceback.print_exc(file=self.__lfh)
            return []

    def getContentTypeFileList(self, dataSetId, wfInstanceId, fileSource="archive", contentTypeList=None):
        """
        For the input content object return a list of file versions sorted by modification time.

        Return:
              List of [(file path, modification date string,size),...]

        """
        if contentTypeList is None:
            contentTypeList = ["model"]
        try:
            if fileSource == "session" and self.__sessionPath is not None:
                self.__pI.setSessionPath(self.__sessionPath)
            fPatternList = []
            for contentType in contentTypeList:
                fPattern = self.__pI.getFilePathContentTypeTemplate(dataSetId=dataSetId, wfInstanceId=wfInstanceId, contentType=contentType, fileSource=fileSource)

                fPatternList.append(fPattern)
            if self.__debug:
                self.__lfh.write("+DataMaintenance.getContentTypeFileList() patterns %r\n" % fPatternList)
            return self.__getFileListWithVersion(fPatternList, sortFlag=True)
        except Exception as e:
            if self.__verbose:
                self.__lfh.write(
                    "+DataMaintenance.getVersionFileList() failing for data set %s instance %s file source %s error %r\n" % (dataSetId, wfInstanceId, fileSource, str(e))
                )
                traceback.print_exc(file=self.__lfh)
            return []

    def getMiscFileList(self, fPatternList=None, sortFlag=True):
        if fPatternList is None:
            fPatternList = ["*"]
        return self.__getFileList(fPatternList=fPatternList, sortFlag=sortFlag)

    def getLogFileList(self, entryId, fileSource="archive"):
        if fileSource in ["archive", "wf-archive"]:
            pth = self.__pI.getArchivePath(entryId)
            fpat1 = os.path.join(pth, "*log")
            fpat2 = os.path.join(pth, "log", "*")
            patList = [fpat1, fpat2]
        elif fileSource in ["deposit"]:
            pth = self.__pI.getDepositPath(entryId)
            fpat1 = os.path.join(pth, "*log")
            fpat2 = os.path.join(pth, "log", "*")
            patList = [fpat1, fpat2]
        else:
            return []
        return self.__getFileList(fPatternList=patList, sortFlag=True)

    def __getFileListWithVersion(self, fPatternList=None, sortFlag=False):
        """
        For the input glob compatible file pattern produce a file list sorted by modification date.

        If sortFlag is set then file list is sorted by modification date (e.g. recently changes first)

        Return:
              List of [(file path, modification date string, KBytes),...]

        """
        if fPatternList is None:
            fPatternList = ["*"]
        try:
            files = []
            for fPattern in fPatternList:
                if fPattern is not None and len(fPattern) > 0:
                    files.extend(filter(os.path.isfile, glob.glob(fPattern)))

            file_ver_tuple_list = []
            for f in files:
                tL = f.split(".")
                vId = tL[-1]
                if vId.startswith("V"):
                    if vId[-1] not in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                        file_ver_tuple_list.append((f, int(vId[1:-1])))
                    else:
                        file_ver_tuple_list.append((f, int(vId[1:])))

            # Sort the tuple list by version id
            #
            if sortFlag:
                file_ver_tuple_list.sort(key=lambda x: x[1], reverse=True)

            return file_ver_tuple_list
        except Exception as e:
            if self.__verbose:
                self.__lfh.write("+DataMaintenance.getVersionFileList() failing for pattern %r error %r\n" % (fPatternList, str(e)))
                traceback.print_exc(file=self.__lfh)
            return []

    def __getFileList(self, fPatternList=None, sortFlag=True):
        """
        For the input glob compatible file pattern produce a file list sorted by modification date.

        If sortFlag is set then file list is sorted by modification date (e.g. recently changes first)

        Return:
              List of [(file path, modification date string, KBytes),...]

        """
        if fPatternList is None:
            fPatternList = ["*"]
        try:
            files = []
            for fPattern in fPatternList:
                if fPattern is not None and len(fPattern) > 0:
                    files.extend(filter(os.path.isfile, glob.glob(fPattern)))

            file_date_tuple_list = []
            for x in files:
                d = os.path.getmtime(x)
                s = float(os.path.getsize(x)) / 1000.0
                file_date_tuple = (x, d, s)
                file_date_tuple_list.append(file_date_tuple)

            # Sort the tuple list by the modification time (recent changes first)
            if sortFlag:
                file_date_tuple_list.sort(key=lambda x: x[1], reverse=True)
            rTup = []
            for fP, mT, sZ in file_date_tuple_list:
                tS = datetime.fromtimestamp(mT).strftime("%Y-%b-%d %H:%M:%S")
                rTup.append((fP, tS, sZ))
            return rTup
        except Exception as e:
            if self.__verbose:
                self.__lfh.write("+DataMaintenance.getVersionFileList() failing for patter %r error %r\n" % (fPatternList, str(e)))
                traceback.print_exc(file=self.__lfh)
            return []

    ##
    def __getArchiveFileName(self, dataSetId, wfInstanceId=None, contentType="model", formatType="pdbx", version="latest", partitionNumber="1", mileStone=None):
        (_fp, _d, f) = self.__targetFilePath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource="archive",
            contentType=contentType,
            formatType=formatType,
            version=version,
            partitionNumber=partitionNumber,
            mileStone=mileStone,
        )
        return f

    # def __getInstanceFileName(self, dataSetId, wfInstanceId=None, contentType="model", formatType="pdbx", version="latest", partitionNumber="1", mileStone=None):
    #     (_fp, _d, f) = self.__targetFilePath(
    #         dataSetId=dataSetId,
    #         wfInstanceId=wfInstanceId,
    #         fileSource="wf-instance",
    #         contentType=contentType,
    #         formatType=formatType,
    #         version=version,
    #         partitionNumber=partitionNumber,
    #         mileStone=mileStone,
    #     )
    #     return f

    # def __getFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", contentType="model", formatType="pdbx", version="latest", partitionNumber="1", mileStone=None):
    #     (fp, _d, _f) = self.__targetFilePath(
    #         dataSetId=dataSetId,
    #         wfInstanceId=wfInstanceId,
    #         fileSource=fileSource,
    #         contentType=contentType,
    #         formatType=formatType,
    #         version=version,
    #         partitionNumber=partitionNumber,
    #         mileStone=mileStone,
    #     )
    #     return fp

    def __targetFilePath(self, dataSetId, wfInstanceId=None, fileSource="archive", contentType="model", formatType="pdbx", version="latest", partitionNumber="1", mileStone=None):
        """Return the file path, directory path, and filen ame  for the input content object if this object is valid.

        If the file path cannot be verified return None for all values
        """
        try:
            if fileSource == "session" and self.__sessionPath is not None:
                self.__pI.setSessionPath(self.__sessionPath)
            fP = self.__pI.getFilePath(
                dataSetId=dataSetId,
                wfInstanceId=wfInstanceId,
                contentType=contentType,
                formatType=formatType,
                fileSource=fileSource,
                versionId=version,
                partNumber=partitionNumber,
                mileStone=mileStone,
            )
            dN, fN = os.path.split(fP)
            return fP, dN, fN
        except Exception as e:
            if self.__debug:
                self.__lfh.write(
                    "+DataMaintenance.__targetFilePath() failing for data set %s instance %s file source %s error %r\n" % (dataSetId, wfInstanceId, fileSource, str(e))
                )
                traceback.print_exc(file=self.__lfh)

            return (None, None, None)

    # def __copyGzip(self, inpFilePath, outFilePath):
    #     """"""
    #     try:
    #         cmd = " gzip -cd  %s > %s " % (inpFilePath, outFilePath)
    #         os.system(cmd)
    #         return True
    #     except:  # noqa: E722 pylint: disable=bare-except
    #         if self.__verbose:
    #             traceback.print_exc(file=self.__lfh)
    #         return False
