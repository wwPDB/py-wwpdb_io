import os
import shutil
import logging
import tarfile
from fnmatch import fnmatch


logger = logging.getLogger()


class Compression:
    def __init__(self, config, dbapi) -> None:
        # injecting dbapi so the connection can be opened only once
        # by the calling code, in case of multiple entries
        self._archive_dir = os.path.join(config.get("SITE_ARCHIVE_STORAGE_PATH"), "archive")
        # maybe this should be read from a separate variable to allow this location to be separate from archive
        self._cold_archive_dir = os.path.join(config.get("SITE_ARCHIVE_STORAGE_PATH"), "cold_archive")

        if not os.path.exists(self._cold_archive_dir):
            raise Exception(f"{self._cold_archive_dir} does not exist")  # pylint: disable=broad-exception-raised)

        self._dbapi = dbapi

    def _can_be_compressed(self, dep_id: str):
        rows = self._dbapi.runSelectNQ(table="deposition", select=["notify", "locking"], where={"dep_set_id": dep_id})

        if len(rows) == 0:
            raise Exception(f"Couldn't find entry in table `status.deposition` for deposition `{dep_id}`")  # pylint: disable=broad-exception-raised)

        if rows[0][0] in ("*", "R*", "T*", "R", "TR", "T", "NT*", "NTR*", "NT", "NTR"):
            logger.warning(f"Deposition `{dep_id}` cannot be compressed due to `notify` value `{rows[0][0]}`")  # pylint: disable=logging-fstring-interpolation
            return False

        if rows[0][1].lower() == "wfm":
            logger.warning(f"Deposition `{dep_id}` cannot be compressed as it's unlocked (locking = {rows[0][1]})")  # pylint: disable=logging-fstring-interpolation
            return False

        rows = self._dbapi.runSelectNQ(table="communication", select=["status"], where={"dep_set_id": dep_id})

        if rows[0][0].lower() == "working":
            logger.warning(f"Deposition `{dep_id}` cannot be compressed as it's being processed by the WFE")  # pylint: disable=logging-fstring-interpolation
            return False

        return True

    def is_compressed(self, dep_id: str):
        dep_tarball = os.path.join(self._cold_archive_dir, f"{dep_id}.tar.gz")

        if os.path.exists(dep_tarball):
            return True

        return False

    def check_tarball(self, dep_id: str):
        dep_tarball = os.path.join(self._cold_archive_dir, f"{dep_id}.tar.gz")

        if not self.is_compressed(dep_id=dep_id):
            raise Exception(f"{dep_id} is not compressed")  # pylint: disable=broad-exception-raised)

        with tarfile.open(dep_tarball, "r:gz") as fp:
            fp.getmembers()

    def compress(self, dep_id: str, overwrite: bool = False):
        if not dep_id.startswith("D_"):
            raise Exception("Invalid deposition id")  # pylint: disable=broad-exception-raised)

        dep_archive = os.path.join(self._archive_dir, dep_id)
        dep_tarball = os.path.join(self._cold_archive_dir, f"{dep_id}.tar.gz")

        if self.is_compressed(dep_id=dep_id) and not overwrite:
            raise Exception(f"{dep_id} is already compressed. Set `overwrite` to True to overwrite it.")  # pylint: disable=broad-exception-raised)

        if not os.path.exists(dep_archive):
            raise Exception(f"Deposition {dep_id} does not exist")  # pylint: disable=broad-exception-raised)

        if not self._can_be_compressed(dep_id=dep_id):
            raise Exception(f"Deposition {dep_id} cannot be compressed")  # pylint: disable=broad-exception-raised)

        logging.info("Compressing %s to %s", dep_archive, dep_tarball)

        with tarfile.open(dep_tarball, "w:gz", debug=1) as tf:
            tf.add(dep_archive, arcname=dep_id)

        # this will throw if the file is corrupt
        self.check_tarball(dep_id=dep_id)
        shutil.rmtree(dep_archive)

        return dep_tarball

    def decompress(self, dep_id: str, overwrite: bool = False):
        dep_archive = os.path.join(self._archive_dir, dep_id)
        dep_tarball = os.path.join(self._cold_archive_dir, f"{dep_id}.tar.gz")

        if not self.is_compressed(dep_id=dep_id):
            raise Exception(f"{dep_id} is not compressed")  # pylint: disable=broad-exception-raised)

        if os.path.exists(dep_archive) and not overwrite:
            raise Exception(f"{dep_id} is already decompressed. Set `overwrite` to True to overwrite it.")  # pylint: disable=broad-exception-raised)

        with tarfile.open(dep_tarball, "r:gz") as tf:
            tf.extractall(self._archive_dir)
            logging.info(f"{dep_id} extracted successfully")  # pylint: disable=logging-fstring-interpolation

    def get_compressed_count(self):
        for _root, _dirs, files in os.walk(self._cold_archive_dir):
            tar_files = [tf for tf in files if fnmatch(tf, "*.tar.gz")]

        return len(tar_files)
