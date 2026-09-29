"""
File:    mmCIFUtil.py
Author:  Zukang Feng
Update:  21-August-2012
Version: 001  Initial version

"""

__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__version__ = "V0.001"

import sys
from typing import Dict, List, Optional, TextIO, Tuple, cast

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import ContainerBase, DataContainer  # pylint: disable=unused-import
from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter
from typing_extensions import TypedDict


class CategoryDictType(TypedDict):
    Items: List[str]
    Values: List[List[Optional[str]]]


class mmCIFUtil:
    """Using pdbx mmCIF utility to parse mmCIF file"""

    def __init__(self, verbose: bool = False, log: TextIO = sys.stderr, filePath: Optional[str] = None) -> None:  # noqa: ARG002 pylint: disable=unused-argument
        # self.__verbose = verbose
        self.__lfh = log
        self.__filePath = filePath
        self.__dataList: List[DataContainer] = []
        self.__dataMap: Dict[str, int] = {}
        self.__container: Optional[DataContainer] = None
        self.__blockID: Optional[str] = None
        self.__read()
        #

    def __read(self) -> None:
        if not self.__filePath:
            return
        #
        try:
            ifh = open(self.__filePath)
            pRd = PdbxReader(ifh)
            pRd.read(cast("List[ContainerBase]", self.__dataList))
            ifh.close()
            if self.__dataList:
                self.__container = self.__dataList[0]
                self.__blockID = self.__container.getName()
                idx = 0
                for container in self.__dataList:
                    self.__dataMap[container.getName()] = idx
                    idx += 1  # noqa: SIM113
                #
            #
        except Exception as e:  # noqa: BLE001
            self.__lfh.write("Read %s failed %s.\n" % (self.__filePath, str(e)))
        #

    def GetBlockID(self) -> Optional[str]:
        """Return first block ID"""
        return self.__blockID

    def GetValueAndItemByBlock(self, blockName: Optional[str], catName: str) -> Tuple[List[Dict[str, str]], List[str]]:
        """Get category values and item names"""
        dList: List[Dict[str, str]] = []
        iList: List[str] = []
        if blockName not in self.__dataMap:
            return dList, iList
        #
        catObj = self.__dataList[self.__dataMap[blockName]].getObj(catName)
        if not catObj:
            return dList, iList
        #
        iList = catObj.getAttributeList()
        rowList = catObj.getRowList()
        for row in rowList:
            tD = {}
            for idxIt, itName in enumerate(iList):
                if row[idxIt] != "?" and row[idxIt] != ".":
                    tD[itName] = row[idxIt]
            #
            if tD:
                dList.append(tD)
            #
        #
        return dList, iList

    def GetValueAndItem(self, catName: str) -> Tuple[List[Dict[str, str]], List[str]]:
        dList, iList = self.GetValueAndItemByBlock(self.__blockID, catName)
        return dList, iList

    def GetValue(self, catName: str) -> List[Dict[str, str]]:
        """Get category values based on category name 'catName'. The results are stored
        in a list of dictionaries with item name as key
        """
        dList, _iList = self.GetValueAndItemByBlock(self.__blockID, catName)
        return dList

    def GetSingleValue(self, catName: str, itemName: str) -> str:
        """Get the first value of item name 'itemName' from 'itemName' item in 'catName' category."""
        text = ""
        dlist = self.GetValue(catName)
        if dlist:
            if itemName in dlist[0]:
                text = dlist[0][itemName]
        return text
        #

    def UpdateSingleRowValue(self, catName: str, itemName: str, row: int, value: str) -> None:
        """Update value in single row"""
        catObj = cast("DataContainer", self.__container).getObj(catName)
        if catObj is None:
            return
        #
        catObj.setValue(value, itemName, row)

    def UpdateMultipleRowsValue(self, catName: str, itemName: str, value: str) -> None:
        """Update value in multiple rows"""
        catObj = cast("DataContainer", self.__container).getObj(catName)
        if catObj is None:
            return
        #
        rowNo = catObj.getRowCount()
        for row in range(rowNo):
            catObj.setValue(value, itemName, row)
        #

    def AddBlock(self, blockID: str) -> None:
        """Add Data Block"""
        self.__container = DataContainer(blockID)
        self.__blockID = blockID
        self.__dataMap[blockID] = len(self.__dataList)
        self.__dataList.append(self.__container)

    def AddCategory(self, categoryID: str, items: List[str]) -> None:
        """Add Category"""
        category = DataCategory(categoryID)
        for item in items:
            category.appendAttribute(item)
        #
        cast("DataContainer", self.__container).append(category)

    def RemoveCategory(self, categoryID: str) -> bool:
        return cast("DataContainer", self.__container).remove(categoryID)

    def InsertData(self, categoryID: str, dataList: List[List[str]]) -> None:
        """"""
        catObj = cast("DataContainer", self.__container).getObj(categoryID)
        if catObj is None:
            return
        #
        for data in dataList:
            catObj.append(data)
        #

    def WriteCif(self, outputFilePath: Optional[str] = None) -> None:
        """Write out cif file"""
        if not outputFilePath:
            return
        #
        ofh = open(outputFilePath, "w")
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(cast("List[ContainerBase]", self.__dataList))
        ofh.close()

    def GetCategories(self) -> List[str]:
        return cast("DataContainer", self.__container).getObjNameList()

    def GetAttributes(self, category: str) -> List[str]:
        # Could raise exceptions if category does not exist
        return self.__container.getObj(category).getAttributeList()  # type: ignore

    def category_as_dict(self, category: str, block: Optional[str] = None) -> Dict[str, CategoryDictType]:
        if block is None:
            block = self.__blockID
        values, attributes = self.GetValueAndItemByBlock(block, category)
        data = [[x[y] if y in x else None for y in attributes] for x in values]  # noqa: SIM401
        ret: Dict[str, CategoryDictType] = {}
        ret[category] = {"Items": attributes, "Values": data}
        return ret

    def block_as_dict(self, block: Optional[str] = None) -> Dict[str, CategoryDictType]:
        if block is None:
            block = self.__blockID
        data = {}
        for category in self.GetCategories():
            data.update(self.category_as_dict(category, block=block))
        return data
