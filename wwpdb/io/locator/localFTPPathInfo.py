import logging
import os
import os.path

from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.io.locator.ReleaseFileNames import ReleaseFileNames

logger = logging.getLogger(__name__)


class LocalFTPPathInfo(object):
    def __init__(self, siteId=None):
        self.__siteId = siteId
        self.__cI = ConfigInfo(siteId=self.__siteId)

        self.ftp_pdb_root = self.__cI.get("SITE_PDB_FTP_ROOT_DIR")
        self.ftp_emdb_root = self.__cI.get("SITE_EMDB_FTP_ROOT_DIR")
        self.__mapping = {
            "model": "mmCIF",
            "structure_factors": "structure_factors",
            "chemical_shifts": "nmr_chemical_shifts",
            "nmr_data": "nmr_data",
        }

    def __get_mapping(self, file_type):
        return self.__mapping.get(file_type)

    def set_ftp_pdb_root(self, ftp_pdb_root):
        if ftp_pdb_root:
            self.ftp_pdb_root = ftp_pdb_root

    def set_ftp_emdb_root(self, ftp_emdb_root):
        if ftp_emdb_root:
            self.ftp_emdb_root = ftp_emdb_root

    def get_ftp_pdb(self):
        if self.ftp_pdb_root:
            return os.path.join(self.ftp_pdb_root, "pdb", "data", "structures", "all")
        return ""

    def get_ftp_emdb(self):
        if self.ftp_emdb_root:
            return os.path.join(self.ftp_emdb_root, "emdb", "structures")
        return ""

    def get_model_path(self):
        return os.path.join(self.get_ftp_pdb(), self.__get_mapping("model"))

    def get_sf_path(self):
        return os.path.join(self.get_ftp_pdb(), self.__get_mapping("structure_factors"))

    def get_cs_path(self):
        return os.path.join(self.get_ftp_pdb(), self.__get_mapping("chemical_shifts"))

    def get_nmr_data_path(self):
        return os.path.join(self.get_ftp_pdb(), self.__get_mapping("nmr_data"))

    def get_model_fname(self, accession):
        model_file_name = ReleaseFileNames().get_model(accession=accession, for_release=False)
        return os.path.join(self.get_model_path(), model_file_name)

    def get_structure_factors_fname(self, accession):
        sf_file_name = ReleaseFileNames().get_structure_factor(accession=accession, for_release=False)
        return os.path.join(self.get_sf_path(), sf_file_name)

    def get_chemical_shifts_fname(self, accession):
        cs_file_name = ReleaseFileNames().get_chemical_shifts(accession=accession, for_release=False)
        return os.path.join(self.get_cs_path(), cs_file_name)

    def get_nmr_data_fname(self, accession):
        nmr_data_file_name = ReleaseFileNames().get_nmr_data(accession=accession, for_release=False)
        return os.path.join(self.get_nmr_data_path(), nmr_data_file_name)
