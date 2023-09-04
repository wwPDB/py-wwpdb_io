import os
import sys
import json
import pytest
import shutil
import importlib
from unittest import mock

from wwpdb.io.misc import Compression
from wwpdb.utils.config.ConfigInfoData import ConfigInfoData


def compile_site_config():
    from wwpdb.utils.config.ConfigInfoFileExec import ConfigInfoFileExec
    ci = ConfigInfoFileExec()
    ci.writeConfigCache(siteLoc="test", siteId="TEST")


@pytest.fixture
def mock_config(monkeypatch):
    with open("./wwpdb/io/tests-io/fixtures/site-config/test/test/ConfigInfoFileCache.json") as fp:
        test_config = json.load(fp)
    monkeypatch.setattr(ConfigInfoData, "getConfigDictionary", lambda s: test_config["TEST"])
    importlib.reload(Compression)


@pytest.fixture
def config():
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    return ConfigInfo(siteId="TEST")


@pytest.fixture
def archive_dir(mock_config, config):
    onedep_base = config.get("SITE_ARCHIVE_STORAGE_PATH")

    if onedep_base is None or not onedep_base.startswith("/tmp"):
        raise Exception("Error getting test archive dir")

    archive_dir = os.path.join(onedep_base, "archive")
    cold_archive_dir = os.path.join(onedep_base, "cold_archive")
    os.makedirs(archive_dir, exist_ok=True)
    os.makedirs(cold_archive_dir, exist_ok=True)

    yield archive_dir

    # shutil.rmtree(onedep_base)


def test_compression(archive_dir):
    dep_dir = os.path.join(archive_dir, "D_800001")
    os.makedirs(dep_dir, exist_ok=True)
    open(os.path.join(dep_dir, "foo"), "w").close()

    # compression
    Compression.compress(dep_id="D_800001")

    assert os.path.exists(os.path.join(archive_dir, "..", "cold_archive", "D_800001.tar.gz"))
    assert not os.path.exists(dep_dir)

    # non-existing deposition
    with pytest.raises(Exception):
        Compression.compress(dep_id="maracatu")

    # decompression
    Compression.decompress(dep_id="D_800001")

    assert os.path.exists(dep_dir)
    assert os.path.exists(os.path.join(dep_dir, "foo"))


def test_overwrite_compression(archive_dir):
    dep_dir = os.path.join(archive_dir, "D_800001")
    os.makedirs(dep_dir, exist_ok=True)
    Compression.compress(dep_id="D_800001")

    with pytest.raises(Exception):
        Compression.compress(dep_id="D_800001")

    os.makedirs(dep_dir, exist_ok=True)
    open(os.path.join(dep_dir, "foo"), "w").close()
    Compression.compress(dep_id="D_800001", overwrite=True)

    Compression.decompress(dep_id="D_800001")

    with pytest.raises(Exception):
        Compression.decompress(dep_id="D_800001")
