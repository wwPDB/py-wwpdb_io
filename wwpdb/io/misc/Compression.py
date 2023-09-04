import os
import shutil
import logging
import tarfile

from wwpdb.utils.config.ConfigInfo import ConfigInfo


logger = logging.getLogger()
logger.setLevel(logging.INFO)
config = ConfigInfo()

ARCHIVE_DIR = os.path.join(config.get("SITE_ARCHIVE_STORAGE_PATH"), "archive")
COLD_ARCHIVE_DIR = os.path.join(config.get("SITE_ARCHIVE_STORAGE_PATH"), "cold_archive")


def compress(dep_id: str, overwrite: bool = False):
    if not dep_id.startswith("D_"):
        raise Exception("Invalid deposition id")

    dep_archive = os.path.join(ARCHIVE_DIR, dep_id)
    dep_tarball = os.path.join(COLD_ARCHIVE_DIR, f"{dep_id}.tar.gz")

    # os.chdir(ARCHIVE_DIR)

    if not os.path.exists(dep_archive):
        raise Exception(f"Deposition {dep_id} does not exist")

    if os.path.exists(dep_tarball) and not overwrite:
        raise Exception(f"{dep_id} is already compressed. Set `overwrite` to True to overwrite it.")

    logging.info("Compressing %s to %s", dep_archive, dep_tarball)

    with tarfile.open(dep_tarball, "w:gz", debug=1) as tf:
        tf.add(dep_archive, arcname=dep_id)
        shutil.rmtree(dep_archive)

    return dep_tarball


def decompress(dep_id: str, overwrite: bool = False):
    dep_archive = os.path.join(ARCHIVE_DIR, dep_id)
    dep_tarball = os.path.join(COLD_ARCHIVE_DIR, f"{dep_id}.tar.gz")

    if not os.path.exists(dep_tarball):
        raise Exception(f"{dep_id} is not compressed")

    if os.path.exists(dep_archive) and not overwrite:
        raise Exception(f"{dep_id} is already decompressed. Set `overwrite` to True to overwrite it.")

    with tarfile.open(dep_tarball, "r:gz") as tf:
        tf.extractall(ARCHIVE_DIR)
        logging.info(f"{dep_id} extracted successfully")
