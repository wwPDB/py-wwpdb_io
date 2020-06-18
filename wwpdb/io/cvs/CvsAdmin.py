##
# File: CvsAdmin.py
# Orig: 09-April-2011  j. Westbrook
#
# Updates:
# 12-April-2011 jdw Revision checkout
# 27-Nov-2012   jdw Rename as CvsAdmin() and change logging to wwPDB style
# 27-Nov-2012   jdw Add update and commit operations
# 29-Nov-2012   jdw Refactor to separate operations for maintaining a working
#                   copy of a project (cvs sandbox) and operations
#                   which are independent of a working copy.
#  3-Dec-2012   jdw Add separate commit operations.
# 27-Jan-2013   jdw Provide return status and message text as returns for public methods
#                   in CvsSandBoxAdmin().
# 28-Jan-2013   jdw change __getCheckOutCmd() to avoid absolute path with 'co -d path'
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


import sys
import os
import subprocess
import traceback
import tempfile
import shutil


class CvsWrapperBase(object):
    """Core wrapper class for opertations on cvs administrative operations on repositories.

    """

    def __init__(self, tmpPath="./", verbose=True, log=sys.stderr):
        self.__tmpPath = tmpPath
        #
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False

        self._repositoryHost = None
        self._repositoryPath = None
        self._cvsUser = None
        self._cvsPassword = None
        self._cvsRoot = None
        #
        self._wrkPath = None
        self._cvsInfoFileName = "cvsInfo.txt"
        self._cvsErrorFileName = "cvsError.txt"
        self.__outputFilePath = None
        self.__errorFilePath = None

    def setRepositoryPath(self, host, path):
        self._repositoryHost = host
        self._repositoryPath = path

    def setAuthInfo(self, user, password):
        self._cvsUser = user
        self._cvsPassword = password

    def _getRedirect(self, fileNameOut="myLog.log", fileNameErr="myLog.log", append=False):
        if append:
            if fileNameOut == fileNameErr:
                oReDir = " >> " + fileNameOut + " 2>&1 "
            else:
                oReDir = " >> " + fileNameOut + " 2>> " + fileNameErr
        else:
            if fileNameOut == fileNameErr:
                oReDir = " > " + fileNameOut + " 2>&1 "
            else:
                oReDir = " > " + fileNameOut + " 2> " + fileNameErr

        return oReDir

    def _runCvsCommand(self, myCommand):
        retcode = -100
        try:
            if self.__debug:
                self.__lfh.write("+CvsWrapperBase._runCvsCommand Command: %s\n" % myCommand)

            # retcode = subprocess.call(myCommand, stdout=self.__lfh, stderr=self.__lfh, shell=True)
            retcode = subprocess.call(myCommand, shell=True)
            if retcode != 0:
                if self.__verbose:
                    self.__lfh.write("+CvsWrapperBase.(_runCvsCommand)  Failed command: %s\n" % myCommand)
                    self.__lfh.write("+CvsWrapperBase(_runCvsCommand) Child was terminated by signal %r\n" % retcode)
                return False
            else:
                if self.__verbose:
                    self.__lfh.write("+CvsWrapperBase(_runCvsCommand) Child was terminated by signal %r\n" % retcode)
                return True
        except OSError as e:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
                self.__lfh.write("+CvsWrapperBase(_runCvsCommand) Execution failed: %r\n" % e)
            return False

    def _setCvsRoot(self):
        try:
            self._cvsRoot = ":pserver:" + self._cvsUser + ":" + self._cvsPassword + "@" + self._repositoryHost + ":" + self._repositoryPath
            return True
        except Exception as e:
            self.__lfh.write("+CvsWrapperBase(_cvsRoot) failed")
            self.__lfh.write(e)
            return False

    def _getOutputFilePath(self):
        self.__outputFilePath = os.path.join(self._wrkPath, self._cvsInfoFileName)
        return self.__outputFilePath

    def _getErrorFilePath(self):
        self.__errorFilePath = os.path.join(self._wrkPath, self._cvsErrorFileName)
        return self.__errorFilePath

    def _getOutputText(self):
        text = ""
        try:
            filePath = self.__outputFilePath
            return self.__getTextFile(filePath)
        except Exception as e:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
                self.__lfh.write("+CvsWrapperBase(_getOutputText) path %r %r\n" % (self.__outputFilePath, str(e)))

        return text

    def _getErrorText(self, filterInfo=False):
        text = ""
        try:
            filePath = self.__errorFilePath
            text = self.__getTextFile(filePath, filterInfo=filterInfo)
            if self.__verbose:
                self.__lfh.write("+CvsWrapperBase(_getErrorText) path: %r  text: %s\n" % (filePath, text))
                self.__lfh.flush()
        except Exception as e:
            if self.__verbose:
                traceback.print_exc(file=self.__lfh)
                self.__lfh.write("+CvsWrapperBase(_getErrorText) path %r %r\n" % (self.__errorFilePath, str(e)))
                self.__lfh.flush()

        return text

    def __getTextFile(self, filePath, filterInfo=False):  # pylint: disable=unused-argument
        text = ""
        try:
            ifh = open(filePath, "r")
            tL = []
            for line in ifh:
                if line.startswith("?"):
                    continue
                if len(str(line[:-1]).strip()) > 0:
                    tL.append(line[:-1])
            ifh.close()
            text = "\n".join(set(tL))
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        return text

    def _makeTempWorkingDir(self):
        if self.__tmpPath is not None and os.path.isdir(self.__tmpPath):
            self._wrkPath = os.path.abspath(tempfile.mkdtemp("tmpdir", "tmpCVS", self.__tmpPath))

        else:
            self._wrkPath = os.path.abspath(tempfile.mkdtemp("tmpdir", "tmpCVS"))

        if self.__debug:
            self.__lfh.write("+CvsWrapperBase(_makeTempWorkingDir) Working directory path set to  %r\n" % self._wrkPath)

    def cleanup(self):
        """Cleanup any temporary files and directories created by this class.
        """
        if self._wrkPath is not None and len(self._wrkPath) > 0:
            try:
                shutil.rmtree(self._wrkPath)
                return True
            except Exception as e:
                self.__lfh.write("cleanup - unable to remove self._wrkpath")
                self.__lfh.write(e)
                return False
        else:
            return True


