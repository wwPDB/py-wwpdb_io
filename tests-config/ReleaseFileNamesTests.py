##
# File:    ReleaseFileNamesTests.py
# Date:    30-Jul-2026
#
# Updates:
##
"""
Tests for computing for_release/public file names for entry content types

"""

from __future__ import annotations

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "ezra.peisach@rcsb.org"

# ruff: noqa: PT027
import unittest

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames


class ReleaseFileNamesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.__rfn = ReleaseFileNames()
        self.__accession = "1abc"
        self.__emdb_accession = "EMD-1234"

    def testGetModel(self) -> None:
        self.assertEqual(self.__rfn.get_model(self.__accession), "1abc.cif.gz")
        self.assertEqual(self.__rfn.get_model(self.__accession, for_release=True), "1abc.cif.gz")

    def testGetStructureFactor(self) -> None:
        self.assertEqual(self.__rfn.get_structure_factor(self.__accession), "r1abcsf.ent.gz")
        self.assertEqual(self.__rfn.get_structure_factor(self.__accession, for_release=True), "1abc-sf.cif")

    def testGetChemicalShifts(self) -> None:
        self.assertEqual(self.__rfn.get_chemical_shifts(self.__accession), "1abc_cs.str.gz")
        self.assertEqual(self.__rfn.get_chemical_shifts(self.__accession, for_release=True), "1abc_cs.str")

    def testGetNmrData(self) -> None:
        self.assertEqual(self.__rfn.get_nmr_data(self.__accession), "1abc_nmr-data.str.gz")
        self.assertEqual(self.__rfn.get_nmr_data(self.__accession, for_release=True), "1abc_nmr-data.str.gz")

    def testGetEmdbXml(self) -> None:
        # accession remapping: public uses hyphen form, for_release uses underscore form
        self.assertEqual(self.__rfn.get_emdb_xml(self.__emdb_accession), "emd-1234-v30.xml")
        self.assertEqual(self.__rfn.get_emdb_xml(self.__emdb_accession, for_release=True), "emd_1234_v3.xml")

    def testGetEmdbMap(self) -> None:
        # accession remapping: both public and for_release use underscore form
        self.assertEqual(self.__rfn.get_emdb_map(self.__emdb_accession), "emd_1234.map.gz")
        self.assertEqual(self.__rfn.get_emdb_map(self.__emdb_accession, for_release=True), "emd_1234.map.gz")

    def testGetEmdbFsc(self) -> None:
        self.assertEqual(self.__rfn.get_emdb_fsc(self.__emdb_accession), "emd_1234_fsc.xml")
        self.assertEqual(self.__rfn.get_emdb_fsc(self.__emdb_accession, for_release=True), "emd_1234_fsc.xml")

    def testGetValidationPdf(self) -> None:
        self.assertEqual(self.__rfn.get_validation_pdf(self.__accession), "1abc_validation.pdf")
        self.assertEqual(self.__rfn.get_validation_pdf(self.__accession, for_release=True), "1abc_validation.pdf")

    def testGetValidationFullPdf(self) -> None:
        self.assertEqual(self.__rfn.get_validation_full_pdf(self.__accession), "1abc_full_validation.pdf")
        self.assertEqual(self.__rfn.get_validation_full_pdf(self.__accession, for_release=True), "1abc_full_validation.pdf")

    def testGetValidationXml(self) -> None:
        self.assertEqual(self.__rfn.get_validation_xml(self.__accession), "1abc_validation.xml")
        self.assertEqual(self.__rfn.get_validation_xml(self.__accession, for_release=True), "1abc_validation.xml")

    def testGetValidationCif(self) -> None:
        self.assertEqual(self.__rfn.get_validation_cif(self.__accession), "1abc_validation.cif")
        self.assertEqual(self.__rfn.get_validation_cif(self.__accession, for_release=True), "1abc_validation.cif")

    def testGetValidationPng(self) -> None:
        self.assertEqual(self.__rfn.get_validation_png(self.__accession), "1abc_multipercentile_validation.png")
        self.assertEqual(self.__rfn.get_validation_png(self.__accession, for_release=True), "1abc_multipercentile_validation.png")

    def testGetValidationSvg(self) -> None:
        self.assertEqual(self.__rfn.get_validation_svg(self.__accession), "1abc_multipercentile_validation.svg")
        self.assertEqual(self.__rfn.get_validation_svg(self.__accession, for_release=True), "1abc_multipercentile_validation.svg")

    def testGetValidation2fofc(self) -> None:
        self.assertEqual(self.__rfn.get_validation_2fofc(self.__accession), "1abc_validation_2fo-fc_map_coef.cif")
        self.assertEqual(self.__rfn.get_validation_2fofc(self.__accession, for_release=True), "1abc_validation_2fo-fc_map_coef.cif")

    def testGetValidationFofc(self) -> None:
        self.assertEqual(self.__rfn.get_validation_fofc(self.__accession), "1abc_validation_fo-fc_map_coef.cif")
        self.assertEqual(self.__rfn.get_validation_fofc(self.__accession, for_release=True), "1abc_validation_fo-fc_map_coef.cif")

    def testGetValidationImageTar(self) -> None:
        self.assertEqual(self.__rfn.get_validation_image_tar(self.__accession), "1abc_validation_images.tar")
        self.assertEqual(self.__rfn.get_validation_image_tar(self.__accession, for_release=True), "1abc_validation_images.tar")

    def testGetLowerEmdbHyphenFormat(self) -> None:
        self.assertEqual(self.__rfn.get_lower_emdb_hyphen_format(self.__emdb_accession), "emd-1234")

    def testGetLowerEmdbUnderscoreFormat(self) -> None:
        self.assertEqual(self.__rfn.get_lower_emdb_underscore_format(self.__emdb_accession), "emd_1234")


def suiteReleaseFileNamesTests() -> unittest.TestSuite:  # pragma: no cover
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ReleaseFileNamesTests("testGetModel"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetStructureFactor"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetChemicalShifts"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetNmrData"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetEmdbXml"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetEmdbMap"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetEmdbFsc"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidationPdf"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidationFullPdf"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidationXml"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidationCif"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidationPng"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidationSvg"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidation2fofc"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidationFofc"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetValidationImageTar"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetLowerEmdbHyphenFormat"))
    suiteSelect.addTest(ReleaseFileNamesTests("testGetLowerEmdbUnderscoreFormat"))
    return suiteSelect


if __name__ == "__main__":  # pragma: no cover
    mySuite = suiteReleaseFileNamesTests()
    unittest.TextTestRunner(verbosity=2).run(mySuite)
