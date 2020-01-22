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

    def getForReleasePath(self, subdir=None, version="current", accession=None, em_sub_path=None):
        """Returns path to for-release directory.

        Input Parameters:
        subdir: If specified,  must be one of "added", "modified", "obsolete",
                "emd", "val-reports".
        version: "current" or "previous"

        returns path, or raises exception
        """
        basedir = os.path.join(self.__cI.get("SITE_ARCHIVE_STORAGE_PATH"), "for_release")

        if version not in ["current", "previous"]:
            raise NameError("version %s not allowed" % version)

        if version == "previous":
            basedir = os.path.join(basedir, "previous")

        if subdir:
            if subdir not in [
                "added",
                "modified",
                "obsolete",
                "emd",
                "val_reports",
                "em_val_reports",
            ]:
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
