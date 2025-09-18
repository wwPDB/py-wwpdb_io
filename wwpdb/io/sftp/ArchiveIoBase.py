##
# File:    ArchiveIoBase.py
# Author:  jdw
# Date:    10-Oct-2017
# Version: 0.001
#
# Updates:
#
##
"""
Base class for archive data transfer operation utilities.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

#
#
import logging

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

logger = logging.getLogger(__name__)


class ArchiveIoBase:
    """A base class for for archive data transfer operation utilities."""

    def __init__(self, *args, **kwargs):  # noqa: ARG002  pylint: disable=unused-argument
        self._raiseExceptions = kwargs.get("raiseExceptions", False)
        self._siteId = kwargs.get("siteId", getSiteId())
        self._serverId = kwargs.get("serverId", None)

        self.__cI = ConfigInfo(siteId=getSiteId())
        #
        cD = self.__cI.get(self._serverId, {})
        self._hostName = cD.get("HOST_NAME", None)
        self._userName = cD.get("HOST_USERNAME", None)
        self._password = cD.get("HOST_PASSWORD", None)
        self._hostPort = int(cD.get("HOST_PORT", 22))
        self._protocol = cD.get("HOST_PROTOCOL", None)
        self._rootPath = cD.get("HOST_ROOT_PATH", None)
        self._keyFilePath = cD.get("HOST_KEY_FILE_PATH", None)
        self._keyFileType = cD.get("HOST_KEY_FILE_TYPE", None)
        #

    def __raise_unimplemented(self):
        err = "To be implemented in subclass"
        raise NotImplementedError(err)

    def connect(self, hostName, userName, **kwargs):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def mkdir(self, path, **kwargs):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def stat(self, path):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def put(self, localPath, remotePath):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def get(self, remotePath, localPath):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def listdir(self, path):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def rmdir(self, path):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def remove(self, path):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def close(self):  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()
