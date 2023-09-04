import os
import shutil
import logging
import tarfile
from fnmatch import fnmatch

from wwpdb.utils.config.ConfigInfo import ConfigInfo


logger = logging.getLogger()
logger.setLevel(logging.INFO)
config = ConfigInfo()

ARCHIVE_DIR = os.path.join(config.get("SITE_ARCHIVE_STORAGE_PATH"), "archive")
# maybe this should be read from a separate variable to allow this location to be separate from archive
COLD_ARCHIVE_DIR = os.path.join(config.get("SITE_ARCHIVE_STORAGE_PATH"), "cold_archive")


# this should go in the constructor of a class
def check_cold_location():
    if not os.path.exists(COLD_ARCHIVE_DIR):
        raise Exception(f"{COLD_ARCHIVE_DIR} does not exist")


def is_compressed(dep_id: str):
    check_cold_location()

    dep_tarball = os.path.join(COLD_ARCHIVE_DIR, f"{dep_id}.tar.gz")

    if os.path.exists(dep_tarball):
        return True

    return False


def check_tarball(dep_id: str):
    check_cold_location()

    dep_tarball = os.path.join(COLD_ARCHIVE_DIR, f"{dep_id}.tar.gz")

    if not is_compressed(dep_id=dep_id):
        raise Exception(f"{dep_id} is not compressed")

    with tarfile.open(dep_tarball, "r:gz") as fp:
        fp.getmembers()


def compress(dep_id: str, overwrite: bool = False):
    check_cold_location()

    if not dep_id.startswith("D_"):
        raise Exception("Invalid deposition id")

    dep_archive = os.path.join(ARCHIVE_DIR, dep_id)
    dep_tarball = os.path.join(COLD_ARCHIVE_DIR, f"{dep_id}.tar.gz")

    if not os.path.exists(dep_archive):
        raise Exception(f"Deposition {dep_id} does not exist")

    if is_compressed(dep_id=dep_id) and not overwrite:
        raise Exception(f"{dep_id} is already compressed. Set `overwrite` to True to overwrite it.")

    logging.info("Compressing %s to %s", dep_archive, dep_tarball)

    with tarfile.open(dep_tarball, "w:gz", debug=1) as tf:
        tf.add(dep_archive, arcname=dep_id)

    # this will throw if the file is corrupt
    check_tarball(dep_id=dep_id)
    shutil.rmtree(dep_archive)

    return dep_tarball


def decompress(dep_id: str, overwrite: bool = False):
    check_cold_location()

    dep_archive = os.path.join(ARCHIVE_DIR, dep_id)
    dep_tarball = os.path.join(COLD_ARCHIVE_DIR, f"{dep_id}.tar.gz")

    if not is_compressed(dep_id=dep_id):
        raise Exception(f"{dep_id} is not compressed")

    if os.path.exists(dep_archive) and not overwrite:
        raise Exception(f"{dep_id} is already decompressed. Set `overwrite` to True to overwrite it.")

    with tarfile.open(dep_tarball, "r:gz") as tf:
        tf.extractall(ARCHIVE_DIR)
        logging.info(f"{dep_id} extracted successfully")


def get_compressed_count():
    check_cold_location()

    for root, dirs, files in os.walk(COLD_ARCHIVE_DIR):
        tar_files = [tf for tf in files if fnmatch(tf, "*.tar.gz")]

    return len(tar_files)
