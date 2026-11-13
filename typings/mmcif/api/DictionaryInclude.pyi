from _typeshed import Incomplete
from mmcif.api.PdbxContainers import CifName as CifName
from mmcif.io.IoAdapterPy import IoAdapterPy as IoAdapterPy

__docformat__: str
logger: Incomplete

class DictionaryInclude:
    def __init__(self, **kwargs) -> None: ...
    def processIncludedContent(self, containerList, cleanup: bool = False): ...
