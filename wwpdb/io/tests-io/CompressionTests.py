import os
import sys
import pytest
import shutil
import importlib.util
from unittest import mock

from wwpdb.io.misc.Compression import compress #, decompress

# ---
# mocking site-config
# maybe this should go to a different file and serve as module fixture
patcher = mock.patch.dict(os.environ, {"TOP_WWPDB_SITE_CONFIG_DIR": "wwpdb/io/tests-io/fixtures/site-config/"})
patcher.start()

cache_path = os.path.abspath("./wwpdb/io/tests-io/fixtures/site-config/test/test/ConfigInfoFileCache.py")
spec = importlib.util.spec_from_file_location("ConfigInfoFileCache", cache_path)
module = importlib.util.module_from_spec(spec)
sys.modules["ConfigInfoFileCache"] = module
spec.loader.exec_module(module)

from ConfigInfoFileCache import ConfigInfoFileCache
# ---


def compile_site_config():
    from wwpdb.utils.config.ConfigInfoFileExec import ConfigInfoFileExec
    ci = ConfigInfoFileExec()
    ci.writeConfigCache(siteLoc="test", siteId="TEST")


@pytest.fixture
def config(monkeypatch):
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    monkeypatch.setattr("wwpdb.utils.config.ConfigInfoData.ConfigInfoFileCache", ConfigInfoFileCache)
    return ConfigInfo(siteId="TEST")


@pytest.fixture
def archive_dir(monkeypatch, config):
    onedep_base = config.get("TOP_DATA_DIR")

    if onedep_base is None or not onedep_base.startswith("/tmp"):
        raise Exception("Error getting test archive dir")

    archive_dir = os.path.join(onedep_base, "data", "archive")
    os.makedirs(archive_dir, exist_ok=True)

    yield archive_dir

    shutil.rmtree(onedep_base)


def test_compression(archive_dir):
    dep_dir = os.path.join(archive_dir, "D_800001")
    os.makedirs(dep_dir, exist_ok=True)
    open(os.path.join(dep_dir, "foo"), "w").close()

    # compression
    compress(dep_id="D_800001")

    assert os.path.exists(os.path.join(archive_dir, "..", "cold_archive", "D_800001.tar.gz"))
    assert not os.path.exists(dep_dir)

    # non-existing deposition
    with pytest.raises(Exception):
        compress(dep_id="maracatu")

    # # decompression
    # decompress(dep_id="D_800001")

    # assert os.path.exists(os.path.join(dep_dir))
    # assert os.path.exists(os.path.join(dep_dir, "foo"))


def test_overwrite_compression(archive_dir):
    dep_dir = os.path.join(archive_dir, "D_800001")
    os.makedirs(dep_dir, exist_ok=True)
    compress(dep_id="D_800001")

    with pytest.raises(Exception):
        compress(dep_id="D_800001")

    open(os.path.join(dep_dir, "foo")).close()
    compress(dep_id="D_800001", overwrite=True)

    # decompress(dep_id="D_800001")


patcher.stop()
