"""
Utility class of generic data file methods.

File:    DataFile.py
Author:  jdw
Update:  21-Aug-2009
Version: 001
Initial version - adapted from rcsbDataFile.py  method collections.

Update:  22-Aug-2009
Version: 002  Fixed comparison function -

This software was developed as part of the Protein Structure Initiative
Structural Genomics Knowledgebase (PSI SGKB) project at Rutgers University.

Copyright (c) 2009 PSI SGKB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""

__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__version__ = "V0.002"


import sys
import os
import os.path
import time
import datetime
import filecmp
import stat
import shutil
import smtplib
import tempfile
from email.mime.text import MIMEText

##
##


class DataFile:

    """ Class of utilities for managing data files.
    """

    def __init__(self, fPath=None, tMode=None, verbose=False):
        self.test = " "
        self.verbose = verbose
        self.vout = sys.stdout
        self.srcPathInp = None
        self.srcPath = None
        self.srcDirName = None
        self.srcFileName = None
        self.srcFileBaseName = None
        self.srcFileExt = None
        self.srcType = None
        self.srcStat = None
        self.__updateSrc(fPath)
        #
        self.dstPathInp = None
        self.dstPath = None
        self.dstDirName = None
        self.dstFileName = None
        self.dstFileBaseName = None
        self.dstFileExt = None
        self.dstType = None
        self.dstStat = None
        #
        self.__formatTimeStamp = "%Y-%m-%d:%H:%M:%S"
        self.tMode = tMode

    def __updateSrc(self, fPath):
        if fPath is not None:
            self.srcPathInp = fPath
            self.srcPath = os.path.abspath(fPath)
            (self.srcDirName, self.srcFileName) = os.path.split(self.srcPath)
            (self.srcFileBaseName, self.srcFileExt) = os.path.splitext(self.srcFileName)
            self.srcType = self.__ftype(self.srcFileExt)
            self.srcStat = None

    def __updateDst(self, fPath):
        if fPath is not None:
            self.dstPathInp = fPath
            self.dstPath = os.path.abspath(fPath)
            (self.dstDirName, self.dstFileName) = os.path.split(self.dstPath)
            (self.dstFileBaseName, self.dstFileExt) = os.path.splitext(self.dstFileName)
            self.dstType = self.__ftype(self.dstFileExt)
            self.dstStat = None

    def __ftype(self, fExt):
        if fExt == ".Z":
            ftype = "zlib"
        elif fExt == ".gz":
            ftype = "gzip"
        elif fExt == ".bz2":
            ftype = "bzip"
        else:
            ftype = None
        return ftype

    def __exists(self, fPath):
        if fPath is not None:
            if os.access(fPath, os.F_OK):
                return True
            else:
                return False
        else:
            return False

    def __stat(self, fPath):
        if fPath is not None:
            try:
                tup = os.stat(fPath)
                return tup
            except:  # noqa: E722 pylint: disable=bare-except
                return None
        else:
            return None

    def __mkdir(self, path):
        if not os.path.isdir(path):
            os.makedirs(path, 0o755)

    def __pathDivide(self, p, rest=None):
        if rest is None:
            rest = []
        (h, t) = os.path.split(p)
        if len(h) < 1:
            return [t] + rest
        if len(t) < 1:
            return [h] + rest
        return self.__pathDivide(h, [t] + rest)

    def __findCommonMembers(self, l1, l2, common=None):
        if common is None:
            common = []
        if len(l1) < 1:
            return (common, l1, l2)
        if len(l2) < 1:
            return (common, l1, l2)
        if l1[0] != l2[0]:
            return (common, l1, l2)
        return self.__findCommonMembers(l1[1:], l2[1:], common + [l1[0]])

    def __makeRelativePath(self, src, dst):
        #        self.vout.write("++INFO - src %s\n" % src)
        #        self.vout.write("++INFO - dst %s\n" % dst)
        (_common, l1, l2) = self.__findCommonMembers(self.__pathDivide(dst), self.__pathDivide(src))
        p = []
        #        if (len(l1) > 0):
        #            p = [ '../' * len(l1) ]
        if len(l1) > 1:
            p = ["../" * (len(l1) - 1)]

        p = p + l2
        return os.path.join(*p)

    def __symLinkRelative(self):
        """Internal method that makes a relative symbolic link to srcPath from dstPath.
           Intervening path components are created for the destination so this method
           is only appropriate for linking files.
        """
        if not self.srcFileExists() or not os.path.isabs(self.srcPath):
            return
        if self.dstPath is None:
            return
        if not self.dstDirExists():
            self.__mkdir(self.dstDirName)

        rPath = self.__makeRelativePath(self.srcPath, self.dstPath)

        if rPath.startswith(".."):
            # make link
            #            self.vout.write("++INFO - linking %s to %s\n" % (self.dstPath,rPath))
            if os.path.islink(self.dstPath):
                os.unlink(self.dstPath)
            return os.symlink(rPath, self.dstPath)
        else:
            self.vout.write("++ERROR - relative pathname creation failed %s\n" % rPath)
            return -1

    def __symLink(self):
        """Internal method that creates a symbolic link to srcPath named dstPath.
           Intervening path components are created for the destination so this method
           is only appropriate for linking files.
        """
        if not self.srcFileExists() or not os.path.isabs(self.srcPath):
            return
        if self.dstPath is None:
            return
        if not self.dstDirExists():
            self.__mkdir(self.dstDirName)
        if os.path.islink(self.dstPath):
            os.unlink(self.dstPath)
        return os.symlink(self.srcPath, self.dstPath)

    def __copy(self, op="copy"):
        """Internal method that copies srcPath to dstPath converting compression mode
           according to file type.
        """
        if not self.srcFileExists():
            return
        if not self.dstDirExists():
            self.__mkdir(self.dstDirName)

        if self.srcType == self.dstType and op == "copy":
            return shutil.copy2(self.srcPath, self.dstPath)
        else:
            if (self.srcType == "zlib") or (self.srcType == "gzip"):
                cmdP1 = "zcat " + self.srcPath
            elif self.srcType == "bzip":
                cmdP1 = "bzcat " + self.srcPath
            elif self.srcType is None:
                cmdP1 = "cat " + self.srcPath

            if op == "copy":
                redir = " > "
            elif op == "append":
                redir = " >> "
            else:
                redir = " > "

            if self.dstType == "zlib":
                cmdP2 = " |  compress -cf - " + redir + self.dstPath
            elif self.dstType == "gzip":
                cmdP2 = " |  gzip " + redir + self.dstPath
            elif self.dstType == "bzip":
                cmdP2 = " | bzip2 " + redir + self.dstPath
            elif self.dstType is None:
                cmdP2 = redir + self.dstPath

            cmd = cmdP1 + cmdP2
            return os.system(cmd)

    def __compare(self):
        """Compare srcPath to dstPath converting compression according to
           file extension (.Z, .gz, .bz ).

        Return True if the files are content equivalent and
               False otherwise.

        """
        isSame = False
        if not self.srcFileExists():
            return isSame
        if not self.dstFileExists():
            return isSame

        if self.srcType == self.dstType:
            isSame = filecmp.cmp(self.srcPath, self.dstPath, False)
        else:
            cmd = ""
            if self.srcType is None:
                f1 = self.srcPath
            elif (self.srcType == "zlib") or (self.srcType == "gzip"):
                f1 = tempfile.mktemp()
                cmd = "zcat " + self.srcPath + "> " + f1
            elif self.srcType == "bzip":
                f1 = tempfile.mktemp()
                cmd = "bzcat " + self.srcPath + "> " + f1

            if len(cmd) > 0:
                print("src command: %s" % cmd)
                os.system(cmd)

            cmd = ""
            if self.dstType is None:
                f2 = self.dstPath
            elif (self.dstType == "zlib") or (self.dstType == "gzip"):
                f2 = tempfile.mktemp()
                cmd = "zcat " + self.dstPath + "> " + f2
            elif self.dstType == "bzip":
                f2 = tempfile.mktemp()
                cmd = "bzcat " + self.dstPath + "> " + f2

            if len(cmd) > 0:
                print("dst command: %s" % cmd)
                os.system(cmd)

            if os.access(f1, os.F_OK) and os.access(f2, os.F_OK):
                isSame = filecmp.cmp(f1, f2, False)
                if f1 != self.srcPath:
                    os.remove(f1)
                if f2 != self.dstPath:
                    os.remove(f2)
            else:
                sys.stdout.write("++ERROR - comparison failed for %s with %s \n" % (f1, f2))

        return isSame

    def __remove(self):
        """Internal method that removes srcPath if it exists.
        """
        if not self.srcFileExists():
            return True
        if os.path.islink(self.srcPath):
            return os.unlink(self.srcPath)
        elif os.path.isfile(self.srcPath):
            return os.unlink(self.srcPath)
        elif os.path.isdir(self.srcPath):
            return shutil.rmtree(self.srcPath, True)

    def __move(self):
        """Internal method that moves srcPath to dstPath.
        """
        if not self.srcFileExists():
            return
        if not self.dstDirExists():
            self.__mkdir(self.dstDirName)
        if self.srcType == self.dstType:
            return shutil.move(self.srcPath, self.dstPath)

    def __timeStampCopy(self):
        """Reset the atime/mtimes of the destination using those of the
           source file.
        """
        if self.srcStat is None:
            self.srcStat = self.__stat(self.srcPath)
        if self.srcStat is not None and self.__exists(self.dstPath):
            times = (self.srcStat[stat.ST_ATIME], self.srcStat[stat.ST_MTIME])
            os.utime(self.dstPath, times)

    def __setTimeStamp(self, fPath, tObj):
        """Reset the atime/mtimes of the input file using the input timestamp.
        """
        if tObj is None or not self.__exists(fPath):
            return
        mtime = int(time.mktime(tObj.timetuple()))
        times = (mtime, mtime)
        os.utime(fPath, times)

    def __setFileMode(self, fPath, mode):
        """Reset the file mode of the input file using the input integer mode (e.g. 0644)
        """
        try:
            os.chmod(fPath, mode)
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False

    def setSrcFileMode(self, mode):
        if not self.srcFileExists():
            return False
        return self.__setFileMode(self.srcPath, mode)

    def setDstFileMode(self, mode):
        if not self.dstFileExists():
            return False
        return self.__setFileMode(self.dstPath, mode)

    def __setDstTimeStamp(self):
        if self.tMode is not None and self.__exists(self.dstPath):
            if self.tMode == "preserve":
                self.__timeStampCopy()
            elif self.tMode == "today":
                tObj = datetime.datetime.today()
                self.__setTimeStamp(self.dstPath, tObj)
            elif self.tMode == "yesterday":
                tObj = datetime.datetime.today() + datetime.timedelta(days=-1)
                self.__setTimeStamp(self.dstPath, tObj)
            elif self.tMode == "tomorrow":
                tObj = datetime.datetime.today() + datetime.timedelta(days=1)
                self.__setTimeStamp(self.dstPath, tObj)
            elif self.tMode == "lastweek":
                tObj = datetime.datetime.today() + datetime.timedelta(days=-7)
                self.__setTimeStamp(self.dstPath, tObj)

    #

    def src(self, fPath):
        """Set or reset the source file path
        """
        self.__updateSrc(fPath)

    def dst(self, fPath):
        """Set or reset the destination file path
        """
        self.__updateDst(fPath)

    def timeMode(self, tMode):
        """Sets the behavior of the timestamping of destination files: one of None, preserve, today, ...
        """
        self.tMode = tMode

    def pr(self, fh=sys.stdout):
        """Output the information about source and destination files
        """
        if self.srcPath is not None:
            fh.write("Source path (input):        %s\n" % self.srcPathInp)
            fh.write("Source path:                %s\n" % self.srcPath)
            fh.write("Source directory:           %s\n" % self.srcDirName)
            fh.write("Source file name:           %s\n" % self.srcFileName)
            fh.write("Source file extension:      %s\n" % self.srcFileExt)
            fh.write("Source file type :          %s\n" % str(self.srcType))
            #  lt = time.strftime("%Y %m %d %H:%M:%S", time.localtime())
            if self.srcStat is None:
                self.srcStat = self.__stat(self.srcPath)
            if self.srcStat is not None:
                fh.write("Source creation time:       %s\n" % time.ctime(self.srcStat[stat.ST_CTIME]))
                fh.write("Source modification time:   %s\n" % time.ctime(self.srcStat[stat.ST_MTIME]))
                fh.write("Source access time:         %s\n" % time.ctime(self.srcStat[stat.ST_ATIME]))
                fh.write("Source size (bytes):        %d\n" % self.srcStat[stat.ST_SIZE])
                fh.write("Source uid/gid:             %d|%d\n" % (self.srcStat[stat.ST_UID], self.srcStat[stat.ST_GID]))
                fh.write("Source mode:                %o\n" % self.srcStat[stat.ST_MODE])

        if self.dstPath is not None:
            fh.write("Destination path (input):   %s\n" % self.dstPathInp)
            fh.write("Destination path:           %s\n" % self.dstPath)
            fh.write("Destination directory:      %s\n" % self.dstDirName)
            fh.write("Destination file name:      %s\n" % self.dstFileName)
            fh.write("Destination file extension: %s\n" % self.dstFileExt)
            fh.write("Destination file type:      %s\n" % str(self.dstType))
            if self.dstStat is None:
                self.dstStat = self.__stat(self.dstPath)
            if self.dstStat is not None:
                fh.write("Destination creation time:       %s\n" % time.ctime(self.dstStat[stat.ST_CTIME]))
                fh.write("Destination modification time:   %s\n" % time.ctime(self.dstStat[stat.ST_MTIME]))
                fh.write("Destination access time:         %s\n" % time.ctime(self.dstStat[stat.ST_ATIME]))
                fh.write("Destination size (bytes):        %d\n" % self.dstStat[stat.ST_SIZE])
                fh.write("Destination uid/gid:             %d|%d\n" % (self.dstStat[stat.ST_UID], self.dstStat[stat.ST_GID]))
                fh.write("Destination mode:                %o\n" % self.dstStat[stat.ST_MODE])

    def copy(self, dstPath=None):
        """Copies srcPath to dstPath converting compression mode
        according to file type.
        """
        self.dst(dstPath)
        self.__copy(op="copy")
        self.__setDstTimeStamp()

    def append(self, dstPath=None):
        """Appends srcPath to dstPath converting compression mode
        according to file type.
        """
        self.dst(dstPath)
        self.__copy(op="append")
        self.__setDstTimeStamp()

    def compare(self, dstPath=None):
        """Compare srcPath to dstPath converting compression mode
        according to file type.

        Returns True if the files are content equivalent or False otherwise
        """
        self.dst(dstPath)
        return self.__compare()

    def remove(self):
        """Removes srcPath.
        """
        self.__remove()

    def srcFileSize(self):
        if self.srcStat is None:
            self.srcStat = self.__stat(self.srcPath)
        if self.srcStat is not None:
            return self.srcStat[stat.ST_SIZE]
        else:
            return 0

    def dstFileSize(self):
        if self.dstStat is None:
            self.dstStat = self.__stat(self.dstPath)
        if self.dstStat is not None:
            return self.dstStat[stat.ST_SIZE]
        else:
            return 0

    def move(self, dstPath=None):
        """Moves (renames) srcPath to dstPath.
        """
        self.dst(dstPath)
        self.__move()
        self.__setDstTimeStamp()

    def symLinkRelative(self, dstPath=None):
        """Creates a relative symbolic link to srcPath at dstPath.
        """
        self.dst(dstPath)
        self.__symLinkRelative()

    #        self.__setDstTimeStamp()

    def symLink(self, dstPath=None):
        """Create a symbolic link to srcPath at dstPath.
        """
        self.dst(dstPath)
        self.__symLink()

    #        self.__setDstTimeStamp()

    def srcFileExists(self):
        """Return True if source file exists or False otherwise.
        """
        return self.__exists(self.srcPath)

    def dstFileExists(self):
        """Return True if destination file exists or False otherwise.
        """
        return self.__exists(self.dstPath)

    def dstDirExists(self):
        """Return True if destination file exists or False otherwise.
        """
        return self.__exists(self.dstDirName)

    def srcModTime(self):
        """Return modification time of the source file as the number of seconds
        since the epoch (ie. 1970-01-01).
        """
        if self.srcStat is None:
            self.srcStat = self.__stat(self.srcPath)
        if self.srcStat is not None:
            return self.srcStat[stat.ST_MTIME]
        else:
            return None

    def srcModTimeStamp(self):
        """Return modification time of the source file as the number of seconds
        since the epoch (ie. 1970-01-01).
        """
        if self.srcStat is None:
            self.srcStat = self.__stat(self.srcPath)
        if self.srcStat is not None:
            return time.strftime(self.__formatTimeStamp, time.localtime(self.srcStat[stat.ST_MTIME]))
        else:
            return None

    def newerThan(self, fPath):
        """Return True if srcPath has been modified more recently than fPath.
           If the comparison cannot be made 'None' is returned.
        """
        if fPath is None:
            return None
        fTup = self.__stat(fPath)
        if fTup is not None:
            modTimeF = fTup[stat.ST_MTIME]
        else:
            return None

        modTime = self.srcModTime()
        if modTime is not None:
            if modTime > modTimeF:
                return True
            else:
                return False
        else:
            # no stat for srcPath
            return None

    def eMail(self, toAddr, fromAddr, subject):  # pragma: no cover
        """ Internal method to mail srcPath file as text.
        """
        if not self.srcFileExists():
            return

        cmd = ""
        if self.srcType is None:
            f1 = self.srcPath
        elif (self.srcType == "zlib") or (self.srcType == "gzip"):
            f1 = tempfile.mktemp()
            cmd = "zcat " + self.srcPath + "> " + f1
        elif self.srcType == "bzip":
            f1 = tempfile.mktemp()
            cmd = "bzcat " + self.srcPath + "> " + f1
        if len(cmd) > 0:
            os.system(cmd)

        # Create a text/plain message
        fp = open(f1, "rb")
        msg = MIMEText(fp.read())
        fp.close()
        msg["Subject"] = subject
        msg["From"] = fromAddr
        msg["To"] = toAddr
        s = smtplib.SMTP()
        s.connect()
        s.sendmail(fromAddr, [toAddr], msg.as_string())
        s.close()
        if f1 != self.srcPath:
            os.remove(f1)

    def setDstMTimeYYYYMMDD(self, dateYYYYMMDD):
        """Set access and modification times to the input date stamp.
        """

    def setDstMTime(self, refPath):
        """Set access and modification times to the input date stamp.
        """
