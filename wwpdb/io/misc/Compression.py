import os
import shutil
import logging
import tarfile

from wwpdb.utils.config.ConfigInfo import ConfigInfo

config = ConfigInfo()

ARCHIVE_DIR = os.path.join(config.get("SITE_ARCHIVE_STORAGE_PATH"), "archive")
COLD_ARCHIVE_DIR = os.path.join(config.get("SITE_ARCHIVE_STORAGE_PATH"), "cold_archive")


def compress(dep_id: str, overwrite: bool = False):
    depid_archive = os.path.join(ARCHIVE_DIR, dep_id)
    depid_tarball = os.path.join(COLD_ARCHIVE_DIR, f"{dep_id}.tar.gz")

    os.chdir(ARCHIVE_DIR)

    print("Compressing %s" % depid_archive)
    if not os.path.exists(depid_archive):
        raise Exception(f"Deposition {dep_id} does not exist")

    if os.path.exists(depid_tarball) and not overwrite:
        raise Exception(f"{dep_id} is already compressed. Set `overwrite` to True to overwrite it.")

    with tarfile.open(depid_tarball, "w:gz", debug=1) as tf:
        tf.add(dep_id)

        if dep_id.startswith("D_"): # better safe than sorry
            shutil.rmtree(depid_archive)

    return depid_tarball


def decompress(dep_id: str, overwrite: bool = False):
    pass
