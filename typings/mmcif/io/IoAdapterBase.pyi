from _typeshed import Incomplete
from typing import Any, List

from mmcif.io.PdbxExceptions import PdbxError as PdbxError
from mmcif.api.PdbxContainers import DataContainer

__docformat__: str
logger: Incomplete

class IoAdapterBase:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def readFile(self, *args: Any, **kwargs: Any) -> List[DataContainer]: ...
    def writeFile(self, outputFilePath: str, containerList: List[DataContainer], **kwargs: Any) -> bool: ...
    def getReadDiags(self) -> List[str]: ...
