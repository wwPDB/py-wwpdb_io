##
# File:  ChemRefPathInfo.py
# Date:  30-Jan-2013
#
# Updated:
# 4-Feb-2013 jdw methods to support testing with surrogate repositories.
# 5-Jul-2013 jdw renamed to ChemRefPathInfo() to avoid name conflict
# 12-Mar-2022 ep Changed API from reqObj to siteId
"""
Common methods for finding path information for chemical reference data files.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os.path

import os
import sys


from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCc


class ChemRefPathInfo(object):
    """Common methods for finding path information for chemical reference data files."""

    #

    def __init__(
        self,
        siteId=None,
        verbose=False,
        log=sys.stderr,
        testMode=False,
        # Old API - to be deprecated
        reqObj=None,
        configObj=None,
        configCommonObj=None,
    ):  # pylint: disable=unused-argument
        """Input request object and configuration (ConfigInfo()) object are used to
        supply information required to compute path details for chemical reference
        data files.
        """
        self.__verbose = verbose
        self.__lfh = log
        if configObj and configCommonObj:
            self.__cI = configObj
            self.__cIcommonAppCc = configCommonObj
        else:
            self.__siteId = siteId
            self.__cI = ConfigInfo(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            self.__cIcommonAppCc = ConfigInfoAppCc(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        self.__testMode = testMode
        #

    def getIdType(self, idCode):
        id_u = idCode.upper()
        #
        if (idCode is None) or (len(idCode) < 1):
            return None
        if len(id_u) <= 5:
            id_type = "CC"
        elif id_u[:6] == "PRDCC_":
            id_type = "PRDCC"
        elif id_u[:4] == "PRD_":
            id_type = "PRD"
        elif id_u[:4] == "FAM_":
            id_type = "PRD_FAMILY"
        else:
            id_type = None

        return id_type

    def getCcdHash(self, idCode):
        """Returns the hash code for a CCD id.  Currently first letter or last two (if extended CCD)"""
        if not idCode:
            return None

        if len(idCode) > 3:
            hash_key = idCode.upper()[-2:]
        else:
            if len(idCode) > 0:
                hash_key = idCode.upper()[0]
            else:
                hash_key = ""

        return hash_key

    def getFilePath(self, idCode, id_type=None):
        """Return the repository file path corresponding to the input reference data id code
        (CC,PRD,FAMILY or PRDCC).

        If id_type is not specified, infer it from length, etc.
        """
        #
        if id_type is None:
            id_type = self.getIdType(idCode)
        if id_type is None:
            return None
        #
        id_u = idCode.upper()
        if len(id_u) > 0:
            hash_key = id_u[-1]
        else:
            hash_key = ""
        file_name = id_u + ".cif"
        #
        if id_type == "CC":
            hash_key = self.getCcdHash(id_u)
            file_path = os.path.join(self.__cIcommonAppCc.get_site_cc_cvs_path(), hash_key, id_u, file_name)
        elif id_type == "PRDCC":
            file_path = os.path.join(self.__cIcommonAppCc.get_site_prdcc_cvs_path(), hash_key, file_name)
        elif id_type == "PRD":
            file_path = os.path.join(self.__cIcommonAppCc.get_site_prd_cvs_path(), hash_key, file_name)
        elif id_type == "PRD_FAMILY":
            file_path = os.path.join(self.__cIcommonAppCc.get_site_family_cvs_path(), hash_key, file_name)
        else:
            file_path = None

        return file_path

    def getFileDir(self, idCode, id_type=None):
        """Return the repository file directory corresponding to the input reference data id code
        (CC,PRD,FAMILY or PRDCC).

        If id_type is not specified, infer it from length, etc.
        """
        #
        filePath = self.getFilePath(idCode, id_type)
        if filePath:
            return os.path.dirname(filePath)
        return None

    def getProjectPath(self, idCode=None, id_type=None):
        """
        Return the project path for an input reference data id code
        (CC,PRD,FAMILY or PRDCC).
        """
        #
        if id_type is None:
            id_type = self.getIdType(idCode)
        if id_type is None:
            return None
        #
        if id_type == "CC":
            return self.__cIcommonAppCc.get_site_cc_cvs_path()
        elif id_type == "PRDCC":
            return self.__cIcommonAppCc.get_site_prdcc_cvs_path()
        elif id_type == "PRD":
            return self.__cIcommonAppCc.get_site_prd_cvs_path()
        elif id_type == "PRD_FAMILY":
            return self.__cIcommonAppCc.get_site_family_cvs_path()
        else:
            return None

    def getCvsProjectInfo(self, idCode, id_type=None):
        """Assign the CVS project name and relative path based on the input ID code.

        The project name represents the directory containing the checked out
        repository within the sandbox directory.  Relative path identifies gives
        the target path for the target file within the repository.
        """
        rel_path = None
        project_name = None

        if id_type is None:
            id_type = self.getIdType(idCode)
        if id_type is None:
            return project_name, rel_path
        #
        project_name = self.assignCvsProjectName(id_type)
        if id_type == "CC":
            hash_key = self.getCcdHash(idCode)
            rel_path = os.path.join(hash_key, idCode, idCode + ".cif")
        elif id_type == "PRDCC":
            rel_path = os.path.join(idCode[-1], idCode + ".cif")
        elif id_type == "PRD":
            rel_path = os.path.join(idCode[-1], idCode + ".cif")
        elif id_type == "PRD_FAMILY":
            rel_path = os.path.join(idCode[-1], idCode + ".cif")
        else:
            pass

        return project_name, rel_path

    def assignIdCodeFromFileName(self, filePath):
        if self.__verbose:
            self.__lfh.write("+PathInfo.assignIdCodeFromFileName() input file path: %s\n" % filePath)

        if (filePath is not None) and (len(filePath) > 7):
            file_name = os.path.basename(filePath)
            definition_id, _ = os.path.splitext(file_name)
            return definition_id.upper()

        return None

    def assignCvsProjectName(self, repType):
        """Assign the CVS project name from the input repository type.

        This wrapper provides for a testing mode which assign an existing  surogate
        repository project with the same organization as the requested repository type.
        """
        project_name = None

        if repType is None:
            return project_name
        #
        if self.__testMode:
            if repType == "CC":
                project_name = "test-ligand-v1"
            elif repType == "PRDCC":
                project_name = "test-project-v1"
            elif repType == "PRD":
                project_name = "test-project-v1"
            elif repType == "PRD_FAMILY":
                project_name = "test-project-v1"
            else:
                pass
        else:
            if repType == "CC":
                project_name = self.__cI.get("SITE_REFDATA_PROJ_NAME_CC")
            elif repType == "PRDCC":
                project_name = self.__cI.get("SITE_REFDATA_PROJ_NAME_PRDCC")
            elif repType == "PRD":
                project_name = self.__cI.get("SITE_REFDATA_PROJ_NAME_PRD")
            elif repType == "PRD_FAMILY":
                project_name = self.__cI.get("SITE_REFDATA_PROJ_NAME_PRD_FAMILY")
            else:
                pass

        return project_name
