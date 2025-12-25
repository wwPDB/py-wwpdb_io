##
#
# File:    FormatOutTests.py
# Author:  E. Peisach
# Date:    29-Dev-2019
# Version: 0.001
#
# Updated:
#
##
"""
Test cases for FormatOut()

"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import os
import sys
import unittest

from wwpdb.io.misc.FormatOut import FormatOut


class DataFileTests(unittest.TestCase):
    def setUp(self):
        pass

    def testFO(self):
        """Tests formatting of interesting structures to ensure does not crash"""
        list_in = ["L1", "L2", "L3", "L4", "L5"]
        tuple_in = ("T1", "T2", "T3", "T4", "T5")
        dict_in = {}
        for i in range(1, 10):
            t = ["D1", list_in, tuple_in]
            dict_in[i] = t

        out = FormatOut()
        out.autoFormat("unitTest1 results", dict_in, 3, 3)
        out.writeStream(sys.stdout)
        out.write(os.devnull)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
