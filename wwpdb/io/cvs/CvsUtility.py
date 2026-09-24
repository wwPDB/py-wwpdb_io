##
# File: CvsUtility.py
# Date: 09-April-2011  j. Westbrook
#
# Updates:
# 12-April-2011 jdw Revision checkout
##
"""
Wrapper class for opertations on cvs repositories.

Methods are provided to manage archiving of chemical component data files.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.001"


import logging
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional, Tuple


class CvsWrapper:
    """Wrapper class for opertations on cvs repositories."""

    def __init__(self, tmpPath: str = "./") -> None:
        self.__tmpPath = tmpPath
        self.__logger = logging.getLogger("wwpdb.utils.rcsb.CvsWrapper")
        self.__logger.debug("Created instance of CvsWrapper")
        #
        # self.__debug = True
        self.__repositoryHost: Optional[str] = None
        self.__repositoryPath: Optional[str] = None
        self.__cvsUser: Optional[str] = None
        self.__cvsPassword: Optional[str] = None
        self.__cvsRoot: Optional[str] = None
        #
        self.__wrkPath: Optional[str] = None
        self.__cvsInfoFileName = "cvsInfo.txt"
        self.__cvsErrorFileName = "cvsError.txt"

    def setRepositoryPath(self, host: Optional[str], path: Optional[str]) -> None:
        self.__repositoryHost = host
        self.__repositoryPath = path

    def setAuthInfo(self, user: Optional[str], password: Optional[str]) -> None:
        self.__cvsUser = user
        self.__cvsPassword = password

    def getHistory(self, cvsPath: str) -> str:
        text = ""
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            _ok = self.__runCvsCommand(myCommand=cmd)  # noqa: F841
            text = self.__getOutputText()

        return text

    def getRevisionList(self, cvsPath: str) -> List[Tuple[str, str, str]]:
        """Return a list of tuples containing the revision identifiers for the input file.

        Return data has the for [(RevId, A/M, timeStamp),...] where A=Added and M=Modified.
        """
        revList = []
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            _ok = self.__runCvsCommand(myCommand=cmd)  # noqa: F841
            revList = self.__extractRevisions()
        return revList

    def cleanup(self) -> None:  # Returns None on success or raises exception...
        """Cleanup temporary files and directories"""
        if self.__wrkPath is None:
            raise TypeError
        return shutil.rmtree(self.__wrkPath)

    def checkOutFile(self, cvsPath: str, outPath: str, revId: Optional[str] = None) -> str:
        text = ""
        (pth, fn) = os.path.split(cvsPath)
        self.__logger.debug("Cvs directory %s   target file name %s", pth, fn)
        if len(fn) > 0:
            cmd = self.__getCheckOutCmd(cvsPath, outPath, revId)
            if cmd is not None:
                _ok = self.__runCvsCommand(myCommand=cmd)  # noqa: F841
                text = self.__getErrorText()
        return text

    def __getHistoryCmd(self, cvsPath: str) -> Optional[str]:
        if self.__wrkPath is None:
            self.__makeTempWorkingDir()
        if self.__wrkPath is None:
            raise ValueError
        outPath = os.path.join(self.__wrkPath, self.__cvsInfoFileName)
        errPath = os.path.join(self.__wrkPath, self.__cvsErrorFileName)
        if self.__setCvsRoot():
            if self.__cvsRoot is None:
                raise TypeError
            cmd = "cvs -d " + self.__cvsRoot + " history -a -x AM " + cvsPath + self.__getRedirect(fileNameOut=outPath, fileNameErr=errPath)
        else:
            cmd = None
        return cmd

    def __getCheckOutCmd(self, cvsPath: str, outPath: str, revId: Optional[str] = None) -> Optional[str]:
        if self.__wrkPath is None:
            self.__makeTempWorkingDir()
        if self.__wrkPath is None:
            raise ValueError
        errPath = os.path.join(self.__wrkPath, self.__cvsErrorFileName)
        (pth, fn) = os.path.split(cvsPath)
        self.__logger.debug("CVS directory %s  target file name %s", pth, fn)
        lclPath = os.path.join(self.__wrkPath, fn)
        #
        #
        if self.__setCvsRoot():
            if self.__cvsRoot is None:
                raise ValueError
            if revId is None:
                rS = " "
                cmd = (
                    "cvs -d "
                    + self.__cvsRoot
                    + " co -d "
                    + self.__wrkPath
                    + " "
                    + cvsPath
                    + self.__getRedirect(fileNameOut=errPath, fileNameErr=errPath)
                    + " ; "
                    + " mv -f  "
                    + lclPath
                    + " "
                    + outPath
                    + self.__getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True)
                    + " ; "
                )
            else:
                rS = " -r " + revId + " "
                cmd = (
                    "cvs -d "
                    + self.__cvsRoot
                    + " co -d "
                    + self.__wrkPath
                    + rS
                    + " "
                    + cvsPath
                    + self.__getRedirect(fileNameOut=errPath, fileNameErr=errPath)
                    + " ; "
                    + " mv -f  "
                    + lclPath
                    + " "
                    + outPath
                    + self.__getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True)
                    + " ; "
                )
        else:
            cmd = None
        return cmd

    def __getRedirect(self, fileNameOut: str = "myLog.log", fileNameErr: str = "myLog.log", append: bool = False) -> str:
        if append:
            if fileNameOut == fileNameErr:
                oReDir = " >> " + fileNameOut + " 2>&1 "
            else:
                oReDir = " >> " + fileNameOut + " 2>> " + fileNameErr
        elif fileNameOut == fileNameErr:
            oReDir = " > " + fileNameOut + " 2>&1 "
        else:
            oReDir = " > " + fileNameOut + " 2> " + fileNameErr

        return oReDir

    def __runCvsCommand(self, myCommand: str) -> bool:
        retcode = -100
        try:
            self.__logger.debug("Command: %s", myCommand)

            # if (self.__debug):
            #    self.__lfh.write("+CvsWrapper(__runCvsCommand) command: %s\n" % myCommand)

            retcode = subprocess.call(myCommand, shell=True)  # noqa: S602
            if retcode < 0:
                self.__logger.debug("Child was terminated by signal %r", retcode)
                # if self.__verbose:
                #    self.__lfh.write("+CvsWrapper(__runCvsCommand) Child was terminated by signal %r\n" % retcode)
                return False
            self.__logger.debug("Child was terminated by signal %r", retcode)
            # if self.__verbose:
            #    self.__lfh.write("+CvsWrapper(__runCvsCommand) Child was terminated by signal %r\n" % retcode)
            return True
        except OSError as e:
            self.__logger.exception("cvs command exception: %r %r", retcode, str(e))
            # if self.__verbose:
            #    self.__lfh.write("+CvsWrapper(__runCvsCommand) Execution failed: %r\n" % e)
            return False

    def __setCvsRoot(self) -> bool:
        try:
            self.__cvsRoot = ":pserver:" + self.__cvsUser + ":" + self.__cvsPassword + "@" + self.__repositoryHost + ":" + self.__repositoryPath  # type: ignore
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def __extractRevisions(self) -> List[Tuple[str, str, str]]:
        """Extract revisions details from the last history command."""
        revList = []
        try:
            fName = os.path.join(self.__wrkPath, self.__cvsInfoFileName)  # type: ignore
            self.__logger.debug("Reading revisions from %r", fName)
            ifh = open(fName)
            for line in ifh:
                fields = line[:-1].split()
                typeCode = str(fields[0])
                revId = str(fields[5])
                timeStamp = str(fields[1] + ":" + fields[2])
                revList.append((revId, typeCode, timeStamp))
        except:  # noqa: E722 pylint: disable=bare-except
            self.__logger.exception("Extracting revision list for : %s", fName)

        revList.reverse()
        self.__logger.debug("Ordered revision list %r", revList)

        return revList

    def __getOutputText(self) -> str:
        text = ""
        try:
            fPath = os.path.join(self.__wrkPath, self.__cvsInfoFileName)  # type: ignore
            ifh = open(fPath)
            text = ifh.read()
        except:  # noqa: E722 pylint: disable=bare-except
            self.__logger.exception("Execption reading cvs output file: %s", fPath)

        return text

    def __getErrorText(self) -> str:
        text = ""
        try:
            fName = os.path.join(self.__wrkPath, self.__cvsErrorFileName)  # type: ignore
            ifh = open(fName)
            text = ifh.read()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        return text

    def __makeTempWorkingDir(self) -> None:
        if self.__tmpPath is not None and os.path.isdir(self.__tmpPath):
            self.__wrkPath = tempfile.mkdtemp("tmpdir", "rcsbCVS", self.__tmpPath)
        else:
            self.__wrkPath = tempfile.mkdtemp("tmpdir", "rcsbCVS")
        self.__logger.debug("Working directory path set to  %r", self.__wrkPath)
