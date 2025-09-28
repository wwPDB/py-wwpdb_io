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


class ReleaseFileNames:
    def __init__(self) -> None:
        #                context   public    for_rel   gzip_pub, gzip_rel

        self.__mapping: dict[str, tuple[str, str, bool, bool]] = {
            "model": ("{}.cif", "{}.cif", True, True),
            "sf": ("r{}sf.ent", "{}-sf.cif", True, False),
            "cs": ("{}_cs.str", "{}_cs.str", True, False),
            "nmr_data": ("{}_nmr-data.str", "{}_nmr-data.str", True, True),
            "emdxml": ("{}-v30.xml", "{}_v3.xml", False, False),
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

        # public for_rel
        self.__accession_remap = {
            "emdxml": ("hyphen", "underscore"),
            "emdmap": ("underscore", "underscore"),
            "emdfsc": ("underscore", "underscore"),
        }

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
        return self.__get_emdb_hyphen_format(accession)

    def get_lower_emdb_underscore_format(self, accession: str) -> str:
        return self.__get_emdb_underscore_format(accession)

    def __process_remap(self, remap_type: str, accession: str) -> str:
        """looks up the accession remapping in __accession_remap"""
        if remap_type == "hyphen":
            return self.__get_emdb_hyphen_format(accession)
        if remap_type == "underscore":
            return self.__get_emdb_underscore_format(accession)
        msg = "unknown EMDB file remapping: {}".format(remap_type)
        raise NameError(msg)  # pragma: no cover

    def __do_accession_remap(self, content: str, accession: str, for_release: bool) -> str:
        """does accession remapping"""
        if content in self.__accession_remap:
            (public, release) = self.__accession_remap[content]
            if for_release:
                accession = self.__process_remap(release, accession)
            else:
                accession = self.__process_remap(public, accession)
        return accession

    def __getfname(self, content: str, accession: str, for_release: bool) -> str:
        """Retrieves the released content file name with compression"""
        assert content in self.__mapping  # noqa: S101
        (public, release, pub_gzip, rel_gzip) = self.__mapping[content]
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
        return self.__getfname("model", accession, for_release)

    def get_structure_factor(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("sf", accession, for_release)

    def get_chemical_shifts(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("cs", accession, for_release)

    def get_emdb_xml(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("emdxml", accession, for_release)

    def get_emdb_map(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("emdmap", accession, for_release)

    def get_emdb_fsc(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("emdfsc", accession, for_release)

    def get_validation_pdf(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("validpdf", accession, for_release)

    def get_validation_full_pdf(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("validpdffull", accession, for_release)

    def get_validation_xml(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("validxml", accession, for_release)

    def get_validation_cif(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("validcif", accession, for_release)

    def get_validation_png(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("validpng", accession, for_release)

    def get_validation_svg(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("validsvg", accession, for_release)

    def get_validation_2fofc(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("valid2fo", accession, for_release)

    def get_validation_fofc(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("validfo", accession, for_release)

    def get_nmr_data(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("nmr_data", accession, for_release)

    def get_validation_image_tar(self, accession: str, for_release: bool = False) -> str:
        return self.__getfname("validimagetar", accession, for_release)
