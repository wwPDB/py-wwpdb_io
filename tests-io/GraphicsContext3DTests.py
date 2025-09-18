##
#
# File:    GraphicsContext3DTests.py
# Author:  J. Westbrook
# Date:    23-Jun-2012
# Version: 0.001
#
# Updated:
#
##
"""
Test cases for GraphicsContext3D using a PDBx persistent store as a data source.

"""

__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

# Disable checks for use of _getframe
# pylint: disable=protected-access
# ruff: noqa: SLF001

import os
import os.path
import platform
import sys
import time
import traceback
import unittest

from mmcif_utils.persist.PdbxPersist import PdbxPersist
from mmcif_utils.persist.PdbxPyIoAdapter import PdbxPyIoAdapter as PdbxIoAdapter

from wwpdb.io.graphics.GraphicsContext3D import GraphicsContext3D

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(HERE)
TESTOUTPUT = os.path.join(HERE, "test-output", platform.python_version())
if not os.path.exists(TESTOUTPUT):  # pragma: no cover
    os.makedirs(TESTOUTPUT)
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")


class GraphicsContext3DTests(unittest.TestCase):
    def setUp(self):
        self.__lfh = sys.stdout
        self.__verbose = True
        self.__debug = False
        self.__pathPdbxDataFile = os.path.join(mockTopPath, "MODELS", "3rer.cif")

    def tearDown(self):
        pass

    def getFirstObject(self, persistFilePath, objectName=None):
        """Open the persistent data store and fetch the input object name from the first container.

        Note -- Will be used for more complex cases which require additional information from
        coordinate model file to resolve the graphics context.
        """
        #
        try:
            myPersist = PdbxPersist(self.__verbose, self.__lfh)
            indexD = myPersist.getIndex(dbFileName=persistFilePath)
            (firstContainerName, _firstContainerType) = indexD["__containers__"][0]

            if self.__debug:  # pragma: no cover
                self.__lfh.write("GraphicsContext3D.getFirstObject() container name list %r\n" % indexD.items())
            myObj = myPersist.fetchOneObject(dbFileName=persistFilePath, containerName=firstContainerName, objectName=objectName)
            return myObj
        except Exception as e:  # noqa: BLE001 pragma: no cover
            if self.__verbose:
                self.__lfh.write("+ERROR- GraphicsContext3D.getFirstObject() Read failed for file %s - %s\n" % (persistFilePath, str(e)))
                traceback.print_exc(file=self.__lfh)
            return None

    def testSimpleContexts(self):
        """Test case -  create simple graphics contexts."""
        self.__lfh.write(
            "\nStarting %s %s at %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
        )

        try:
            gC = GraphicsContext3D(app3D="JMol", verbose=self.__verbose, log=self.__lfh)
            myReader = PdbxIoAdapter(self.__verbose, self.__lfh)
            ok = myReader.read(pdbxFilePath=self.__pathPdbxDataFile)
            self.assertTrue(ok)
            myPersist = PdbxPersist(self.__verbose, self.__lfh)
            myPersist.setContainerList(myReader.getContainerList())
            dbFile = os.path.join(TESTOUTPUT, "my.db")
            myPersist.store(dbFileName=dbFile)
            indexD = myPersist.getIndex(dbFile)

            self.__lfh.write("Persistent index dictionary %r\n" % indexD.items())

            for containerName, _containerType in indexD["__containers__"]:
                objNameList = indexD[containerName]
                #
                # For a selection of categories with obvious graphics contexts --
                #
                for objectName in [
                    "struct_conn",
                    "struct_conf",
                    "struct_site_gen",
                    "pdbx_poly_seq_scheme",
                    "pdbx_nonpoly_scheme",
                    "atom_site",
                    "struct_sheet_range",
                    "pdbx_struct_sheet_hbond",
                ]:
                    if objectName in objNameList:
                        self.__lfh.write("Fetching %s  %s\n" % (containerName, objectName))
                        myObj = myPersist.fetchOneObject(dbFileName=dbFile, containerName=containerName, objectName=objectName)
                        aL = myObj.getAttributeList()
                        rowList = myObj.getRowList()
                        for row in rowList:
                            rD = {}
                            for ii, rVal in enumerate(row):
                                rD[aL[ii]] = rVal
                            # self.__lfh.write("Row dictionary: %r\n" % rD.items())
                            gcS = gC.getGraphicsContext(categoryName=objectName, rowDictList=[rD])
                            self.__lfh.write("Context : %s\n" % gcS)

        except:  # noqa: E722 pylint: disable=bare-except  # pragma: no cover
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testSiteContexts(self):
        """Test case -  create graphics contexts for a full site"""
        self.__lfh.write(
            "\nStarting %s %s at %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
        )
        try:
            #
            #  Create a persistent store for the test file --
            #
            myReader = PdbxIoAdapter(self.__verbose, self.__lfh)
            ok = myReader.read(pdbxFilePath=self.__pathPdbxDataFile)
            self.assertTrue(ok)
            myPersist = PdbxPersist(self.__verbose, self.__lfh)
            myPersist.setContainerList(myReader.getContainerList())
            outputDb = os.path.join(TESTOUTPUT, "my2.db")
            myPersist.store(dbFileName=outputDb)
            #
            # Open the persistent store and read the site details -
            #
            mySite = self.getFirstObject(persistFilePath=outputDb, objectName="struct_site")
            aL = mySite.getAttributeList()
            #
            gC = GraphicsContext3D(app3D="JMol", verbose=self.__verbose, log=self.__lfh)
            gC.setPersistStorePath(persistFilePath=outputDb)
            #
            for row in mySite.getRowList():
                rD = {}
                for ii, rVal in enumerate(row):
                    rD[aL[ii]] = rVal
                # rD now contains the row dictionary for this site row -
                #
                gcS = gC.getGraphicsContext(categoryName="struct_site", rowDictList=[rD])
                self.__lfh.write("Site context : %s\n" % gcS)
        except:  # noqa: E722 pylint: disable=bare-except # pragma: no cover
            traceback.print_exc(file=self.__lfh)
            self.fail()

    def testSiteContextsOld(self):
        """Test case -  create graphics contexts for a full site"""
        self.__lfh.write(
            "\nStarting %s %s at %s\n" % (self.__class__.__name__, sys._getframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
        )
        try:
            #
            #  Create a persistent store for the test file --
            #
            myReader = PdbxIoAdapter(self.__verbose, self.__lfh)
            ok = myReader.read(pdbxFilePath=self.__pathPdbxDataFile)
            self.assertTrue(ok)
            myPersist = PdbxPersist(self.__verbose, self.__lfh)
            myPersist.setContainerList(myReader.getContainerList())
            outputDb = os.path.join(TESTOUTPUT, "my2.db")
            myPersist.store(dbFileName=outputDb)
            #
            # Open the persistent store and read the site details -
            #
            mySite = self.getFirstObject(persistFilePath=outputDb, objectName="struct_site")
            aL = mySite.getAttributeList()
            idx = aL.index("id")
            #
            # idList will hold the identifiers for each site.
            #
            idList = []
            for row in mySite.getRowList():
                idList.append(row[idx])

            #
            #
            mySiteGen = self.getFirstObject(persistFilePath=outputDb, objectName="struct_site_gen")
            aL = mySiteGen.getAttributeList()
            idx = aL.index("site_id")
            #
            #  Get the graphics context for structure details for each site.
            gC = GraphicsContext3D(app3D="JMol", verbose=self.__verbose, log=self.__lfh)
            for eid in idList:
                rDL = []
                for row in mySiteGen.getRowList():
                    if eid == row[idx]:
                        # create a row dictionary
                        rD = {}
                        for ii, rVal in enumerate(row):
                            rD[aL[ii]] = rVal
                        # self.__lfh.write("Row dictionary: %r\n" % rD.items())
                        rDL.append(rD)
                gcS = gC.getGraphicsContext(categoryName="struct_site_gen", rowDictList=rDL)
                self.__lfh.write("Site %s context : %s\n" % (eid, gcS))

        except:  # noqa: E722 pylint: disable=bare-except # pragma: no cover
            traceback.print_exc(file=self.__lfh)
            self.fail()


def suiteFile():  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(GraphicsContext3DTests("testSimpleContexts"))
    suiteSelect.addTest(GraphicsContext3DTests("testSiteContexts"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    #
    mySuite = suiteFile()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
    #
