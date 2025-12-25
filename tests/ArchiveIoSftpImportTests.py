##
# File: ArchiveIoSftpImportTests.py
# Date:  06-Oct-2018  E. Peisach
#
# Updates:
##
"""Test cases for emdb - simply import everything to ensure imports work"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest

from wwpdb.io.sftp.ArchiveIoSftp import ArchiveIoSftp


class ImportTests(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def testInstantiate(self) -> None:
        aio = ArchiveIoSftp()  # noqa: F841 pylint: disable=unused-variable


if __name__ == "__main__":
    unittest.main()
