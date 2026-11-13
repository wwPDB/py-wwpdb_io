from __future__ import annotations

import logging
import os
from typing import Literal, Optional

from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames

logger = logging.getLogger(__name__)


class LocalFTPPathInfo:
    """Provides path information for files staged on the public archive site (PDB and EMDB)."""

    def __init__(self, siteId: Optional[str] = None) -> None:
        """Load FTP root directory paths from site configuration for the given siteId."""
        self.__siteId = siteId
        self.__cI = ConfigInfo(siteId=self.__siteId)

        self.__ftp_pdb_root: Optional[str] = self.__cI.get("SITE_PDB_FTP_ROOT_DIR")
        self.__ftp_emdb_root: Optional[str] = self.__cI.get("SITE_EMDB_FTP_ROOT_DIR")
        self.__mapping: dict[str, str] = {
            "model": "mmCIF",
            "structure_factors": "structure_factors",
            "chemical_shifts": "nmr_chemical_shifts",
            "nmr_data": "nmr_data",
        }

    def __get_mapping(self, file_type: Literal["model", "structure_factors", "chemical_shifts", "nmr_data"]) -> str:
        """Return the archive subdirectory name corresponding to the given file_type."""
        return self.__mapping[file_type]

    def set_ftp_pdb_root(self, ftp_pdb_root: Optional[str]) -> None:
        """Set the root directory of the public PDB archive site."""
        if ftp_pdb_root:
            self.__ftp_pdb_root = ftp_pdb_root

    def get_ftp_pdb_root(self) -> Optional[str]:
        """Return the root directory of the public PDB archive site."""
        return self.__ftp_pdb_root

    def set_ftp_emdb_root(self, ftp_emdb_root: Optional[str]) -> None:
        """Set the root directory of the public EMDB archive site."""
        if ftp_emdb_root is not None:
            self.__ftp_emdb_root = ftp_emdb_root

    def get_ftp_emdb_root(self) -> Optional[str]:
        """Return the root directory of the public EMDB archive site."""
        return self.__ftp_emdb_root

    def get_ftp_pdb(self) -> str:
        """Return the path to the PDB structures directory on the archive site, or "" if the root is not configured."""
        if self.__ftp_pdb_root:
            return os.path.join(self.__ftp_pdb_root, "pdb", "data", "structures", "all")
        return ""

    def get_ftp_emdb(self) -> str:
        """Return the path to the EMDB structures directory on the archive site, or "" if the root is not configured."""
        if self.__ftp_emdb_root:
            return os.path.join(self.__ftp_emdb_root, "emdb", "structures")
        return ""

    def get_model_path(self) -> str:
        """Return the archive directory path for model files."""
        return os.path.join(self.get_ftp_pdb(), self.__get_mapping("model"))

    def get_sf_path(self) -> str:
        """Return the archive directory path for structure factor files."""
        return os.path.join(self.get_ftp_pdb(), self.__get_mapping("structure_factors"))

    def get_cs_path(self) -> str:
        """Return the archive directory path for chemical shift files."""
        return os.path.join(self.get_ftp_pdb(), self.__get_mapping("chemical_shifts"))

    def get_nmr_data_path(self) -> str:
        """Return the archive directory path for NMR data files."""
        return os.path.join(self.get_ftp_pdb(), self.__get_mapping("nmr_data"))

    def get_model_fname(self, accession: str) -> str:
        """Return the full archive path to the model file for the given accession."""
        model_file_name = ReleaseFileNames().get_model(accession=accession, for_release=False)
        return os.path.join(self.get_model_path(), model_file_name)

    def get_structure_factors_fname(self, accession: str) -> str:
        """Return the full archive path to the structure factor file for the given accession."""
        sf_file_name = ReleaseFileNames().get_structure_factor(accession=accession, for_release=False)
        return os.path.join(self.get_sf_path(), sf_file_name)

    def get_chemical_shifts_fname(self, accession: str) -> str:
        """Return the full archive path to the chemical shift file for the given accession."""
        cs_file_name = ReleaseFileNames().get_chemical_shifts(accession=accession, for_release=False)
        return os.path.join(self.get_cs_path(), cs_file_name)

    def get_nmr_data_fname(self, accession: str) -> str:
        """Return the full archive path to the NMR data file for the given accession."""
        nmr_data_file_name = ReleaseFileNames().get_nmr_data(accession=accession, for_release=False)
        return os.path.join(self.get_nmr_data_path(), nmr_data_file_name)
