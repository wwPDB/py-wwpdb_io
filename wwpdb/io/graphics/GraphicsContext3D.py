##
# File: GraphicsContext3D.py
# Date: 24-June-2012
#
# Updates:
# 27-June-2012 jdw Change magnification on zoomto and quoting policy on labels.
# 28-Sept-2012 jdw Adjust the Jmol setup to improve the depiction.
#
##
"""
Construct a 3D graphics context from selected rows in PDBx/mmCIF data catagories.


"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"


import sys
import traceback

from mmcif_utils.persist.PdbxPersist import PdbxPersist


class GraphicsContext3D(object):
    """ Construct a 3D graphics context from selected rows in PDBx/mmCIF data catagories.

    Only app3D='JMol' is currently supported.
    """

    def __init__(self, app3D="JMol", verbose=True, log=sys.stderr):
        self.__verbose = verbose
        self.__debug = False
        self.__lfh = log
        self.__app3D = app3D
        self.__persistFilePath = None

        self.__setup()
        #

    def __setup(self):
        """ Category dictionary containing data attribute names which define 3D context.

        For each category with a graphics context a list of atom/component/polymer features is
        is provided.  The feature are defined as a set of standard keys defining the
        the author nomenclature for the feature.

        """
        self.__jMolDefaultSelection = "select all; label off; "
        # self.__jMolSetup=" background black; wireframe only; wireframe 0.15; labels off; slab 100; depth 40; slab on; "

        self.__jMolSetup = (
            " background black; font label 20 monospaced bold; set fontScaling OFF; color label white; wireframe only; wireframe 0.10; labels off; slab 70; depth 25; slab on; "
        )
        #
        # Category types to customize context assignments -
        #
        self.__searchContextCategoryList = ["struct_site"]
        self.__rangeTypeCategoryList = ["struct_conf", "struct_sheet_range"]
        self.__atomContextCategoryList = ["atom_site", "struct_conn", "pdbx_struct_sheet_hbond"]
        self.__componentContextCategoryList = ["struct_conf", "struct_sheet_range", "pdbx_poly_seq_scheme", "pdbx_nonpoly_scheme"]
        self.__polymerContextCategoryList = []
        #
        #  Templates for extracting structur features from selected categories.
        #
        self.__d = {
            "struct_conn": [
                {
                    "auth_asym_id": "ptnr1_auth_asym_id",
                    "auth_comp_id": "ptnr1_auth_comp_id",
                    "auth_seq_id": "ptnr1_auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "pdbx_ptnr1_PDB_ins_code",
                    "atom_id": "ptnr1_label_atom_id",
                    "sym_op": "ptnr1_symmetry",
                    "model_num": None,
                },
                {
                    "auth_asym_id": "ptnr2_auth_asym_id",
                    "auth_comp_id": "ptnr2_auth_comp_id",
                    "auth_seq_id": "ptnr2_auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "pdbx_ptnr2_PDB_ins_code",
                    "atom_id": "ptnr2_label_atom_id",
                    "sym_op": "ptnr2_symmetry",
                    "model_num": None,
                },
            ],
            "struct_conf": [
                {
                    "auth_asym_id": "beg_auth_asym_id",
                    "auth_comp_id": "beg_auth_comp_id",
                    "auth_seq_id": "beg_auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "pdbx_beg_PDB_ins_code",
                    "atom_id": "auth_atom_id",
                    "sym_op": None,
                    "model_num": None,
                },
                {
                    "auth_asym_id": "end_auth_asym_id",
                    "auth_comp_id": "end_auth_comp_id",
                    "auth_seq_id": "end_auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "end_beg_PDB_ins_code",
                    "atom_id": "auth_atom_id",
                    "sym_op": None,
                    "model_num": None,
                },
            ],
            "struct_site_gen": [
                {
                    "auth_asym_id": "auth_asym_id",
                    "auth_comp_id": "auth_comp_id",
                    "auth_seq_id": "auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "pdbx_auth_ins_code",
                    "atom_id": "auth_atom_id",
                    "sym_op": "symmetry",
                    "model_num": None,
                }
            ],
            "atom_site": [
                {
                    "auth_asym_id": "auth_asym_id",
                    "auth_comp_id": "auth_comp_id",
                    "auth_seq_id": "auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "pdbx_PDB_ins_code",
                    "atom_id": "auth_atom_id",
                    "sym_op": None,
                    "model_num": "pdbx_PDB_model_num",
                }
            ],
            "pdbx_poly_seq_scheme": [
                {
                    "auth_asym_id": "pdb_strand_id",
                    "auth_comp_id": "pdb_mon_id",
                    "auth_seq_id": "pdb_seq_num",
                    "auth_seq_id_range": None,
                    # 'auth_comp_id': 'auth_mon_id',
                    # 'auth_seq_id' : 'auth_seq_num',
                    "ins_code": "pdb_ins_code",
                    "atom_id": "auth_atom_id",
                    "sym_op": None,
                    "model_num": None,
                }
            ],
            "pdbx_nonpoly_scheme": [
                {
                    "auth_asym_id": "pdb_strand_id",
                    "auth_comp_id": "pdb_mon_id",
                    "auth_seq_id": "pdb_seq_num",
                    "auth_seq_id_range": None,
                    # 'auth_comp_id': 'auth_mon_id',
                    # 'auth_seq_id' : 'auth_seq_num',
                    "ins_code": "pdb_ins_code",
                    "atom_id": "auth_atom_id",
                    "sym_op": None,
                    "model_num": None,
                }
            ],
            "struct_sheet_range": [
                {
                    "auth_asym_id": "beg_auth_asym_id",
                    "auth_comp_id": "beg_auth_comp_id",
                    "auth_seq_id": "beg_auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "pdbx_beg_PDB_ins_code",
                    "atom_id": None,
                    "sym_op": "symmetry",
                    "model_num": None,
                },
                {
                    "auth_asym_id": "end_auth_asym_id",
                    "auth_comp_id": "end_auth_comp_id",
                    "auth_seq_id": "end_auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "pdbx_end_PDB_ins_code",
                    "atom_id": None,
                    "sym_op": "symmetry",
                    "model_num": None,
                },
            ],
            "pdbx_struct_sheet_hbond": [
                {
                    "auth_asym_id": "range_1_auth_asym_id",
                    "auth_comp_id": "range_1_auth_comp_id",
                    "auth_seq_id": "range_1_auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "range_1_PDB_ins_code",
                    "atom_id": "range_1_auth_atom_id",
                    "sym_op": None,
                    "model_num": None,
                },
                {
                    "auth_asym_id": "range_2_auth_asym_id",
                    "auth_comp_id": "range_2_auth_comp_id",
                    "auth_seq_id": "range_2_auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "range_2_PDB_ins_code",
                    "atom_id": "range_2_auth_atom_id",
                    "sym_op": None,
                    "model_num": None,
                },
            ],
            "pdbx_distant_solvent_atoms": [
                {
                    "auth_asym_id": "auth_asym_id",
                    "auth_comp_id": "auth_comp_id",
                    "auth_seq_id": "auth_seq_id",
                    "auth_seq_id_range": None,
                    "ins_code": "PDB_ins_code",
                    "atom_id": "auth_atom_id",
                    "sym_op": None,
                    "model_num": "PDB_model_num",
                }
            ],
        }

    #
    #  Public methods
    #
    def getCategoriesWithContext(self):
        """  Return the list of categories with a defined graphics context.
        """
        cL = []
        cL.extend(self.__d.keys())
        cL.extend(self.__searchContextCategoryList)
        return cL

    def setPersistStorePath(self, persistFilePath):
        """  Set the path of persistent store.

        Required for categories in the __searchContextCategoryList.

        """
        self.__persistFilePath = persistFilePath

    def getGraphicsContext(self, categoryName=None, rowDictList=None):
        """ Create a command string to highlight the 3D graphics context for the
            input list of rows (stored with attribute keys) in the target category.

            Return a script command appropriate for the current 3D graphics application.
        """
        #
        if categoryName in self.__searchContextCategoryList:
            return self.__getContextViaSearch(categoryName=categoryName, rowDictList=rowDictList)
        #
        contextList = []
        for rowDict in rowDictList:
            cS = self.__createContext(categoryName=categoryName, rowDict=rowDict)
            if (cS is not None) and (len(cS) > 0):
                contextList.extend(cS)

        rL = []
        rL.append(self.__jMolSetup)
        rL.append(self.__jMolDefaultSelection)
        #
        if len(contextList) > 0:
            tS = "select ( " + ",".join(contextList) + " ) ; "
            rL.append(tS)
            lS = self.__assignLabelStyle(categoryName=categoryName)
            rL.append(lS)
            rL.append("zoomto (selected) 900; ")
        #
        return "".join(rL)

    #
    # Internal methods for here on --
    #
    def __createContext(self, categoryName=None, rowDict=None):
        """  Wrapper to create the feature selection ---
        """
        contextL = []

        if categoryName in self.__rangeTypeCategoryList:
            contextL = self.__createComponentRangeContext(categoryName=categoryName, rowDict=rowDict)
        elif categoryName in self.__d.keys():
            contextL = self.__createContextSimple(categoryName=categoryName, rowDict=rowDict)
        else:
            pass

        return contextL

    def __getContextViaSearch(self, categoryName=None, rowDictList=None):
        """ Establish the context for cases where the structural details may be determined from
        related data categories.
        """
        #
        gcS = self.__jMolDefaultSelection
        if categoryName == "struct_site":
            searchKeyName = "site_id"
            searchCategoryName = "struct_site_gen"
            #
            rDL = []
            for rowDict in rowDictList:
                keyValue = self.__getStringValue(rowDict)
                rDL.extend(self.__searchAttribute(keyValue=keyValue, searchKeyName=searchKeyName, searchCategoryName=searchCategoryName))
            #
            #
            gcS = self.getGraphicsContext(categoryName=searchCategoryName, rowDictList=rDL)
        elif categoryName == "struct_sheet":
            searchKeyName = "sheet_id"
            searchCategoryName = "struct_sheet_range"
            #
            rDL = []
            for rowDict in rowDictList:
                keyValue = self.__getStringValue(rowDict)
                rDL.extend(self.__searchAttribute(keyValue=keyValue, searchKeyName=searchKeyName, searchCategoryName=searchCategoryName))
            #
            #
            gcS = self.getGraphicsContext(categoryName=searchCategoryName, rowDictList=rDL)
        else:
            pass

        return gcS

    def __createContextSimple(self, categoryName=None, rowDict=None):
        """  Create a graphics context from the list of feature templates for this category.

             The features are treated independently and the associated contexts are returned as
             a list of JMol "atom expressions" appropriate for a JMol "select" statement.
        """
        contextL = []
        catNameLC = categoryName.lower()
        if catNameLC in self.__d:
            for fD in self.__d[catNameLC]:
                fI = self.__extractValues(fD, rowDict)
                fS = self.__assignFeatureContext(self.__app3D, fI)
                if self.__debug:
                    self.__lfh.write("+GraphicsContext3D.__createContext - feature dict     %r\n" % fD.items())
                    self.__lfh.write("+GraphicsContext3D.__createContext - row     dict     %r\n" % rowDict.items())
                    self.__lfh.write("+GraphicsContext3D.__createContext - feature instance %r\n" % fI.items())
                    self.__lfh.write("+GraphicsContext3D.__createContext - feature context  %s\n" % fS)

                if fS is not None and len(fS) > 0:
                    contextL.append(fS)
        else:
            pass
        #
        return contextL

    def __createComponentRangeContext(self, categoryName=None, rowDict=None):
        """  Create a "component range" graphics context from a pair of features templates for this category.

             The feature pair are treated as defining a contiguous range of components and a range style
             JMol "atom expression" appropriate for a JMol "select" statement is returned.
        """

        contextL = []
        catNameLC = categoryName.lower()
        if (catNameLC in self.__d) and (len(self.__d[catNameLC]) == 2):
            fD1 = self.__d[catNameLC][0]
            fD2 = self.__d[catNameLC][1]
            fI1 = self.__extractValues(fD1, rowDict)
            fI2 = self.__extractValues(fD2, rowDict)
            if self.__debug:
                self.__lfh.write("+GraphicsContext3D.__createContext - feature instance 1 %r\n" % fI1.items())
                self.__lfh.write("+GraphicsContext3D.__createContext - feature instance 2 %r\n" % fI2.items())
            #
            # Check if the features are compatible for a range context -
            #
            if (
                (fI1["auth_asym_id"] == fI2["auth_asym_id"])
                and (fI1["model_num"] == fI2["model_num"])
                and (fI1["sym_op"] == fI2["sym_op"])
                and (fI1["auth_seq_id"] is not None)
                and (fI2["auth_seq_id"] is not None)
            ):
                #
                # create the component range assignment in the first instance.
                fI1["auth_seq_id_range"] = (fI1["auth_seq_id"], fI2["auth_seq_id"])
                fI1["auth_seq_id"] = None
                fS = self.__assignFeatureContext(self.__app3D, fI1)
                if fS is not None and len(fS) > 0:
                    contextL.append(fS)
            else:
                # Default to range end points -
                fS = self.__assignFeatureContext(self.__app3D, fI1)
                if fS is not None and len(fS) > 0:
                    contextL.append(fS)
                fS = self.__assignFeatureContext(self.__app3D, fI2)
                if fS is not None and len(fS) > 0:
                    contextL.append(fS)
        else:
            pass
        #
        return contextL

    def __assignFeatureContext(self, app3D, featureInstDict=None):
        """ The general syntax for JMol is  [<compId>]<seqId>^<insertCode>:<authAsymId>.<atomId>/<model_num>
                                            [<compId>]<beg_seqId>-<end_seqId>^<insertCode>:<authAsymId>.<atomId>/<model_num>
        """
        if featureInstDict is None or featureInstDict == {}:
            return ""
        sL = []
        if app3D == "JMol":
            if featureInstDict["sym_op"] is not None and featureInstDict["sym_op"] != "1_555":
                # bail out here if the feature is not in the deposited coordinates.
                return
            if featureInstDict["auth_comp_id"] is not None:
                s = "[%s]" % featureInstDict["auth_comp_id"]
                sL.append(s)
            if featureInstDict["auth_seq_id"] is not None:
                s = "%s" % featureInstDict["auth_seq_id"]
                sL.append(s)
            if featureInstDict["auth_seq_id_range"] is not None:
                s = "%s-%s" % featureInstDict["auth_seq_id_range"]
                sL.append(s)
            if featureInstDict["ins_code"] is not None:
                s = "^%s" % featureInstDict["ins_code"]
                sL.append(s)
            if featureInstDict["auth_asym_id"] is not None:
                s = ":%s" % featureInstDict["auth_asym_id"]
                sL.append(s)
            if featureInstDict["atom_id"] is not None:
                s = ".%s" % featureInstDict["atom_id"]
                sL.append(s)
            if featureInstDict["model_num"] is not None:
                s = "/%s" % featureInstDict["model_num"]
                sL.append(s)
        else:
            sL = []
        return "".join(sL)

    def __getFirstObject(self, persistFilePath, objectName=None):
        """ Open the persistent data store and fetch the input object name from the first container.

        Note -- Will be used for more complex cases which require additional information from
        coordinate model file to resolve the graphics context.
        """
        #
        try:
            myPersist = PdbxPersist(self.__verbose, self.__lfh)
            indexD = myPersist.getIndex(dbFileName=persistFilePath)
            (firstContainerName, _type) = indexD["__containers__"][0]

            if self.__debug:
                self.__lfh.write("GraphicsContext3D.getFirstObject() container name list %r\n" % indexD.items())
            # myPersist.open(dbFileName=persistFilePath,flag='r')
            # myPersist.recover()
            # cList=myPersist.getContainerNameList()
            # self.__lfh.write("GraphicsContext3D.getFirstObject() container name list %r\n" % cList)

            myObj = myPersist.fetchOneObject(dbFileName=persistFilePath, containerName=firstContainerName, objectName=objectName)
            return myObj
        except Exception as e:
            if self.__verbose:
                self.__lfh.write("+ERROR- GraphicsContext3D.getFirstObject() Read failed for file %s %s\n" % (persistFilePath, str(e)))
                traceback.print_exc(file=self.__lfh)
            return None

    def __getStringValue(self, rowDict):
        if "id" in rowDict and len(rowDict["id"]) > 0 and rowDict["id"] != "?" and rowDict["id"] != ".":
            return rowDict["id"]
        else:
            return None

    def __searchAttribute(self, keyValue=None, searchKeyName=None, searchCategoryName=None):
        """ Search input category for rows where the attribue searchKeyName equals
            the input keyValue.

            Return a list of rows stored as dictionaries with attribute names mapped to  values.
        """
        rDL = []
        if keyValue is not None:
            myCatObj = self.__getFirstObject(persistFilePath=self.__persistFilePath, objectName=searchCategoryName)
            if myCatObj is not None:
                aL = myCatObj.getAttributeList()
                indexSearchKey = aL.index(searchKeyName)
                #
                # assemble a row dictionary list to hold search results.
                rDL = []
                for row in myCatObj.getRowList():
                    if keyValue == row[indexSearchKey]:
                        rD = {}
                        for ii, rVal in enumerate(row):
                            rD[aL[ii]] = rVal
                        # self.__lfh.write("Row dictionary: %r\n" % rD.items())
                        rDL.append(rD)
                        #
                        if self.__debug:
                            self.__lfh.write("GraphicsContext3D.__getContextViaSearch KeyValue %s row : %r\n" % (keyValue, rD.items()))
        return rDL

    def __assignLabelStyle(self, categoryName=None):
        if categoryName in self.__atomContextCategoryList:
            return "label '%c:%n:%r:%a' ; "
        elif categoryName in self.__componentContextCategoryList:
            return "label '%c:%n:%r' ; "
        elif categoryName in self.__polymerContextCategoryList:
            return "label '%c' ; "
        else:
            return "label '%c:%n:%r' ; "

    def __extractValues(self, attribDict, rowDict):
        """  Return a value dictionary
        """
        rD = {}
        for ky, attrib in attribDict.items():
            rD[ky] = None
            if attrib is not None and attrib in rowDict:
                if (len(rowDict[attrib]) > 0) and (rowDict[attrib] != "?") and (rowDict[attrib] != "."):
                    rD[ky] = rowDict[attrib]
        return rD
