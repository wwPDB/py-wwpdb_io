##
# File:  PathInfo.py
# Date:  25-Feb-2013  J. Westbrook
#
# Updated:
#  26-Feb-2013  jdw   implement new session storage options in DataFileReference()
#  28-Feb-2013  jdw   move to generic path wwpdb.utils.rcsb.PathInfo()
#  28-Feb-2013  jdw   Add wrappers for more general purpose methods -
#  04-Apr-2013  jdw   Add assembly assignment and map convenience methods
#  27-Aug-2013  jdw   Add optional parameters for content milestone variants [upload,deposit,annotate,...]
#  23-Dec-2013  jdw   Add support for file source 'session-download' as extension of file source session.
#  19-Apr-2014  jdw   add getPolyLinkReportFilePath()
#   9-May-2014  jdw   add entity/partition argument to getSequenceAlignFilePath()
# 25-Jun-2014   jdw   add convenience methods getEmVolumeFilePath() getEmMaskFilePath()
# 26-Jun-2014   jdw   correct parameter errors on blast-match and map methods, add omit-map methods
# 28-Jun-2014   jdw   add template methods for searching file versions and partitions
#  1-Jul-2014   jdw   fix initialization in __getPathWorker()
#  5-Jul-2014   jdw   add method getFilePathContentTypeTemplate()
#  7-Jul-2014   jdw   add method getStatusHistoryFilePath()
# 23-Aug-2014   jdw   add method getEmDepositVolumeParamsFilePath()
# 14-Sep-2014   jdw   add isValidFileName(fileName, requireVersion=True) and splitFileName(fileName)
# 24-Sep-2014   jdw   add getFileExtension(formatType)
# 13-Dec-2016   jdw   add getStructureFactorsPdbxFilePath()
# 23-Oct-2017   jdw   config for logging - add parseFileName wrapper method
# 24-Mar-2018   ep    add mileStone argument to getFilePathContentTypeTemplate()
# 06-Jun-2023   dh    add getNMRCombinedFilePath()
# 15-Jun-2023   dh    add getMolecularRestraintsFilePath()
# 19-Dec-2024   my    add getNMRifFilePath() (DAOTHER-8905)
##
"""
Common methods for finding path information for resource and data files in the wwPDB data processing
and annotation system.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Apache 2.0"
__version__ = "V0.07"

import logging
import os
import os.path
from typing import Dict, Literal, Optional, TextIO, Tuple, Union, cast  # pylint: disable=unused-import

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId

from wwpdb.io.locator.DataReference import DataFileReference, DataReferencePartitionId, DataReferenceStorageType, DataReferenceVersionId, ReferenceFileComponents

logger = logging.getLogger(__name__)


# Types
PathInfoVersionId = DataReferenceVersionId  # Same
PathInfoPartitionId = Union[DataReferencePartitionId, str]  # These APIs allow strings
PathInfoStorageType = Union[DataReferenceStorageType, Literal["session-download"]]  # These APIs allow additional one


class PathInfo:
    """Common methods for finding path information for sequence resources and data files.

    In these methods the parameter contentType refers to a base content type.

    The mileStone parameter is used to select the milestone variant in any convenience methods
    (e.g. model-deposit, model-upload, ... )

    """

    def __init__(self, siteId: Optional[str] = None, sessionPath: Optional[str] = ".", verbose: bool = False, log: Optional[TextIO] = None):
        """"""
        self.__lfh: TextIO
        self.__verbose = verbose
        self.__closelfh = False
        if log is None:
            self.__lfh = open(os.devnull, "w")
            self.__closelfh = True
        else:
            self.__lfh = log
        #
        self.__debug = False  # pylint: disable=unused-private-member
        self.__siteId = siteId if siteId is not None else getSiteId(defaultSiteId=siteId)
        self.__sessionPath = sessionPath
        self.__sessionDownloadPath: Optional[str] = None
        if self.__sessionPath is not None:
            self.__sessionDownloadPath = os.path.join(self.__sessionPath, "downloads")
        #
        self.__cI = ConfigInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

    def __del__(self) -> None:
        if self.__closelfh:
            self.__lfh.close()

    def setDebugFlag(self, flag: bool) -> None:
        self.__debug = flag  # pylint: disable=unused-private-member

    def parseFileName(self, fileName: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[PathInfoPartitionId], Optional[PathInfoVersionId]]:
        rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
        if rfc.set(fileName=fileName):
            return rfc.get()
        return None, None, None, None, None

    def isValidFileName(self, fileName: str, requireVersion: bool = True) -> bool:
        """Is the input file name project compliant ?"""
        rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
        if rfc.set(fileName=fileName):
            (dId, cT, cF, pN, vN) = rfc.get()
            if requireVersion:
                if (dId is None) or (cT is None) or (cF is None) or (pN is None) or (vN is None):
                    return False
                return True
            if (dId is None) or (cT is None) or (cF is None) or (pN is None):
                return False
            return True
        return False

    def getFileExtension(self, formatType: str) -> Optional[str]:
        eD = cast("Dict[str, str]", self.__cI.get("FILE_FORMAT_EXTENSION_DICTIONARY"))
        try:
            return eD[formatType]
        except Exception as _e:  # noqa: F841,BLE001
            return None

    def splitFileName(self, fileName: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[PathInfoPartitionId], Optional[PathInfoVersionId]]:
        """
        returns (depositionDataSetId, contentType, contentFormat, filePartionNumber, [versionId (int) or None])
        """
        try:
            rfc = ReferenceFileComponents(verbose=self.__verbose, log=self.__lfh)
            rfc.set(fileName=fileName)
            return rfc.get()
        except Exception as _e:  # noqa: F841,BLE001
            return (None, None, None, None, None)

    #

    def setSessionPath(self, sessionPath: str) -> None:
        """Set the top path that will be searched for files with fileSource='session'"""
        self.__sessionPath = sessionPath
        self.__sessionDownloadPath = os.path.join(self.__sessionPath, "downloads")

    def getArchivePath(self, dataSetId: str) -> Optional[str]:
        try:
            if dataSetId.startswith("G_"):
                return self.getDirPath(dataSetId=dataSetId, fileSource="autogroup")
            return self.getDirPath(dataSetId=dataSetId, fileSource="archive")
            #
        except Exception as _e:  # noqa: F841,BLE001
            return None

    def getInstancePath(self, dataSetId: str, wfInstanceId: Optional[str]) -> Optional[str]:
        try:
            return self.getDirPath(dataSetId=dataSetId, fileSource="wf-instance", wfInstanceId=wfInstanceId)
            # return os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'workflow', dataSetId, 'instance', wfInstanceId)
        except Exception as _e:  # noqa: F841,BLE001
            return None

    def getInstanceTopPath(self, dataSetId: str) -> Optional[str]:
        try:
            return os.path.dirname(cast("str", self.getDirPath(dataSetId=dataSetId, fileSource="wf-instance", wfInstanceId="W_001")))
            # return os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'workflow', dataSetId, 'instance')
        except Exception as _e:  # noqa: F841,BLE001
            return None

    def getDepositPath(self, dataSetId: str) -> Optional[str]:
        try:
            return self.getDirPath(dataSetId=dataSetId, fileSource="deposit")
            # return os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'deposit', dataSetId)
        except Exception as _e:  # noqa: F841,BLE001
            return None

    def getDepositUIPath(self, dataSetId: str) -> Optional[str]:
        try:
            return self.getDirPath(dataSetId=dataSetId, fileSource="deposit-ui")
        except Exception as _e:  # noqa: F841,BLE001
            return None

    def getTempDepPath(self, dataSetId: str) -> Optional[str]:
        try:
            return self.getDirPath(dataSetId=dataSetId, fileSource="tempdep")
        except Exception as _e:  # noqa: F841,BLE001
            return None

    def getModelPdbxFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="model", formatType="pdbx", mileStone=mileStone
        )

    def getModelPdbFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="model", formatType="pdb", mileStone=mileStone
        )

    def getStructureFactorsPdbxFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="structure-factors", formatType="pdbx", mileStone=mileStone
        )

    def getPolyLinkFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            contentTypeBase="polymer-linkage-distances",
            formatType="pdbx",
            mileStone=mileStone,
        )

    def getPolyLinkReportFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            contentTypeBase="polymer-linkage-report",
            formatType="html",
            mileStone=mileStone,
        )

    def getSequenceStatsFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="seq-data-stats", formatType="pic", mileStone=mileStone
        )

    def getSequenceAlignFilePath(
        self,
        dataSetId: str,
        entityId: PathInfoPartitionId = "1",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            contentTypeBase="seq-align-data",
            partNumber=entityId,
            formatType="pic",
            mileStone=mileStone,
        )

    def getReferenceSequenceFilePath(
        self,
        dataSetId: str,
        entityId: PathInfoPartitionId = "1",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber=entityId,
            contentTypeBase="seqdb-match",
            formatType="pdbx",
            mileStone=mileStone,
        )

    def getSequenceAssignmentFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="seq-assign", formatType="pdbx", mileStone=mileStone
        )

    def getAssemblyAssignmentFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="assembly-assign", formatType="pdbx", mileStone=mileStone
        )

    def getBlastMatchFilePath(
        self,
        dataSetId: str,
        entityId: PathInfoPartitionId = "1",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber=entityId,
            contentTypeBase="blast-match",
            formatType="xml",
            mileStone=mileStone,
        )

    def getMap2fofcFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber="1",
            contentTypeBase="map-2fofc",
            formatType="map",
            mileStone=mileStone,
        )

    def getMapfofcFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber="1",
            contentTypeBase="map-fofc",
            formatType="map",
            mileStone=mileStone,
        )

    def getOmitMap2fofcFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber="1",
            contentTypeBase="omit-map-2fofc",
            formatType="map",
            mileStone=mileStone,
        )

    def getOmitMapfofcFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber="1",
            contentTypeBase="omit-map-fofc",
            formatType="map",
            mileStone=mileStone,
        )

    #

    def getEmVolumeFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber="1",
            contentTypeBase="em-volume",
            formatType="map",
            mileStone=mileStone,
        )

    def getEmMaskFilePath(
        self,
        dataSetId: str,
        maskNumber: PathInfoPartitionId = "1",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber=maskNumber,
            contentTypeBase="em-mask",
            formatType="map",
            mileStone=mileStone,
        )

    def getEmDepositVolumeParamsFilePath(
        self,
        dataSetId: str,
        maskNumber: PathInfoPartitionId = "1",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "deposit",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber=maskNumber,
            contentTypeBase="deposit-volume-params",
            formatType="pic",
            mileStone=mileStone,
        )

    def getAuthChemcialShiftsFilePath(
        self,
        dataSetId: str,
        formatType: str = "nmr-star",
        partNumber: PathInfoPartitionId = "next",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber=partNumber,
            contentTypeBase="nmr-chemical-shifts-auth",
            formatType=formatType,
            mileStone=mileStone,
        )

    def getChemcialShiftsFilePath(
        self,
        dataSetId: str,
        formatType: str = "nmr-star",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber="1",
            contentTypeBase="nmr-chemical-shifts",
            formatType=formatType,
            mileStone=mileStone,
        )

    def getMolecularRestraintsFilePath(
        self,
        dataSetId: str,
        formatType: str = "nmr-star",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber="1",
            contentTypeBase="nmr-restraints",
            formatType=formatType,
            mileStone=mileStone,
        )

    def getNMRCombinedFilePath(
        self,
        dataSetId: str,
        formatType: str = "nmr-star",
        wfInstanceId: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            fileSource=fileSource,
            versionId=versionId,
            partNumber="1",
            contentTypeBase="nmr-data-str",
            formatType=formatType,
            mileStone=mileStone,
        )

    def getNMRifFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "deposit", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="nmrif", formatType="pdbx", mileStone=mileStone
        )

    def getAssemblyModelFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "deposit", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="assembly-model", formatType="pdbx", mileStone=mileStone
        )

    def getAssemblySuggestedFilePath(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, fileSource: PathInfoStorageType = "deposit", versionId: PathInfoVersionId = "latest", mileStone: Optional[str] = None
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=wfInstanceId, fileSource=fileSource, versionId=versionId, contentTypeBase="assembly-suggested", formatType="json", mileStone=mileStone
        )

    def getStatusHistoryFilePath(self, dataSetId: str, fileSource: PathInfoStorageType = "archive", versionId: PathInfoVersionId = "latest") -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId, wfInstanceId=None, fileSource=fileSource, versionId=versionId, partNumber="1", contentTypeBase="status-history", formatType="pdbx", mileStone=None
        )

    #
    def getFilePath(
        self,
        dataSetId: Optional[str],
        wfInstanceId: Optional[str] = None,
        contentType: Optional[str] = None,
        formatType: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        partNumber: PathInfoPartitionId = "1",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        return self.__getStandardPath(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            contentTypeBase=contentType,
            formatType=formatType,
            fileSource=fileSource,
            versionId=versionId,
            partNumber=partNumber,
            mileStone=mileStone,
        )

    #
    def getFileName(
        self,
        dataSetId: str,
        wfInstanceId: Optional[str] = None,
        contentType: Optional[str] = None,
        formatType: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        partNumber: PathInfoPartitionId = "1",
        mileStone: Optional[str] = None,
    ) -> str:
        return os.path.basename(
            cast(
                "str",
                self.__getStandardPath(
                    dataSetId=dataSetId,
                    wfInstanceId=wfInstanceId,
                    contentTypeBase=contentType,
                    formatType=formatType,
                    fileSource=fileSource,
                    versionId=versionId,
                    partNumber=partNumber,
                    mileStone=mileStone,
                ),
            )
        )

    def getDirPath(
        self,
        dataSetId: str,
        wfInstanceId: Optional[str] = None,
        contentType: Optional[str] = None,  # noqa: ARG002  pylint: disable=unused-argument
        formatType: Optional[str] = None,  # noqa: ARG002  pylint: disable=unused-argument
        fileSource: PathInfoStorageType = "archive",
        versionId: Optional[PathInfoVersionId] = "latest",  # noqa: ARG002  pylint: disable=unused-argument
        partNumber: PathInfoPartitionId = "1",  # noqa: ARG002  pylint: disable=unused-argument
        mileStone: Optional[str] = None,  # noqa: ARG002  pylint: disable=unused-argument
    ) -> Optional[str]:  # noqa: E501,ARG002 pylint: disable=unused-argument
        dfRef = DataFileReference(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        dfRef.setDepositionDataSetId(dataSetId)
        dfRef.setStorageType(cast("DataReferenceStorageType", fileSource))  # session-download will cause rejection here - but we correct below
        if fileSource in ("session", "wf-session"):
            dfRef.setStorageType("session")
            dfRef.setSessionPath(self.__sessionPath)
        if fileSource in ("session-download"):
            dfRef.setStorageType("session")
            dfRef.setSessionPath(self.__sessionDownloadPath)
        dfRef.setSessionDataSetId(dataSetId)
        dfRef.setWorkflowInstanceId(wfInstanceId)
        return dfRef.getDirPathReference()

        # return os.path.dirname(self.__getStandardPath(dataSetId=dataSetId,
        #                                               wfInstanceId=wfInstanceId,
        #                                               contentTypeBase=contentType,
        #                                               formatType=formatType,
        #                                               fileSource=fileSource,
        #                                               versionId=versionId,
        #                                               partNumber=partNumber,
        #                                               mileStone=mileStone))

    def getWebDownloadPath(
        self,
        dataSetId: str,
        wfInstanceId: Optional[str] = None,
        contentType: Optional[str] = None,
        formatType: Optional[str] = None,
        versionId: PathInfoVersionId = "latest",
        partNumber: PathInfoPartitionId = "1",
        mileStone: Optional[str] = None,
    ) -> str:
        fn = os.path.basename(
            cast(
                "str",
                self.__getStandardPath(
                    dataSetId=dataSetId,
                    wfInstanceId=wfInstanceId,
                    contentTypeBase=contentType,
                    formatType=formatType,
                    fileSource="session-download",
                    versionId=versionId,
                    partNumber=partNumber,
                    mileStone=mileStone,
                ),
            )
        )
        (_p, sId) = os.path.split(cast("str", self.__sessionPath))
        return os.path.join("/sessions", sId, "downloads", fn)

    def getFilePathVersionTemplate(
        self,
        dataSetId: str,
        wfInstanceId: Optional[str] = None,
        contentType: Optional[str] = None,
        formatType: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        partNumber: PathInfoPartitionId = "1",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        _fp, vt, _pt, _cct = self.__getPathWorker(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            contentTypeBase=contentType,
            formatType=formatType,
            fileSource=fileSource,
            versionId="none",
            partNumber=partNumber,
            mileStone=mileStone,
        )
        return vt

    def getFilePathPartitionTemplate(
        self,
        dataSetId: str,
        wfInstanceId: Optional[str] = None,
        contentType: Optional[str] = None,
        formatType: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        _fp, _vt, pt, _cct = self.__getPathWorker(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            contentTypeBase=contentType,
            formatType=formatType,
            fileSource=fileSource,
            versionId="none",
            partNumber="1",
            mileStone=mileStone,
        )
        return pt

    def getFilePathContentTypeTemplate(
        self, dataSetId: str, wfInstanceId: Optional[str] = None, contentType: Optional[str] = None, fileSource: PathInfoStorageType = "archive", mileStone: Optional[str] = None
    ) -> Optional[str]:
        _fp, _vt, _pt, cct = self.__getPathWorker(
            dataSetId=dataSetId,
            wfInstanceId=wfInstanceId,
            contentTypeBase=contentType,
            formatType="any",
            fileSource=fileSource,
            versionId="none",
            partNumber="1",
            mileStone=mileStone,
        )
        return cct

    def __getStandardPath(
        self,
        dataSetId: Optional[str],
        wfInstanceId: Optional[str] = None,
        contentTypeBase: Optional[str] = None,
        formatType: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        partNumber: PathInfoPartitionId = "1",
        mileStone: Optional[str] = None,
    ) -> Optional[str]:
        fP = None
        try:
            fP, _vT, _pT, _ccT = self.__getPathWorker(
                dataSetId=dataSetId,
                wfInstanceId=wfInstanceId,
                contentTypeBase=contentTypeBase,
                formatType=formatType,
                fileSource=fileSource,
                versionId=versionId,
                partNumber=partNumber,
                mileStone=mileStone,
            )
        except Exception as e:
            logger.exception("+PathInfo.__getStandard() failing for %s id %s wf id %s with %r", fileSource, dataSetId, wfInstanceId, str(e))

        return fP

    def __getPathWorker(
        self,
        dataSetId: Optional[str],
        wfInstanceId: Optional[str] = None,
        contentTypeBase: Optional[str] = None,
        formatType: Optional[str] = None,
        fileSource: PathInfoStorageType = "archive",
        versionId: PathInfoVersionId = "latest",
        partNumber: PathInfoPartitionId = "1",
        mileStone: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Return the path and templates corresponding to the input file typing arguments.

        Return:  <full file path>,<file path as a version template>,<file path as a partition template>
        """
        #
        try:
            if mileStone is not None:
                contentType: Optional[str] = cast("str", contentTypeBase) + "-" + mileStone
            else:
                contentType = contentTypeBase
                #
            logger.debug(
                "+PathInfo.__getPathworker() file source %s for id %s wf id %s contentType %r formatType %r partNumber %r versionId %r",
                fileSource,
                dataSetId,
                wfInstanceId,
                contentType,
                formatType,
                partNumber,
                versionId,
            )
            dfRef = DataFileReference(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            if fileSource in ["archive", "wf-archive"]:
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setStorageType("archive")
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif fileSource in ["autogroup"]:
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setStorageType("autogroup")
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif fileSource in ["deposit"]:
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setStorageType("deposit")
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif fileSource in ["deposit-ui"]:
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setStorageType("deposit-ui")
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif fileSource in ["tempdep"]:
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setStorageType("tempdep")
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif fileSource == "wf-instance":
                dfRef.setDepositionDataSetId(dataSetId)
                dfRef.setWorkflowInstanceId(wfInstanceId)
                dfRef.setStorageType("wf-instance")
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            elif fileSource in ["session", "wf-session"]:
                dfRef.setSessionPath(self.__sessionPath)
                dfRef.setSessionDataSetId(dataSetId)
                dfRef.setStorageType("session")
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)

            elif fileSource in ["session-download"]:
                dfRef.setSessionPath(self.__sessionDownloadPath)
                dfRef.setSessionDataSetId(dataSetId)
                dfRef.setStorageType("session")
                dfRef.setContentTypeAndFormat(contentType, formatType)
                dfRef.setPartitionNumber(partNumber)
                dfRef.setVersionId(versionId)
            else:
                logger.debug("+PathInfo.__getPathworker() bad file source %s for id %s wf id %s contentType %r", fileSource, dataSetId, wfInstanceId, contentType)
                return None, None, None, None

            fP = None
            vT = None
            pT = None
            ctT = None
            if dfRef.isReferenceValid():
                fP = dfRef.getFilePathReference()
                dP = dfRef.getDirPathReference()
                pT = os.path.join(cast("str", dP), cast("str", dfRef.getPartitionNumberSearchTarget()))
                vT = os.path.join(cast("str", dP), cast("str", dfRef.getVersionIdSearchTarget()))
                ctT = os.path.join(cast("str", dP), cast("str", dfRef.getContentTypeSearchTarget()))
                logger.debug("+PathInfo.__getPathworker() file path:                %s", fP)
                logger.debug("+PathInfo.__getPathworker() partition search path:    %s", pT)
                logger.debug("+PathInfo.__getPathworker() version search path:      %s", vT)
                logger.debug("+PathInfo.__getPathworker() content type search path: %s", ctT)
            else:
                dP = dfRef.getDirPathReference()
                try:
                    ctT = os.path.join(cast("str", dP), cast("str", dfRef.getContentTypeSearchTarget()))
                except Exception as e:
                    ctT = None
                    logger.exception("+PathInfo.__getPathworker() failing with content type search template construction with %r", str(e))
                #
            return fP, vT, pT, ctT
        except Exception as e:
            logger.exception("Failing for source %s id %s wf id %s contentType %r with %r", fileSource, dataSetId, wfInstanceId, contentType, str(e))
        return None, None, None, None
