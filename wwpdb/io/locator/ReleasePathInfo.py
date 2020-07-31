##
# File:  ReleasePathInfo.py
# Date:  11-Nov-2019  E. Peisach
#
# Updated:
##
"""
Common methods for finding path information for release directories used in the system.

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Apache 2.0"
__version__ = "V0.07"

import os
import os.path
import logging

from wwpdb.utils.config.ConfigInfo import ConfigInfo

logger = logging.getLogger(__name__)


class ReleasePathInfo(object):
    def __init__(self, siteId=None):
        self.__siteId = siteId
        self.__cI = ConfigInfo(siteId=self.__siteId)
        self.current_folder_name = "current"
        self.previous_folder_name = "previous"

    def getForReleasePath(self, subdir=None, version="current", accession=None, em_sub_path=None):
        """Returns path to for-release directory.

        Input Parameters:
        subdir: If specified,  must be one of "added", "modified", "obsolete",
                "emd", "val-reports".
        version: "current" or "previous"

        returns path, or raises exception
        """
        basedir = self.get_for_release_path()

        if version not in [self.current_folder_name, self.previous_folder_name]:
            raise NameError("version %s not allowed" % version)

        if version == self.previous_folder_name:
            basedir = os.path.join(basedir, self.previous_folder_name)

        if subdir:
            if subdir not in ["added", "modified", "obsolete", "emd", "val_reports", "em_val_reports", "val_images"]:
                raise NameError("subdir %s not allowed" % subdir)

            basedir = os.path.join(basedir, subdir)

            if em_sub_path and accession:
                if em_sub_path not in [
                    "header",
                    "map",
                    "fsc",
                    "images",
                    "masks",
                    "other",
                    "validation",
                ]:
                    raise NameError("em_sub_path %s not allowed" % em_sub_path)

                basedir = os.path.join(basedir, accession.upper(), em_sub_path)

        return basedir

    def get_for_release_path(self):
        """Returns path to for_release directory"""
        return os.path.join(self.__cI.get("SITE_ARCHIVE_STORAGE_PATH"), "for_release")

    def get_for_release_beta_path(self):
        """Returns path to for_release_beta directory"""
        return os.path.join(self.__cI.get("SITE_ARCHIVE_STORAGE_PATH"), "for_release_beta")

    def get_for_release_version_path(self):
        """Returns path to for_release_version directory"""
        return os.path.join(self.__cI.get("SITE_ARCHIVE_STORAGE_PATH"), "for_release_version")

    def get_added_path(self, version=None):
        if version is None:
            version = self.current_folder_name
        return self.getForReleasePath(subdir="added", version=version)

    def get_previous_added_path(self):
        return self.get_added_path(version=self.previous_folder_name)

    def get_modified_path(self, version=None):
        if version is None:
            version = self.current_folder_name
        return self.getForReleasePath(subdir="modified", version=version)

    def get_previous_modified_path(self):
        return self.get_modified_path(version=self.previous_folder_name)

    def get_emd_subfolder_path(self, accession, subfolder, version=None):
        if version is None:
            version = self.current_folder_name
        return self.getForReleasePath(subdir="emd", accession=accession, em_sub_path=subfolder, version=version)

    def get_previous_emd_subfolder_path(self, accession, subfolder):
        return self.get_emd_subfolder_path(accession=accession, subfolder=subfolder, version=self.previous_folder_name)
