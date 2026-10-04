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

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "john.westbrook@rcsb.org"
__license__ = "Apache 2.0"
__version__ = "V0.001"

#
#
import logging
from typing import Any, Dict, NoReturn, Optional, cast

# For python 3.8 compatibility
from typing_extensions import NotRequired, TypedDict, Unpack
from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

logger = logging.getLogger(__name__)


class SftpConnectConfig(TypedDict):
    port: NotRequired[int]
    pw: NotRequired[Optional[str]]
    keyFilePath: NotRequired[Optional[str]]
    keyFileType: NotRequired[str]


class ArchiveIoInitConfig(TypedDict):
    raiseExceptions: NotRequired[bool]
    siteId: NotRequired[str]
    serverId: NotRequired[str]


class ArchiveIoBase:
    """A base class for for archive data transfer operation utilities."""

    def __init__(self, *args: str, **kwargs: Unpack[ArchiveIoInitConfig]) -> None:  # noqa: ARG002  pylint: disable=unused-argument
        self._raiseExceptions = kwargs.get("raiseExceptions", False)
        self._siteId = kwargs.get("siteId", getSiteId())
        self._serverId = cast("str", kwargs.get("serverId"))

        self.__cI = ConfigInfo(siteId=getSiteId())
        #
        cD: Dict[str, Any] = self.__cI.get(self._serverId, {})
        self._hostName = cast("str", cD.get("HOST_NAME"))
        self._userName = cast("str", cD.get("HOST_USERNAME"))
        self._password = cD.get("HOST_PASSWORD")
        self._hostPort = int(cD.get("HOST_PORT", 22))
        self._protocol = cD.get("HOST_PROTOCOL")
        self._rootPath: str | None = cD.get("HOST_ROOT_PATH")
        self._keyFilePath = cD.get("HOST_KEY_FILE_PATH")
        self._keyFileType = cast("str", cD.get("HOST_KEY_FILE_TYPE"))
        #

    def __raise_unimplemented(self) -> NoReturn:
        err = "To be implemented in subclass"
        raise NotImplementedError(err)

    def connect(self, hostName: str, userName: str, **kwargs: Unpack[SftpConnectConfig]) -> bool:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def mkdir(self, path: str, mode: int) -> bool:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def stat(self, path: str) -> dict[str, Any]:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def put(self, localPath: str, remotePath: str) -> bool:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def get(self, remotePath: str, localPath: str) -> bool:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def listdir(self, path: str) -> list[str] | bool:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def rmdir(self, path: str) -> bool:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def remove(self, filePath: str) -> bool:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()

    def close(self) -> bool:  # noqa: ARG002  pylint: disable=unused-argument
        self.__raise_unimplemented()