class CvsAdmin(CvsWrapperBase):
    """Wrapper class for opertations on cvs administrative operations on repositories.
    """

    def __init__(self, tmpPath="./", verbose=True, log=sys.stderr):
        super(CvsAdmin, self).__init__(tmpPath=tmpPath, verbose=verbose, log=log)
        self.__tmpPath = tmpPath
        #
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False

    def getHistory(self, cvsPath):
        """ Return the history text for project files identified by cvsPath in the
            current repository.
        """
        text = ""
        ok = False
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            ok = self._runCvsCommand(myCommand=cmd)
            text = self._getOutputText()
        else:
            text = "History command failed with repository command processing error"

        return (ok, text)

    def getRevisionList(self, cvsPath):
        """ Return a list of tuples containing the revision identifiers for the input file.

            Return data has the for [(RevId, A/M, timeStamp),...] where A=Added and M=Modified.
        """
        revList = []
        ok = False
        cmd = self.__getHistoryCmd(cvsPath)
        if cmd is not None:
            ok = self._runCvsCommand(myCommand=cmd)
            revList = self.__extractRevisions()
        else:
            _text = "Revision history command failed with repository command processing error"  # noqa: F841

        return (ok, revList)

    def checkOutFile(self, cvsPath, outPath, revId=None):
        """ Perform CVS checkout operation for the project files identified by the input cvsPath
            subject to the input revision identifier.

            Files that are checked out are then subsequently copied to outPath.

            Note that outPath will not be a CVS working copy (sandbox) after this operation.
        """
        text = ""
        ok = False
        (pth, fn) = os.path.split(cvsPath)
        if self.__verbose:
            self.__lfh.write("+CvsAdmin(checkOutFile) Cvs directory %s   target file name %s\n" % (pth, fn))
        if len(fn) > 0:
            cmd = self.__getCheckOutCmd(cvsPath, outPath, revId)
            if cmd is not None:
                ok = self._runCvsCommand(myCommand=cmd)
                text = self._getErrorText()
            else:
                text = "Check out failed with repository command processing error"
        else:
            self.__lfh.write("+ERROR - CvsAdmin(checkOutFile) cannot check out project path %s\n" % cvsPath)
            text = "Check out failed with repository project path issue: %s" % cvsPath

        return (ok, text)

    def __getHistoryCmd(self, cvsPath):
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        outPath = self._getOutputFilePath()
        errPath = self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = "cvs -d " + self._cvsRoot + " history -a -x AM " + cvsPath + self._getRedirect(fileNameOut=outPath, fileNameErr=errPath)
        else:
            cmd = None
        return cmd

    def __getCheckOutCmd(self, cvsPath, outPath, revId=None):
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath = self._getErrorFilePath()
        (pth, fn) = os.path.split(cvsPath)
        if self.__verbose:
            self.__lfh.write("+CvsAdmin(__getCheckOutCmd) CVS directory %s  target file name %s\n" % (pth, fn))
        lclPath = os.path.join(self._wrkPath, cvsPath)
        outPathAbs = os.path.abspath(outPath)
        #
        #
        if self._setCvsRoot():
            if revId is None:
                rS = " "
                cmd = (
                    "cd "
                    + self._wrkPath
                    + " ; cvs -d "
                    + self._cvsRoot
                    + " co "
                    + cvsPath
                    + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath)
                    + " ; "
                    + " mv -f  "
                    + lclPath
                    + " "
                    + outPathAbs
                    + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True)
                    + " ; "
                )
                # cmd="cvs -d " +  self._cvsRoot  + " co -d " + self._wrkPath + " " + cvsPath +  \
                #     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                #     " mv -f  " + lclPath + " " + outPath + self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; '
            else:
                rS = " -r " + revId + " "
                cmd = (
                    "cd "
                    + self._wrkPath
                    + "; cvs -d "
                    + self._cvsRoot
                    + " co "
                    + rS
                    + " "
                    + cvsPath
                    + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath)
                    + " ; "
                    + " mv -f  "
                    + lclPath
                    + " "
                    + outPathAbs
                    + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True)
                    + " ; "
                )
                # cmd="cvs -d " +  self._cvsRoot  + " co -d " + self._wrkPath + rS +  " " + cvsPath + \
                #     self._getRedirect(fileNameOut=errPath,fileNameErr=errPath) + ' ; '  + \
                #     " mv -f  " + lclPath + " " + outPath + self._getRedirect(fileNameOut=errPath,fileNameErr=errPath,append=True) + ' ; '
        else:
            cmd = None
        return cmd

    def __extractRevisions(self):
        """Extract revisions details from the last history command.
        """
        revList = []
        try:
            fName = self._getOutputFilePath()
            if self.__verbose:
                self.__lfh.write("+CvsAdmin(__extraRevisions) Reading revisions from %r\n" % fName)
            ifh = open(fName, "r")
            for line in ifh.readlines():
                fields = line[:-1].split()
                typeCode = str(fields[0])
                revId = str(fields[5])
                timeStamp = str(fields[1] + ":" + fields[2])
                revList.append((revId, typeCode, timeStamp))
        except Exception as e:
            if self.__verbose:
                self.__lfh.write("+CvsAdmin(__extraRevisions) Extracting revision list for : %s %s\n" % (fName, str(e)))

        revList.reverse()
        self.__lfh.write("Ordered revision list %r\n" % revList)

        return revList


