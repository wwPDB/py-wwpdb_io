##
# File: FileImportTests.py
# Date:  10-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for wwpdb.io.file - simply import everything to ensure imports work"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest

from wwpdb.io.file.DataExchange import DataExchange  # noqa: F401 pylint: disable=unused-import
from wwpdb.io.file.DataFile import DataFile  # noqa: F401
from wwpdb.io.file.mmCIFUtil import mmCIFUtil  # noqa: F401
from wwpdb.io.file.DataMaintenance import DataMaintenance  # noqa: F401 pylint: disable=unused-import
from wwpdb.io.file.ValidateXml import ValidateXml  # noqa: F401 pylint: disable=unused-import


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        _vc = DataFile()
        _vc = mmCIFUtil()  # noqa: F841
        # Will not function without a reqObj
        # vc = DataExchange()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
