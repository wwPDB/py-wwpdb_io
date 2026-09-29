from _typeshed import Incomplete
from typing import Any, List, Optional  # noqa: F401

# from build.lib.mmciflib import CifFile as CifFile, CifFileReadDef as CifFileReadDef, ParseCifSelective as ParseCifSelective, ParseCifSimple as ParseCifSimple
from mmcif.api.DataCategory import DataCategory as DataCategory
from mmcif.api.PdbxContainers import DataContainer as DataContainer
from mmcif.io.IoAdapterBase import IoAdapterBase as IoAdapterBase
from mmcif.io.PdbxExceptions import PdbxError as PdbxError, PdbxSyntaxError as PdbxSyntaxError

__docformat__: str
logger: Incomplete
HERE: Incomplete

class IoAdapterCore(IoAdapterBase):
    def readFile(self, inputFilePath: str, enforceAscii: bool = True, selectList: Optional[List[str]] = None, excludeFlag: bool = False, logFilePath: Optional[str] = None, outDirPath: Optional[str] = None, cleanUp: bool = True, fmt: str = 'mmcif', **kwargs: Any) -> List[DataContainer]: ...
    def getReadDiags(self) -> List[str]: ...
    def writeFile(self, outputFilePath: str, containerList: Optional[List[DataContainer]] = None, doubleQuotingFlag: bool = False, maxLineLength: int = 900, enforceAscii: bool = True, lastInOrder: Optional[List[str]]=None, selectOrder: Optional[List[str]]=None, fmt: str = 'mmcif', **kwargs: Any) -> bool: ...