class CvsSandBoxAdmin(CvsWrapperBase):
    """Wrapper class for opertations on cvs working directories (aka cvs sandboxes).

    """

    def __init__(self, tmpPath="./", verbose=True, log=sys.stderr):
        super(CvsSandBoxAdmin, self).__init__(tmpPath=tmpPath, verbose=verbose, log=log)
        self.__tmpPath = tmpPath
        #
        self.__verbose = verbose
        self.__lfh = log
        self.__debug = False
        #
        self.__sandBoxTopPath = None

    def setSandBoxTopPath(self, dirPath):
        """ Assign the path that contains or will contain the working copy of the cvs project.

        """
        if not os.path.exists(dirPath):
            try:
                os.makedirs(dirPath)
            except Exception as e:
                self.__lfh.write("+setSandBoxTopPath - can't make sandboxpath: %s\n" % str(e))
        if os.access(dirPath, os.W_OK):
            self.__sandBoxTopPath = dirPath
            return True
        else:
            self.__lfh.write("+setSandBoxTopPath - can't access sandboxpath\n")
            return False

    def getSandBoxTopPath(self):
        return os.path.abspath(self.__sandBoxTopPath)

    def checkOut(self, projectPath=None, revId=None):
        """ Create CVS sandbox working copy of the input project path within the current repository.

        """
        if self.__verbose:
            self.__lfh.write("\n+CvsSandBoxAdmin(checkOut) Checking out CVS repository working path %s project file path %s\n" % (self.__sandBoxTopPath, projectPath))
        text = ""
        ok = False
        if self.__sandBoxTopPath is not None and projectPath is not None:
            cmd = self.__getCheckOutProjectCmd(projectPath, revId=revId)
            if self.__verbose:
                self.__lfh.write("\n+CvsSandBoxAdmin(checkOut) checkout command %s\n" % cmd)
            if cmd is not None:
                ok = self._runCvsCommand(myCommand=cmd)
                text = self._getErrorText()
            else:
                text = "Check out failed with repository command processing error"
        else:
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(checkOut) cannot check out project path %s\n" % projectPath)
            text = "Check out failed with repository project path issue: %s" % projectPath

        return (ok, text)

    def updateList(self, dataList, procName, optionsD, workingDir):  # pylint: disable=unused-argument
        """  Implements an interface for multiprocessing module --

             input is [(CvsProjectDir, relativePath, pruneFlag),...]

             returns -  successList,resultList=successList,diagList
        """
        retList = []
        diagTextList = []
        for dTup in dataList:
            pDir, relPath, _prune = dTup
            ok, text = self.update(projectDir=pDir, relProjectPath=relPath, prune=True, fetchErrorLog=True, appendErrors=True)
            diagTextList.append(text)
            if self.__verbose:
                self.__lfh.write("+CvsSandBoxAdmin(updateList) process %s project %s path %s status %r diagnostics:\n%s\n" % (procName, pDir, relPath, ok, text))
                self.__lfh.write("\n+CvsSandBoxAdmin(updateList) current diagnostics length %d\n" % len(diagTextList))
                self.__lfh.flush()
            if ok:
                retList.append(dTup)
        return retList, retList, diagTextList

    def update(self, projectDir, relProjectPath=".", prune=False, fetchErrorLog=True, appendErrors=False):
        """ Update CVS sandbox working copy of the input project path.   The project path must
            correspond to an existing working copy of the repository.

        """
        if self.__verbose:
            self.__lfh.write(
                "\n+CvsSandBoxAdmin(update) Updating CVS repository working path %s project %s relative file path %s\n" % (self.__sandBoxTopPath, projectDir, relProjectPath)
            )
        targetPath = os.path.join(self.__sandBoxTopPath, projectDir)
        text = ""
        ok = False
        if os.access(targetPath, os.W_OK):
            cmd = self.__getUpdateCmd(projectDir, relProjectPath=relProjectPath, prune=prune, appendErrors=appendErrors)
            if self.__debug:
                self.__lfh.write("\n+CvsSandBoxAdmin(update) update command %s\n" % cmd)
            if cmd is not None:
                ok = self._runCvsCommand(myCommand=cmd)
                if fetchErrorLog:
                    text = self._getErrorText(filterInfo=True)
                else:
                    text = "+CvsSandBoxAdmin(update) failing update command %s" % cmd
            else:
                text = "Update failed with repository command processing error"
        else:
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(update) top sandbox path %s project dir %s \n" % (self.__sandBoxTopPath, projectDir))
            if not os.path.exists(targetPath):
                try:
                    os.makedirs(targetPath)
                except Exception as e:
                    self.__lfh.write("+ERROR - CvsSandBoxAdmin(update) cannot make project path %s\n" % targetPath)
                    self.__lfh.write("%s\n" % str(e))
            if os.access(self.__sandBoxTopPath, os.W_OK):
                # try a full checkout --
                #
                ok, text = self.checkOut(projectPath=projectDir, revId=None)
            else:
                text = "Update failed with repository project path issue: %s" % targetPath
                self.__lfh.write("+ERROR - CvsSandBoxAdmin(update) cannot update project path %s\n" % targetPath)

        return (ok, text)

    def add(self, projectDir, relProjectPath):
        """ Add an new definition in CVS working direcotry in the input project path.   The project path must
            correspond to an existing file path in the local working copy.

        """
        if self.__verbose:
            self.__lfh.write("\n+CvsSandBoxAdmin(add) Add %s to project %s in CVS repository working path %s\n" % (relProjectPath, projectDir, self.__sandBoxTopPath))
        targetPath = os.path.join(self.__sandBoxTopPath, projectDir, relProjectPath)
        text = ""
        ok = False
        if os.access(targetPath, os.W_OK):
            cmd = self.__getAddCommitCmd(projectDir, relProjectPath)
            if cmd is not None:
                ok = self._runCvsCommand(myCommand=cmd)
                text = self._getErrorText()
            else:
                text = "Add failed with repository command processing error"
        else:
            text = "Add failed due with repository project path issue: %s" % targetPath
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(add) cannot add project path %s\n" % targetPath)

        return (ok, text)

    def commit(self, projectDir, relProjectPath):
        """ Commit changes in the input project/file path to the CVS repository. The project path must
            correspond to an existing path in the local working copy.

        """
        if self.__verbose:
            self.__lfh.write(
                "\n+CvsSandBoxAdmin(commit) Commit changes to %s in project %s in CVS repository working path %s\n" % (relProjectPath, projectDir, self.__sandBoxTopPath)
            )
        targetPath = os.path.join(self.__sandBoxTopPath, projectDir, relProjectPath)
        text = ""
        ok = False
        if os.access(targetPath, os.W_OK):
            cmd = self.__getCommitCmd(projectDir, relProjectPath)
            if cmd is not None:
                ok = self._runCvsCommand(myCommand=cmd)
                text = self._getErrorText()
            else:
                text = "Commit failed with repository command processing error"
        else:
            text = "Commit failed due with repository project path issue: %s" % targetPath
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(commit) cannot commit project path %s\n" % targetPath)

        return (ok, text)

    def remove(self, projectDir, relProjectPath, saveCopy=True):
        """ Remove from the CVS sandbox working copy the input project path.   The project path must
            correspond to an existing path in the local working copy.

            if saveCopy=True then preserve a copy of the remove target in the reserved REMOVED path
            of the repository.
        """
        if self.__verbose:
            self.__lfh.write("\n+CvsSandBoxAdmin(remove) Remove %s from project %s in CVS repository working path %s\n" % (relProjectPath, projectDir, self.__sandBoxTopPath))

        text = ""
        ok = False
        if (relProjectPath is None) or (len(relProjectPath) < 3):
            return (ok, text)
        #
        targetPath = os.path.join(self.__sandBoxTopPath, projectDir, relProjectPath)

        if self.__verbose:
            self.__lfh.write("\n+CvsSandBoxAdmin(remove) Remove target file path is %s\n" % targetPath)

        if os.access(targetPath, os.W_OK):
            #
            if saveCopy:
                (_pth, fn) = os.path.split(relProjectPath)
                savePath = os.path.join(self.__sandBoxTopPath, projectDir, "REMOVED", fn)

                # relSavePath = os.path.join("REMOVED", fn)
                shutil.copyfile(targetPath, savePath)
                # (ok1,saveText)=self.add(projectDir,relSavePath)
                # if not ok1:
                #    return (ok1,saveText)
            cmd = self.__getRemoveCommitCmd(projectDir, relProjectPath)
            if cmd is not None:
                ok = self._runCvsCommand(myCommand=cmd)
                text = self._getErrorText()
            else:
                text = "Remove failed with repository command processing error"
        else:
            text = "Remove failed due with repository project path issue: %s" % targetPath
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(remove) cannot remove project path %s\n" % targetPath)

        return (ok, text)

    def removeDir(self, projectDir, relProjectPath):
        """ Remove from the CVS sandbox working directory the input empty directory.

        """
        if self.__verbose:
            self.__lfh.write("\n+CvsSandBoxAdmin(removeDir) Remove %s from project %s in CVS repository working path %s\n" % (relProjectPath, projectDir, self.__sandBoxTopPath))

        text = ""
        ok = False
        if (relProjectPath is None) or (len(relProjectPath) < 3):
            return (ok, text)
        #
        targetPath = os.path.join(self.__sandBoxTopPath, projectDir, relProjectPath)

        if os.access(targetPath, os.W_OK):
            #
            cmd = self.__getRemoveDirCommitCmd(projectDir, relProjectPath)
            if cmd is not None:
                ok = self._runCvsCommand(myCommand=cmd)
                text = self._getErrorText()
            else:
                text = "Remove directory failed with repository command processing error"
        else:
            text = "Remove directory failed due with repository project path issue: %s" % targetPath
            self.__lfh.write("+ERROR - CvsSandBoxAdmin(remove) cannot remove project path %s\n" % targetPath)

        return (ok, text)

    def __getCheckOutProjectCmd(self, relProjectPath, revId=None):
        """ Return CVS command for checkout of a complete project from the current repository.
        """
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath = self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + self.__sandBoxTopPath + " ; "
            if revId is None:
                cmd += "cvs -d " + self._cvsRoot + " co " + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath) + " ; "
            else:
                rS = " -r " + revId + " "
                cmd += "cvs -d " + self._cvsRoot + " co " + rS + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath) + " ; "
        else:
            cmd = None
        return cmd

    def __getUpdateProjectCmd(self, projectDir, prune=False, appendErrors=False):
        """ Return CVS command for updating a complete project working directory from current repository.
        """
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath = self._getErrorFilePath()
        if self._setCvsRoot():
            if prune:
                pF = " -P "
            else:
                pF = " "
            targetPath = os.path.join(self.__sandBoxTopPath, projectDir)
            cmd = " cd " + targetPath + "; "
            cmd += "cvs -d " + self._cvsRoot + " update -C -d " + pF + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=appendErrors) + " ; "
        else:
            cmd = None
        return cmd

    def __getUpdateCmd(self, projectDir, relProjectPath, prune=False, appendErrors=False):
        """ Return CVS command for updating the input relative path within project working
            directory from current repository.
        """
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath = self._getErrorFilePath()
        if self._setCvsRoot():
            if prune:
                pF = " -P "
            else:
                pF = " "
            targetPath = os.path.join(self.__sandBoxTopPath, projectDir)
            cmd = " cd " + targetPath + "; "
            cmd += "cvs -q -d " + self._cvsRoot + " update -C -d " + pF + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=appendErrors) + " ; "
        else:
            cmd = None
        return cmd

    def __getAddCommitCmd(self, projectDir, relProjectPath, message="Initial version"):
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath = self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + os.path.join(self.__sandBoxTopPath, projectDir) + " ; "
            if message is not None and len(message) > 0:
                qm = ' -m "' + message + '" '
            cmd += "cvs -d " + self._cvsRoot + " add " + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath) + " ; "
            cmd += "cvs -d " + self._cvsRoot + " commit " + qm + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True) + " ; "
        else:
            cmd = None
        return cmd

    def __getCommitCmd(self, projectDir, relProjectPath, message="Automated update"):
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath = self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + os.path.join(self.__sandBoxTopPath, projectDir) + " ; "
            if message is not None and len(message) > 0:
                qm = ' -m "' + message + '" '
            cmd += "cvs -d " + self._cvsRoot + " commit " + qm + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True) + " ; "
        else:
            cmd = None
        return cmd

    def __getRemoveCommitCmd(self, projectDir, relProjectPath, message="File removed"):
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath = self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + os.path.join(self.__sandBoxTopPath, projectDir) + " ; "
            if message is not None and len(message) > 0:
                qm = ' -m "' + message + '" '
            cmd += "cvs -d " + self._cvsRoot + " remove -f " + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath) + " ; "
            cmd += "cvs -d " + self._cvsRoot + " commit " + qm + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True) + " ; "
        else:
            cmd = None
        return cmd

    def __getRemoveDirCommitCmd(self, projectDir, relProjectPath, message="Directory removed"):
        if self._wrkPath is None:
            self._makeTempWorkingDir()
        errPath = self._getErrorFilePath()
        if self._setCvsRoot():
            cmd = " cd " + os.path.join(self.__sandBoxTopPath, projectDir) + " ; "
            if message is not None and len(message) > 0:
                qm = ' -m "' + message + '" '
            cmd += "cvs -d " + self._cvsRoot + " remove " + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath) + " ; "
            cmd += "cvs -d " + self._cvsRoot + " commit " + qm + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True) + " ; "
            cmd += " rm -rf " + relProjectPath + self._getRedirect(fileNameOut=errPath, fileNameErr=errPath, append=True) + " ; "
        else:
            cmd = None
        return cmd
