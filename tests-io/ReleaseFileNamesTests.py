##
#
# File:    ReleaseFileNamesTests.py
# Author:  E. Peisach
# Date:    29-Dev-2019
# Version: 0.001
#
# Updated:
#
##
"""
Test cases for ReleaseFileNames()

"""
# ruff: noqa: T201

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import unittest

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames


class ReleaseFileNamesTests(unittest.TestCase):
    def setUp(self):
        pass

    def testNames(self):
        """Tests that retrieving different file names is successful"""
        rf = ReleaseFileNames()
        print("Pub model %s" % rf.get_model("1abc"))
        print("Rel model %s" % rf.get_model("1abc", True))
        print("Pub sf: %s" % rf.get_structure_factor("1abc"))
        print("Rel sf: %s" % rf.get_structure_factor("1abc", True))
        print("Pub cs: %s" % rf.get_chemical_shifts("1abc"))
        print("Rel cs: %s" % rf.get_chemical_shifts("1abc", True))
        print("Pub emdxml: %s" % rf.get_emdb_xml("EMD-1234"))
        print("Rel emdxml: %s" % rf.get_emdb_xml("EMD-1234", True))
        print("Pub emdmap: %s" % rf.get_emdb_map("EMD-1234"))
        print("Rel emdmap: %s" % rf.get_emdb_map("EMD-1234", True))
        print("Pub emdfsc: %s" % rf.get_emdb_fsc("EMD-1234"))
        print("Rel emdfsc: %s" % rf.get_emdb_fsc("EMD-1234", True))
        print("Pub validpdf: %s" % rf.get_validation_pdf("1abc"))
        print("Rel validpdf: %s" % rf.get_validation_pdf("1abc", True))
        print("Pub validfullpdf: %s" % rf.get_validation_full_pdf("1abc"))
        print("Rel validfullpdf: %s" % rf.get_validation_full_pdf("1abc", True))
        print("Pub validxml: %s" % rf.get_validation_xml("1abc"))
        print("Rel validxml: %s" % rf.get_validation_xml("1abc", True))
        print("Pub validsvg: %s" % rf.get_validation_svg("1abc"))
        print("Rel validsvg: %s" % rf.get_validation_svg("1abc", True))
        print("Pub validpng: %s" % rf.get_validation_png("1abc"))
        print("Rel validpng: %s" % rf.get_validation_png("1abc", True))
        print("Pub 2fo-fc: %s" % rf.get_validation_2fofc("1abc"))
        print("Rel 2fo-fc: %s" % rf.get_validation_2fofc("1abc", True))
        print("Pub fo-fc: %s" % rf.get_validation_fofc("1abc"))
        print("Rel fo-fc: %s" % rf.get_validation_fofc("1abc", True))
        # External use...
        rf.get_lower_emdb_hyphen_format("EMD-1234")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
