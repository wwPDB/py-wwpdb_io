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

from mmcif.api.DataCategory import DataCategory
from mmcif.api.PdbxContainers import DataContainer
from mmcif.io.PdbxReader import PdbxReader
from mmcif.io.PdbxWriter import PdbxWriter


class mmCIFUtil:
    """Using pdbx mmCIF utility to parse mmCIF file
    """

    def __init__(self, verbose=False, log=sys.stderr, filePath=None):
        self.__verbose = verbose
        self.__lfh = log
        self.__filePath = filePath
        self.__dataList = []
        self.__dataMap = {}
        self.__container = None
        self.__blockID = None
        self.__read()
        #

    def __read(self):
        if not self.__filePath:
            return
        #
        try:
            ifh = open(self.__filePath, "r")
            pRd = PdbxReader(ifh)
            pRd.read(self.__dataList)
            ifh.close()
            if self.__dataList:
                self.__container = self.__dataList[0]
                self.__blockID = self.__container.getName()
                idx = 0
                for container in self.__dataList:
                    self.__dataMap[container.getName()] = idx
                    idx += 1
                #
            #
        except Exception as e:
            self.__lfh.write("Read %s failed %s.\n" % (self.__filePath, str(e)))
        #

    def GetBlockID(self):
        """Return first block ID
        """
        return self.__blockID

    def GetValueAndItemByBlock(self, blockName, catName):
        """Get category values and item names
        """
        dList = []
        iList = []
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

    def GetValueAndItem(self, catName):
        dList, iList = self.GetValueAndItemByBlock(self.__blockID, catName)
        return dList, iList

    def GetValue(self, catName):
        """Get category values based on category name 'catName'. The results are stored
           in a list of dictionaries with item name as key
        """
        dList, _iList = self.GetValueAndItemByBlock(self.__blockID, catName)
        return dList

    def GetSingleValue(self, catName, itemName):
        """Get the first value of item name 'itemName' from 'itemName' item in 'catName' category.
        """
        text = ""
        dlist = self.GetValue(catName)
        if dlist:
            if itemName in dlist[0]:
                text = dlist[0][itemName]
        return text
        #

    def UpdateSingleRowValue(self, catName, itemName, row, value):
        """Update value in single row
        """
        catObj = self.__container.getObj(catName)
        if catObj is None:
            return
        #
        catObj.setValue(value, itemName, row)

    def UpdateMultipleRowsValue(self, catName, itemName, value):
        """Update value in multiple rows
        """
        catObj = self.__container.getObj(catName)
        if catObj is None:
            return
        #
        rowNo = catObj.getRowCount()
        for row in range(0, rowNo):
            catObj.setValue(value, itemName, row)
        #

    def AddBlock(self, blockID):
        """Add Data Block
        """
        self.__container = DataContainer(blockID)
        self.__blockID = blockID
        self.__dataMap[blockID] = len(self.__dataList)
        self.__dataList.append(self.__container)

    def AddCategory(self, categoryID, items):
        """Add Category
        """
        category = DataCategory(categoryID)
        for item in items:
            category.appendAttribute(item)
        #
        self.__container.append(category)

    def InsertData(self, categoryID, dataList):
        """
        """
        catObj = self.__container.getObj(categoryID)
        if catObj is None:
            return
        #
        for data in dataList:
            catObj.append(data)
        #

    def WriteCif(self, outputFilePath=None):
        """Write out cif file
        """
        if not outputFilePath:
            return
        #
        ofh = open(outputFilePath, "w")
        pdbxW = PdbxWriter(ofh)
        pdbxW.write(self.__dataList)
        ofh.close()

    def GetCategories(self):
        return self.__container.getObjNameList()

    def GetAttributes(self, category):
        return self.__container.getObj(category).getAttributeList()

    def category_as_dict(self, category, block=None):
        if block is None:
            block = self.__blockID
        values, attributes = self.GetValueAndItemByBlock(block, category)
        data = [[x[y] if y in x else None for y in attributes] for x in values]
        return {category: {"Items": attributes, "Values": data}}

    def block_as_dict(self, block=None):
        if block is None:
            block = self.__blockID
        data = {}
        for category in self.GetCategories():
            data.update(self.category_as_dict(category, block=block))
        return data
