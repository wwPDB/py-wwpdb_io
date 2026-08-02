##
# File:  ReleaseFileNames.py
# Date:  Nov-2019  J. Berrisford
#
# Updated:
#  15-Nov-2019 E. Peisach  Code cleanups
#
##
"""
Methods for finding file names for entries within the for_release area of ftp archive

In general the methods take accession and for_release flags.  for_release indicates the for_release directory.

"""

from __future__ import annotations

from datetime import date
from typing import Final, Literal

ContentType = Literal[
    "model",
    "sf",
    "cs",
    "nmr_data",
    "emdxml",
    "emdmap",
    "emdmetadata",
    "emdfsc",
    "validpdf",
    "validpdffull",
    "validxml",
    "validcif",
    "validpng",
    "validsvg",
    "valid2fo",
    "validfo",
    "validimagetar",
]


class ReleaseFileNames:
    """Computes file names for entry content types as they appear publicly (on the FTP/HTTP archive)
    or within the for_release directory, including any EMDB accession remapping and gzip compression."""

    def __init__(self, **kwargs: bool) -> None:
        self.__use_beta_filenames: bool = kwargs.get("use_beta_filenames", self._is_on_or_after_20270717())

        #                context   public    for_rel   gzip_pub, gzip_rel

        base_mapping: dict[ContentType, tuple[str, str, bool, bool]] = {
            "model": ("{}.cif", "{}.cif", True, True),
            "cs": ("{}_cs.str", "{}_cs.str", True, False),
            "nmr_data": ("{}_nmr-data.str", "{}_nmr-data.str", True, True),
            "emdxml": ("{}-v30.xml", "{}_v3.xml", False, False),
            "emdmetadata": ("{}.cif", "{}.cif", True, True),
            "emdmap": ("{}.map", "{}.map", True, True),
            "emdfsc": ("{}_fsc.xml", "{}_fsc.xml", False, False),
            "validpdf": ("{}_validation.pdf", "{}_validation.pdf", False, False),
            "validpdffull": ("{}_full_validation.pdf", "{}_full_validation.pdf", False, False),
            "validxml": ("{}_validation.xml", "{}_validation.xml", False, False),
            "validcif": ("{}_validation.cif", "{}_validation.cif", False, False),
            "validpng": ("{}_multipercentile_validation.png", "{}_multipercentile_validation.png", False, False),
            "validsvg": ("{}_multipercentile_validation.svg", "{}_multipercentile_validation.svg", False, False),
            "valid2fo": ("{}_validation_2fo-fc_map_coef.cif", "{}_validation_2fo-fc_map_coef.cif", False, False),
            "validfo": ("{}_validation_fo-fc_map_coef.cif", "{}_validation_fo-fc_map_coef.cif", False, False),
            "validimagetar": ("{}_validation_images.tar", "{}_validation_images.tar", False, False),
        }

        legacy_sf_mapping: dict[ContentType, tuple[str, str, bool, bool]] = {
            "sf": ("r{}sf.ent", "{}-sf.cif", True, False),
        }

        # for_release_beta - sf files are compressed
        beta_sf_mapping: dict[ContentType, tuple[str, str, bool, bool]] = {
            "sf": ("r{}sf.ent", "{}-sf.cif", True, True),
        }

        self.__legacy_mapping: Final = {**base_mapping, **legacy_sf_mapping}
        self.__beta_mapping: Final = {**base_mapping, **beta_sf_mapping}

        # public for_rel
        self.__accession_remap: Final = {
            "emdxml": ("hyphen", "underscore"),
            "emdmap": ("underscore", "underscore"),
            "emdfsc": ("underscore", "underscore"),
            "emdmetadata": ("hyphen", "hyphen"),
        }

    @staticmethod
    def _is_on_or_after_20270717() -> bool:
        """Returns True if the current local date is on or after 17-Jul-2027."""
        return date.today() >= date(2027, 7, 17)

    @staticmethod
    def __get_emdb_number(accession: str) -> str:
        """gets the EMDB number from the accession"""
        return accession[4:]
        # return accession.split("-")[-1]

    def __get_emdb_underscore_format(self, accession: str) -> str:
        """returns lower case emdb accession with underscore"""
        return "emd_{}".format(self.__get_emdb_number(accession))

    def __get_emdb_hyphen_format(self, accession: str) -> str:
        """returns lower case emdb accessin with hypen"""
        return "emd-{}".format(self.__get_emdb_number(accession))

    def get_lower_emdb_hyphen_format(self, accession: str) -> str:
        """Returns lower case EMDB accession with a hyphen, e.g. "emd-1234"."""
        return self.__get_emdb_hyphen_format(accession)

    def get_lower_emdb_underscore_format(self, accession: str) -> str:
        """Returns lower case EMDB accession with an underscore, e.g. "emd_1234"."""
        return self.__get_emdb_underscore_format(accession)

    def __process_remap(self, remap_type: str, accession: str) -> str:
        """looks up the accession remapping in __accession_remap"""
        if remap_type == "hyphen":
            return self.__get_emdb_hyphen_format(accession)
        if remap_type == "underscore":
            return self.__get_emdb_underscore_format(accession)
        msg = "unknown EMDB file remapping: {}".format(remap_type)
        raise NameError(msg)  # pragma: no cover

    def __do_accession_remap(self, content: ContentType, accession: str, for_release: bool) -> str:
        """does accession remapping"""
        if content in self.__accession_remap:
            (public, release) = self.__accession_remap[content]
            if for_release:
                accession = self.__process_remap(release, accession)
            else:
                accession = self.__process_remap(public, accession)
        return accession

    def __getfname(self, content: ContentType, accession: str, for_release: bool) -> str:
        """Retrieves the released content file name with compression"""

        assert content in self.__legacy_mapping  # noqa: S101
        assert content in self.__beta_mapping  # noqa: S101
        (public, release, pub_gzip, rel_gzip) = self.__beta_mapping[content] if self.__use_beta_filenames else self.__legacy_mapping[content]
        accession = self.__do_accession_remap(accession=accession, content=content, for_release=for_release)
        if for_release:
            base = release
            gzipflag = rel_gzip
        else:
            base = public
            gzipflag = pub_gzip
        suffix = ".gz" if gzipflag else ""

        fname = base.format(accession) + suffix

        return fname

    def get_model(self, accession: str, for_release: bool = False) -> str:
        """Returns the model coordinate file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("model", accession, for_release)

    def get_structure_factor(self, accession: str, for_release: bool = False) -> str:
        """Returns the structure factor file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("sf", accession, for_release)

    def get_chemical_shifts(self, accession: str, for_release: bool = False) -> str:
        """Returns the chemical shifts file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("cs", accession, for_release)

    def get_emdb_xml(self, accession: str, for_release: bool = False) -> str:
        """Returns the EMDB header XML file name.

        Args:
            accession: EMDB accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("emdxml", accession, for_release)

    def get_emdb_map(self, accession: str, for_release: bool = False) -> str:
        """Returns the EMDB map file name.

        Args:
            accession: EMDB accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("emdmap", accession, for_release)

    def get_emdb_metadata(self, accession: str, for_release: bool = False) -> str:
        """Returns the EMDB metadata file name.

        Args:
            accession: EMDB accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("emdmetadata", accession, for_release)

    def get_emdb_fsc(self, accession: str, for_release: bool = False) -> str:
        """Returns the EMDB FSC file name.

        Args:
            accession: EMDB accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("emdfsc", accession, for_release)

    def get_validation_pdf(self, accession: str, for_release: bool = False) -> str:
        """Returns the validation report PDF file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("validpdf", accession, for_release)

    def get_validation_full_pdf(self, accession: str, for_release: bool = False) -> str:
        """Returns the full validation report PDF file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("validpdffull", accession, for_release)

    def get_validation_xml(self, accession: str, for_release: bool = False) -> str:
        """Returns the validation report XML file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("validxml", accession, for_release)

    def get_validation_cif(self, accession: str, for_release: bool = False) -> str:
        """Returns the validation report mmCIF file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("validcif", accession, for_release)

    def get_validation_png(self, accession: str, for_release: bool = False) -> str:
        """Returns the multi-percentile validation plot PNG file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("validpng", accession, for_release)

    def get_validation_svg(self, accession: str, for_release: bool = False) -> str:
        """Returns the multi-percentile validation plot SVG file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("validsvg", accession, for_release)

    def get_validation_2fofc(self, accession: str, for_release: bool = False) -> str:
        """Returns the validation 2Fo-Fc map coefficients file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("valid2fo", accession, for_release)

    def get_validation_fofc(self, accession: str, for_release: bool = False) -> str:
        """Returns the validation Fo-Fc map coefficients file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("validfo", accession, for_release)

    def get_nmr_data(self, accession: str, for_release: bool = False) -> str:
        """Returns the combined NMR data file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("nmr_data", accession, for_release)

    def get_validation_image_tar(self, accession: str, for_release: bool = False) -> str:
        """Returns the validation images tar file name.

        Args:
            accession: entry accession code.
            for_release: if True, returns the for_release file name; otherwise the public file name.
        """
        return self.__getfname("validimagetar", accession, for_release)
