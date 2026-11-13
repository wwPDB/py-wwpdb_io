from _typeshed import Incomplete
from typing import Any, List, Optional  # noqa: F401

from mmcif.io.BinaryCifReader import BinaryCifReader as BinaryCifReader
from mmcif.io.BinaryCifWriter import BinaryCifWriter as BinaryCifWriter
from mmcif.io.IoAdapterBase import IoAdapterBase as IoAdapterBase
from mmcif.io.PdbxExceptions import PdbxError as PdbxError, PdbxSyntaxError as PdbxSyntaxError
from mmcif.io.PdbxReader import PdbxReader as PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter as PdbxWriter
from mmcif.api.PdbxContainers import DataContainer
from mmcif.api.DictionaryApi import DictionaryApi

__docformat__: str
logger: Incomplete

class IoAdapterPy(IoAdapterBase):
    def readFile(self, inputFilePath: str, enforceAscii: bool = False, selectList: Optional[List[str]] = None, excludeFlag: bool = False, logFilePath: Optional[str] = None, outDirPath: Optional[str] = None, cleanUp: bool = True, fmt: str = 'mmcif', timeout: Optional[float] = None, storeStringsAsBytes: bool = False, defaultStringEncoding: str = 'utf-8', **kwargs: Any) -> List[DataContainer]: ...
    def getReadDiags(self) -> List[str]: ...
    def writeFile(self, outputFilePath: str, containerList: List[DataContainer], maxLineLength: int = 900, enforceAscii: bool = True, lastInOrder: Optional[List[str]] = None, selectOrder: Optional[List[str]] = None, columnAlignFlag: bool = True, useStopTokens: bool = False, formattingStep: Optional[int] = None, fmt: str = 'mmcif', storeStringsAsBytes: bool = False, defaultStringEncoding: str = 'utf-8', applyTypes: bool = True, dictionaryApi: Optional[DictionaryApi] = None, useStringTypes: bool = False, useFloat64: bool = False, copyInputData: bool = False, ignoreCastErrors: bool = False, **kwargs: Any) -> bool: ...
