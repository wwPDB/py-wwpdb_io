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
import glob
import shutil

import logging
logger = logging.getLogger(__name__)

from wwpdb.utils.config.ConfigInfo import ConfigInfo, getSiteId


class ReleasePathInfo(object):
    def __init__(self, siteId=None):
        self.__siteId = siteId
        self.__cI = ConfigInfo(siteId=self.__siteId)
        
    def getForReleasePath(self, subdir=None, version='current'):
        """Returns path to for-release directory. 

        Input Parameters:
        subdir: If specified,  must be one of "added", "modified", "obsolete", 
                "emd", "val-reports".
        version: "current" or "previous"

        returns path, or raises exception
        """
        basedir = os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'),
                               'for-release')

        if version not in ['current', 'previous']:
            raise NameError('version %s not allowed' % version)

        if version == 'previous':
            basedir = os.path.join(basedir, 'previous')
        
        if subdir:
            if subdir not in ['added', 'modified', 'obsolete', 'emd',
                              'val-reports',
                              'em-val-reports']:
                raise NameError('subdir %s not allowed' % subdir)

            basedir = os.path.join(basedir, subdir)

        return basedir
        
