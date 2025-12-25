##
#
# File:    ValidateXmlTests.py
# Author:  E. Peisach
# Date:    30-Dev-2019
# Version: 0.001
#
# Updated:
#
##
"""
Test cases for ValidateXml

"""
__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest
import os

from wwpdb.io.file.ValidateXml import ValidateXml

HERE = os.path.abspath(os.path.dirname(__file__))
TOPDIR = os.path.dirname(HERE)
mockTopPath = os.path.join(TOPDIR, "wwpdb", "mock-data")


class ReleaseFileNamesTests(unittest.TestCase):
    def setUp(self):
        self.__xrayxmlfile = os.path.join(mockTopPath, "MISC", "3ltq_validation.xml")
        self.__nmrxmlfile = os.path.join(mockTopPath, "MISC", "6ne8_validation.xml")

    def testValidate(self):
        """Tests parsing of validation XML file"""
        for fname in [self.__xrayxmlfile, self.__nmrxmlfile]:
            obj = ValidateXml(fname)
            # Ignore returns
            obj.getClashOutliers()
            obj.getCalculatedCompleteness()
            obj.getCsMappingErrorNumber()
            obj.getCsMappingWarningNumber()
            obj.getNotFoundInStructureCsList()
            obj.getNotFoundResidueInStructureCsList()
            obj.getCsOutliers()
            obj.getCsReferencingOffsetFlag()
            obj.getSummary()
            obj.getOutlier("torsion-outlier")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
