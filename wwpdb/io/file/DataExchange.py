##
# File:  DataExchange.py
# Date:  19-Sep-2012
#
# Updates:
#
#  28-Feb-2013 jdw incorporate PathInfo() class
#  05-Mar-2013 jdw fetch() should not strip version information for output files.
#  08-Mar-2013 jdw add method to separately set path for 'session' storage.
#  29-Jun-2014 jdw refactor add getVersionFileList() and getPartitionFileList()
#   5-Jul-2014 jdw  getContentTypeFileList() and getMiscFileList()
#   5-Jan-2015 jdw add siteId as an optional argument to the constructor -
#  16-Feb-2017 jdw add setFileSource() method ...
##
"""
 Implements common data exchange operations including: moving annotation data files between session
and workflow storage, accessing files in workflow directories,  and routine file maintenance operations.

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


class DataExchange(object):

    """
     Implements common data exchange operations
     including: moving annotation data files between session
     and workflow storage, accessing files in workflow directories,
     and routine file maintenance operations.

    """

    def __init__(self, reqObj=None, depDataSetId=None, wfInstanceId=None, fileSource="archive", siteId=None, verbose=False, log=sys.stderr):

        self.__reqObj = reqObj
        self.__depDataSetId = depDataSetId
        self.__wfInstanceId = wfInstanceId
        self.__fileSource = fileSource
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__debug = False
        self.__inputSessionPath = None
        #
        self.__setup(siteId=siteId)

    def __setup(self, siteId=None):
        if siteId is not None:
            self.__siteId = siteId
        else:
            self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")

        self.__sessionObj = self.__reqObj.getSessionObj()
        self.__sessionPath = self.__sessionObj.getPath()

        self.__cI = ConfigInfo(self.__siteId)
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)

        #
        if self.__debug:
            self.__lfh.write("+DataExchange.__setup() - session id   %s\n" % (self.__sessionObj.getId()))
            self.__lfh.write("+DataExchange.__setup() - session path %s\n" % (self.__sessionObj.getPath()))

            self.__lfh.write("+DataExchange.__setup() - data set %s  instance %s file source %s\n" % (self.__depDataSetId, self.__wfInstanceId, self.__fileSource))
            self.__pI.setDebugFlag(flag=self.__debug)

    def setFileSource(self, fileSource):
        """  Override fileSource="archive"
        """
        self.__fileSource = fileSource

    def setInputSessionPath(self, inputSessionPath=None):
        """  Override the path to files with fileSource="session"
        """
        self.__inputSessionPath = inputSessionPath

    def purgeLogs(self):
        archivePath = self.__cI.get("SITE_ARCHIVE_STORAGE_PATH")
        dirPath = os.path.join(archivePath, "archive", self.__depDataSetId, "log")
        if self.__verbose:
            self.__lfh.write("+DataExchange.purgeLogs() - purging logs in directory  %s\n" % (dirPath))

        if os.access(dirPath, os.W_OK):
            fpattern = os.path.join(dirPath, "*log")
            if self.__verbose:
                self.__lfh.write("+DataExchange.purgeLogs() - purging pattern is %s\n" % (fpattern))

            pthList = glob.glob(fpattern)
            if self.__verbose:
                self.__lfh.write("+DataExchange.purgeLogs() candidate path length is %d\n" % len(pthList))
            #
            for pth in pthList:
                try:
                    os.remove(pth)
                except:  # noqa: E722 pylint: disable=bare-except
                    pass
            #
        return pthList

    def reversePurge(self, contentType, formatType="pdbx", partitionNumber=1):
        fn = self.__getArchiveFileName(contentType=contentType, formatType=formatType, version="none", partitionNumber=partitionNumber)

        archivePath = self.__cI.get("SITE_ARCHIVE_STORAGE_PATH")
        dirPath = os.path.join(archivePath, "archive", self.__depDataSetId)
        if self.__verbose:
            self.__lfh.write("+DataExchange.__setup() - purging in directory  %s\n" % (dirPath))

        if len(dirPath) < 2:
            return []
        fpattern = os.path.join(dirPath, fn + ".V*")
        if self.__verbose:
            self.__lfh.write("+DataExchange.__setup() - purging pattern is %s\n" % (fpattern))

        pthList = glob.glob(fpattern)
        if self.__verbose:
            self.__lfh.write("+DataExchange.__reversePurge() candidate length is %d\n" % len(pthList))
        #
        fList = []
        for pth in pthList:
            if not pth.endswith(".V1"):
                fList.append(pth)

        for pth in fList:
            try:
                os.remove(pth)
            except:  # noqa: E722 pylint: disable=bare-except
                pass
            #
        return fList

    def removeWorkflowDir(self):
        if (self.__depDataSetId is not None) and self.__depDataSetId.startswith("D_") and (len(self.__depDataSetId) > 7):
            workflowPath = self.__cI.get("SITE_WORKFLOW_STORAGE_PATH")
            dirPath = os.path.join(workflowPath, "workflow", self.__depDataSetId)
            if os.access(dirPath, os.W_OK):
                shutil.rmtree(dirPath)
                return True
            else:
                return False
        else:
            return False

    def createArchiveDir(self, purgeFlag=True):
        """ Create new the archive directory if this is needed.

        """

        if self.__verbose:
            self.__lfh.write("+DataExchange.export() creating archive directory for data set %s\n" % self.__depDataSetId)

        try:
            archivePath = self.__cI.get("SITE_ARCHIVE_STORAGE_PATH")
            dirPath = os.path.join(archivePath, "archive", self.__depDataSetId)

            if not os.access(dirPath, os.W_OK):
                if self.__verbose:
                    self.__lfh.write("+DataExchange.createArchiveDir() creating archive directory path %s\n" % dirPath)
                os.makedirs(dirPath)
                return True
            else:
                if purgeFlag:
                    if self.__verbose:
                        self.__lfh.write("+DataExchange.export() existing archive directory path purged: %s\n" % dirPath)
                    shutil.rmtree(dirPath)
                    os.makedirs(dirPath)
                    return True
                else:
                    if self.__verbose:
                        self.__lfh.write("+DataExchange.export() archive directory exists: %s\n" % dirPath)
                    return False
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False

    def fetch(self, contentType, formatType, version="latest", partitionNumber=1):
        """ Copy the input content object into the current session directory (session naming semantics follow source file object)

            Return the full path of the copied file or None

        """
        inpFilePath = self.__getFilePath(fileSource=self.__fileSource, contentType=contentType, formatType=formatType, version=version, partitionNumber=partitionNumber)
        if self.__verbose:
            self.__lfh.write("+DataExchange.fetch() source type %s format %s version %s path %s\n" % (contentType, formatType, version, inpFilePath))

        try:
            if os.access(inpFilePath, os.R_OK):
                (_dirPath, fileName) = os.path.split(inpFilePath)
                # trim of the trailing version -
                # lastIdx=tfileName.rfind(".V")
                # if lastIdx > 0:
                #    fileName=tfileName[:lastIdx]
                # else:
                #    fileName=tfileName
                outFilePath = os.path.join(self.__sessionPath, fileName)
                if self.__verbose:
                    self.__lfh.write("+DataExchange.fetch() destination file path %s\n" % outFilePath)
                shutil.copyfile(inpFilePath, outFilePath)
                return outFilePath
            else:
                if self.__verbose:
                    self.__lfh.write("+DataExchange.fetch() missing input file at path %s\n" % inpFilePath)
                return None
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return None

    def export(self, inpFilePath, contentType, formatType, version="latest", partitionNumber=1):
        """ Copy input file to workflow instance or archival storage.

            Return True on success or False otherwise.

        """
        outFilePath = self.__getFilePath(fileSource=self.__fileSource, contentType=contentType, formatType=formatType, version=version, partitionNumber=partitionNumber)
        if self.__verbose:
            self.__lfh.write("+DataExchange.export() destination type %s format %s version %s path %s\n" % (contentType, formatType, version, outFilePath))

        try:
            if os.access(inpFilePath, os.R_OK) and (os.path.getsize(inpFilePath) > 0):
                if self.__verbose:
                    self.__lfh.write("+DataExchange.export() destination file path %s\n" % outFilePath)
                if inpFilePath.endswith(".gz"):
                    self.__copyGzip(inpFilePath, outFilePath)
                else:
                    shutil.copyfile(inpFilePath, outFilePath)
                return True
            else:
                if self.__verbose:
                    self.__lfh.write("+DataExchange.export() missing or zero length input file at path %s\n" % inpFilePath)
                return False
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False

    def __copyGzip(self, inpFilePath, outFilePath):
        """
        """
        try:
            cmd = " gzip -cd  %s > %s " % (inpFilePath, outFilePath)
            os.system(cmd)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return False

    def copyDirToSession(self, dirName):
        """  Replicate the input diretory in the session directory -
        """
        try:
            if self.__fileSource in ["archive", "wf-archive"]:
                pth = self.__pI.getArchivePath(self.__depDataSetId)
            elif self.__fileSource in ["deposit"]:
                pth = self.__pI.getDepositPath(self.__depDataSetId)
            elif self.__fileSource in ["wf-instance"]:
                pth = self.__pI.getInstancePath(self.__depDataSetId, self.__wfInstanceId)
            else:
                return False

            srcPath = os.path.join(pth, dirName)
            if not os.access(srcPath, os.R_OK):
                return False

            dstPath = os.path.join(self.__sessionPath, dirName)
            if not os.path.isdir(dstPath):
                os.makedirs(dstPath, 0o755)
            #
            fPattern = os.path.join(srcPath, "*")
            fpL = filter(os.path.isfile, glob.glob(fPattern))
            for fp in fpL:
                _dN, fN = os.path.split(fp)
                oP = os.path.join(dstPath, fN)
                shutil.copyfile(fp, oP)

            if self.__verbose:
                self.__lfh.write("+DataExchange.copyDirToSession() successful session copy of dirName %s\n" % (dirName))
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                self.__lfh.write("+DataExchange.copyDirToSession() fails for dirName %s\n" % (dirName))
                traceback.print_exc(file=self.__lfh)
            return False

        return True

    def copyToSession(self, contentType, formatType, version="latest", partitionNumber=1):
        """ Copy the input content object into the session directory using archive naming conventions less version details.

            Return the full path of the session file or None

        """
        inpFilePath = self.__getFilePath(fileSource=self.__fileSource, contentType=contentType, formatType=formatType, version=version, partitionNumber=partitionNumber)
        if self.__debug:
            self.__lfh.write("+DataExchange.copyToSession() source file type %s format %s version %s path %s\n" % (contentType, formatType, version, inpFilePath))

        try:
            outFilePath = None
            if os.access(inpFilePath, os.R_OK):
                fn = self.__getArchiveFileName(contentType, formatType, version="none", partitionNumber=partitionNumber)
                outFilePath = os.path.join(self.__sessionPath, fn)
                if self.__verbose:
                    self.__lfh.write("+DataExchange.copyToSession() content type %s format %s copied to session path %s\n" % (contentType, formatType, outFilePath))
                shutil.copyfile(inpFilePath, outFilePath)
                return outFilePath
            else:
                if self.__debug:
                    self.__lfh.write("+DataExchange.copyToSession() missing input file at path %s\n" % inpFilePath)
                return None
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                if self.__verbose:
                    self.__lfh.write("+DataExchange.copyToSession() Failing for content type %s format %s with session path %s\n" % (contentType, formatType, outFilePath))
                traceback.print_exc(file=self.__lfh)
            return None

    def updateArchiveFromSession(self, contentType, formatType, version="next", partitionNumber=1):
        """ Copy the input content object from the session directory stored using  archive naming conventions less version details
            to archive storage.

            Return the full path of the archive file or None

        """
        fn = self.__getArchiveFileName(contentType, formatType, version="none", partitionNumber=partitionNumber)
        inpFilePath = os.path.join(self.__sessionPath, fn)
        if self.__verbose:
            self.__lfh.write("+DataExchange.updateArchiveDromSession() source file type %s format %s path %s\n" % (contentType, formatType, inpFilePath))

        try:
            if os.access(inpFilePath, os.R_OK):
                outFilePath = self.__getFilePath(fileSource="archive", contentType=contentType, formatType=formatType, version=version, partitionNumber=partitionNumber)
                if self.__verbose:
                    self.__lfh.write("+DataExchange.updateArchiveFromSession() archive destination file path %s\n" % outFilePath)
                shutil.copyfile(inpFilePath, outFilePath)
                return outFilePath
            else:
                if self.__verbose:
                    self.__lfh.write("+DataExchange.updateArchiveFrom() missing session input file at path %s\n" % inpFilePath)
                return None
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
            return None

    ##
    def getVersionFileList(self, fileSource="archive", contentType="model", formatType="pdbx", partitionNumber="1", mileStone=None):
        """
        For the input content object return a list of file versions sorted by modification time.

        Return:
              List of [(file path, modification date string,size),...]

        """
        try:
            if fileSource == "session" and self.__inputSessionPath is not None:
                self.__pI.setSessionPath(self.__inputSessionPath)

            fPattern = self.__pI.getFilePathVersionTemplate(
                dataSetId=self.__depDataSetId,
                wfInstanceId=self.__wfInstanceId,
                contentType=contentType,
                formatType=formatType,
                fileSource=fileSource,
                partNumber=partitionNumber,
                mileStone=mileStone,
            )
            return self.__getFileList([fPattern], sortFlag=True)
        except Exception as e:
            if self.__verbose:
                self.__lfh.write(
                    "+DataExchange.getVersionFileList() failing for data set %s instance %s file source %s error %r\n"
                    % (self.__depDataSetId, self.__wfInstanceId, self.__fileSource, str(e))
                )
                traceback.print_exc(file=self.__lfh)
            return []

    def getPartitionFileList(self, fileSource="archive", contentType="model", formatType="pdbx", mileStone=None):
        """
        For the input content object return a list of file partitions sorted by modification time.

        Return:
              List of [(file path, modification date string,size),...]

        """
        try:
            if fileSource == "session" and self.__inputSessionPath is not None:
                self.__pI.setSessionPath(self.__inputSessionPath)

            fPattern = self.__pI.getFilePathPartitionTemplate(
                dataSetId=self.__depDataSetId, wfInstanceId=self.__wfInstanceId, contentType=contentType, formatType=formatType, fileSource=fileSource, mileStone=mileStone
            )
            tL = self.__getFileList([fPattern], sortFlag=True)
            if self.__debug:
                self.__lfh.write("+DataExchange.getPartionFileList() pattern %r\n" % fPattern)
                self.__lfh.write("+DataExchange.getPartionFileList() file list %r\n" % tL)
            #
            return tL
        except Exception as e:
            if self.__verbose:
                self.__lfh.write(
                    "+DataExchange.getVersionFileList() failing for data set %s instance %s file source %s error %r\n"
                    % (self.__depDataSetId, self.__wfInstanceId, self.__fileSource, str(e))
                )
                traceback.print_exc(file=self.__lfh)
            return []

    def getContentTypeFileList(self, fileSource="archive", contentTypeList=None):
        """
        For the input content object return a list of file versions sorted by modification time.

        Return:
              List of [(file path, modification date string,size),...]

        """
        if contentTypeList is None:
            contentTypeList = ["model"]
        try:
            if fileSource == "session" and self.__inputSessionPath is not None:
                self.__pI.setSessionPath(self.__inputSessionPath)
            fPatternList = []
            for contentType in contentTypeList:
                fPattern = self.__pI.getFilePathContentTypeTemplate(dataSetId=self.__depDataSetId, wfInstanceId=self.__wfInstanceId, contentType=contentType, fileSource=fileSource)

                fPatternList.append(fPattern)
            if self.__debug:
                self.__lfh.write("+DataExchange.getContentTypeFileList() patterns %r\n" % fPatternList)
            return self.__getFileList(fPatternList, sortFlag=True)
        except Exception as e:
            if self.__verbose:
                self.__lfh.write(
                    "+DataExchange.getVersionFileList() failing for data set %s instance %s file source %s error %r\n"
                    % (self.__depDataSetId, self.__wfInstanceId, self.__fileSource, str(e))
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

    def __getFileList(self, fPatternList=None, sortFlag=True):
        """
        For the input glob compatible file pattern produce a file list sorted by modification date.

        If sortFlag is set then file list is sorted by modification date (e.g. recently changes first)

        Return:
              List of [(file path, modification date string, KBytes),...]

        """
        if fPatternList is None:
            fPatternList = ["*"]
        rTup = []
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

            for fP, mT, sZ in file_date_tuple_list:
                tS = datetime.fromtimestamp(mT).strftime("%Y-%b-%d %H:%M:%S")
                rTup.append((fP, tS, sZ))
            return rTup
        except Exception as e:
            if self.__verbose:
                self.__lfh.write("+DataExchange.__getFileList() failing for patternlist %r error %r\n" % (fPatternList, str(e)))
                traceback.print_exc(file=self.__lfh)
        return rTup

    ##
    def __getArchiveFileName(self, contentType="model", formatType="pdbx", version="latest", partitionNumber="1", mileStone=None):
        (_fp, _d, f) = self.__targetFilePath(
            fileSource="archive", contentType=contentType, formatType=formatType, version=version, partitionNumber=partitionNumber, mileStone=mileStone
        )
        return f

    def __getInstanceFileName(self, contentType="model", formatType="pdbx", version="latest", partitionNumber="1", mileStone=None):
        (_fp, _d, f) = self.__targetFilePath(
            fileSource="wf-instance", contentType=contentType, formatType=formatType, version=version, partitionNumber=partitionNumber, mileStone=mileStone
        )
        return f

    def __getFilePath(self, fileSource="archive", contentType="model", formatType="pdbx", version="latest", partitionNumber="1", mileStone=None):
        (fp, _d, _f) = self.__targetFilePath(
            fileSource=fileSource, contentType=contentType, formatType=formatType, version=version, partitionNumber=partitionNumber, mileStone=mileStone
        )
        return fp

    def __targetFilePath(self, fileSource="archive", contentType="model", formatType="pdbx", version="latest", partitionNumber="1", mileStone=None):
        """ Return the file path, directory path, and filename  for the input content object if this object is valid.

            If the file path cannot be verified return None for all values
        """
        try:
            if fileSource == "session" and self.__inputSessionPath is not None:
                self.__pI.setSessionPath(self.__inputSessionPath)
            fP = self.__pI.getFilePath(
                dataSetId=self.__depDataSetId,
                wfInstanceId=self.__wfInstanceId,
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
                    "+DataExchange.__targetFilePath() failing for data set %s instance %s file source %s error %r\n"
                    % (self.__depDataSetId, self.__wfInstanceId, self.__fileSource, str(e))
                )
                traceback.print_exc(file=self.__lfh)

            return (None, None, None)
