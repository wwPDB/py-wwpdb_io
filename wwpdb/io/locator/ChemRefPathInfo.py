##
# File:  ChemRefPathInfo.py
# Date:  30-Jan-2013
#
# Updated:
# 4-Feb-2013 jdw methods to support testing with surrogate repositories.
# 5-Jul-2013 jdw renamed to ChemRefPathInfo() to avoid name conflict
# s
"""
Common methods for finding path information for chemical reference data files.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import sys
import os
import os.path


class ChemRefPathInfo(object):
    """ Common methods for finding path information for chemical reference data files.
    """
#

    def __init__(self, reqObj=None, configObj=None, configCommonObj=None, testMode=False, verbose=False, log=sys.stderr):
        """ Input request object and configuration (ConfigInfo()) object are used to
            supply information required to compute path details for chemical reference
            data files.
        """
        self.__verbose = verbose
        self.__lfh = log
        self.__cI = configObj
        self.__cIcommon = configCommonObj
        self.__reqObj = reqObj
        self.__testMode = testMode
        #

    def getIdType(self, idCode):
        idU = idCode.upper()
        #
        if ((idCode is None) or (len(idCode) < 1)):
            return None
        if len(idU) <= 3:
            idType = "CC"
        elif idU[:6] == "PRDCC_":
            idType = "PRDCC"
        elif idU[:4] == "PRD_":
            idType = "PRD"
        elif idU[:4] == "FAM_":
            idType = "PRD_FAMILY"
        else:
            idType = None

        return idType

    def getFilePath(self, idCode):
        """ Return the repository file path corresponding to the input reference data id code
           (CC,PRD,FAMILY or PRDCC).
        """
        #
        idType = self.getIdType(idCode)
        if idType is None:
            return None
        #
        idU = idCode.upper()
        hashKey = idU[-1]
        fileName = idU + ".cif"
        #
        if idType == "CC":
            hashKey = idU[0]
            filePath = os.path.join(self.__cIcommon.get_site_cc_cvs_path(), hashKey, idU, fileName)
        elif idType == "PRDCC":
            filePath = os.path.join(self.__cIcommon.get_site_prdcc_cvs_path(), hashKey, fileName)
        elif idType == "PRD":
            filePath = os.path.join(self.__cIcommon.get_site_prd_cvs_path(), hashKey, fileName)
        elif idType == "PRD_FAMILY":
            filePath = os.path.join(self.__cIcommon.get_site_family_cvs_path(), hashKey, fileName)
        else:
            filePath = None

        return filePath

    def getProjectPath(self, idCode):
        """
        Return the project path for an input reference data id code
        (CC,PRD,FAMILY or PRDCC).
        """
        #
        idType = self.getIdType(idCode)
        if idType is None:
            return None
        #
        if idType == "CC":
            return self.__cIcommon.get_site_cc_cvs_path()
        elif idType == "PRDCC":
            return self.__cIcommon.get_site_prdcc_cvs_path()
        elif idType == "PRD":
            return self.__cIcommon.get_site_prd_cvs_path()
        elif idType == "PRD_FAMILY":
            return self.__cIcommon.get_site_family_cvs_path()
        else:
            return None

    def getCvsProjectInfo(self, idCode):
        """  Assign the CVS project name and relative path based on the input ID code.

             The project name represents the directory containing the checked out
             repository within the sandbox directory.  Relative path identifies gives
             the target path for the target file within the repository.
        """
        relPath = None
        projectName = None

        idType = self.getIdType(idCode)
        if idType is None:
            return (projectName, relPath)
        #
        projectName = self.assignCvsProjectName(idType)
        if (idType == "CC"):
            relPath = os.path.join(idCode[0], idCode, idCode + '.cif')
        elif (idType == "PRDCC"):
            relPath = os.path.join(idCode[-1], idCode + '.cif')
        elif (idType == "PRD"):
            relPath = os.path.join(idCode[-1], idCode + '.cif')
        elif (idType == "PRD_FAMILY"):
            relPath = os.path.join(idCode[-1], idCode + '.cif')
        else:
            pass

        return (projectName, relPath)

    def assignIdCodeFromFileName(self, filePath):
        if (self.__verbose):
            self.__lfh.write("+PathInfo.assignIdCodeFromFileName() input file path: %s\n" % filePath)

        if ((filePath is not None) and (len(filePath) > 7)):
            (pth, fileName) = os.path.split(filePath)
            (id, ext) = os.path.splitext(fileName)
            return id.upper()

        return None

    def assignCvsProjectName(self, repType):
        """  Assign the CVS project name from the input repository type.

             This wrapper provides for a testing mode which assign an existing  surogate
             repository project with the same organization as the requested repository type.
        """
        projectName = None

        if repType is None:
            return projectName
        #
        if self.__testMode:
            if (repType == "CC"):
                projectName = 'test-ligand-v1'
            elif (repType == "PRDCC"):
                projectName = 'test-project-v1'
            elif (repType == "PRD"):
                projectName = 'test-project-v1'
            elif (repType == "PRD_FAMILY"):
                projectName = 'test-project-v1'
            else:
                pass
        else:
            if (repType == "CC"):
                projectName = self.__cI.get('SITE_REFDATA_PROJ_NAME_CC')
            elif (repType == "PRDCC"):
                projectName = self.__cI.get('SITE_REFDATA_PROJ_NAME_PRDCC')
            elif (repType == "PRD"):
                projectName = self.__cI.get('SITE_REFDATA_PROJ_NAME_PRD')
            elif (repType == "PRD_FAMILY"):
                projectName = self.__cI.get('SITE_REFDATA_PROJ_NAME_PRD_FAMILY')
            else:
                pass

        return projectName
