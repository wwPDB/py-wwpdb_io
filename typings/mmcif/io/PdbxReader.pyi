from _typeshed import Incomplete

from typing import List, Optional, TextIO, Union

from mmcif.api.DataCategory import DataCategory as DataCategory
from mmcif.api.DataCategoryBase import DataCategoryBase
from mmcif.api.PdbxContainers import DataContainer as DataContainer, DefinitionContainer as DefinitionContainer, ContainerBase
from mmcif.io.PdbxExceptions import PdbxError as PdbxError, PdbxSyntaxError as PdbxSyntaxError

__docformat__: str
logger: Incomplete

class PdbxReader:
    def __init__(self, ifh: TextIO) -> None: ...
    def read(self, containerList: List[ContainerBase], selectList: Optional[List[str]] = None, excludeFlag: bool = False) -> None: ...
