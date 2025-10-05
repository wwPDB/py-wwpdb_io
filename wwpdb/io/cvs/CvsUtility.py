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

from __future__ import annotations

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


class CvsWrapper:
    """Wrapper class for opertations on cvs repositories."""

    def __init__(self, tmpPath: str = "./") -> None:
        self.__tmpPath = tmpPath
        self.__logger = logging.getLogger("wwpdb.utils.rcsb.CvsWrapper")
        self.__logger.debug("Created instance of CvsWrapper")
        #
        # self.__debug = True
        self.__repositoryHost: str | None = None
        self.__repositoryPath: str | None = None
        self.__cvsUser: str | None = None
        self.__cvsPassword: str | None = None
        self.__cvsRoot: str | None = None
        #
        self.__wrkPath: str | None = None
        self.__cvsInfoFileName = "cvsInfo.txt"
        self.__cvsErrorFileName = "cvsError.txt"

    def setRepositoryPath(self, host: str | None, path: str | None) -> None:
        self.__repositoryHost = host
        self.__repositoryPath = path

    def setAuthInfo(self, user: str | None, password: str | None) -> None:
        self.__cvsUser = user
        self.__cvsPassword = password

    def getHistory(self, cvsPath: str) -> str:
        text = ""
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            _ok = self.__runCvsCommand(myCommand=cmd)  # noqa: F841
            text = self.__getOutputText()

        return text

    def getRevisionList(self, cvsPath: str) -> list[tuple[str, str, str]]:
        """Return a list of tuples containing the revision identifiers for the input file.

        Return data has the for [(RevId, A/M, timeStamp),...] where A=Added and M=Modified.
        """
        revList = []
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            _ok = self.__runCvsCommand(myCommand=cmd)  # noqa: F841
            revList = self.__extractRevisions()
        return revList

    def cleanup(self) -> None:
        """Cleanup temporary files and directories"""
        if self.__wrkPath is None:
            raise ValueError
        return shutil.rmtree(self.__wrkPath)

    def checkOutFile(self, cvsPath: str, outPath: str, revId: str | None = None) -> str:
        text = ""
        (pth, fn) = os.path.split(cvsPath)
        self.__logger.debug("Cvs directory %s   target file name %s", pth, fn)
        if len(fn) > 0:
            cmd = self.__getCheckOutCmd(cvsPath, outPath, revId)
            if cmd is not None:
                _ok = self.__runCvsCommand(myCommand=cmd)  # noqa: F841
                text = self.__getErrorText()
        else:
            pass
        return text

    def __getHistoryCmd(self, cvsPath: str) -> str | None:
        if self.__wrkPath is None:
            self.__makeTempWorkingDir()
            # sets self.__wrkPath
        if self.__wrkPath is None:
            raise ValueError
        outPath = os.path.join(self.__wrkPath, self.__cvsInfoFileName)
        errPath = os.path.join(self.__wrkPath, self.__cvsErrorFileName)
        if self.__setCvsRoot():
            # Should never happen
            if self.__cvsRoot is None:
                raise ValueError
            cmd = "cvs -d " + self.__cvsRoot + " history -a -x AM " + cvsPath + self.__getRedirect(fileNameOut=outPath, fileNameErr=errPath)
        else:
            cmd = None
        return cmd

    def __getCheckOutCmd(self, cvsPath: str, outPath: str, revId: str | None = None) -> str | None:
        if self.__wrkPath is None:
            self.__makeTempWorkingDir()
            # sets self.__wrkPath
        if self.__wrkPath is None:
            raise ValueError
        errPath = os.path.join(self.__wrkPath, self.__cvsErrorFileName)
        (pth, fn) = os.path.split(cvsPath)
        self.__logger.debug("CVS directory %s  target file name %s", pth, fn)
        lclPath = os.path.join(self.__wrkPath, fn)
        #
        #
        if self.__setCvsRoot():
            # Should be set..
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
            if self.__cvsUser is None or self.__cvsPassword is None or self.__repositoryHost is None or self.__repositoryPath is None:
                return False
            self.__cvsRoot = ":pserver:" + self.__cvsUser + ":" + self.__cvsPassword + "@" + self.__repositoryHost + ":" + self.__repositoryPath
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def __extractRevisions(self) -> list[tuple[str, str, str]]:
        """Extract revisions details from the last history command."""
        revList: list[tuple[str, str, str]] = []
        try:
            if self.__wrkPath is None or self.__cvsInfoFileName is None:
                self.__logger.exception("Extracting revision list - missing wrkPath or cvsInfoFileName")
                return revList
            fName = os.path.join(self.__wrkPath, self.__cvsInfoFileName)
            self.__logger.debug("Reading revisions from %r", fName)
            ifh = open(fName)
            for line in ifh.readlines():  # noqa: FURB129
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
        if self.__wrkPath is None or self.__cvsInfoFileName is None:
            self.__logger.exception("Execption reading cvs output file: __wrkPath %s _cvsInfoFileName %s", self.__wrkPath, self.__cvsInfoFileName)
            return text
        try:
            fPath = os.path.join(self.__wrkPath, self.__cvsInfoFileName)
            ifh = open(fPath)
            text = ifh.read()
        except:  # noqa: E722 pylint: disable=bare-except
            self.__logger.exception("Execption reading cvs output file: %s", fPath)

        return text

    def __getErrorText(self) -> str:
        text = ""
        if self.__wrkPath is None:
            return text
        try:
            fName = os.path.join(self.__wrkPath, self.__cvsErrorFileName)
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
