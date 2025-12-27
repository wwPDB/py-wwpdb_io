# ruff: noqa: S101,PT011,B017

import importlib
import json
import logging
import os
import shutil
from unittest.mock import Mock

import pytest
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoData import ConfigInfoData

from wwpdb.io.misc.Compression import Compression

logging.basicConfig(level=logging.INFO)


def compile_site_config():
    from wwpdb.utils.config.ConfigInfoFileExec import ConfigInfoFileExec  # noqa: PLC0415

    ci = ConfigInfoFileExec()
    ci.writeConfigCache(siteLoc="test", siteId="TEST")


@pytest.fixture
def mock_config(monkeypatch):  # noqa: ARG001
    with open("./wwpdb/io/tests-io/fixtures/site-config/test/test/ConfigInfoFileCache.json") as fp:
        test_config = json.load(fp)
    monkeypatch.setattr(ConfigInfoData, "getConfigDictionary", lambda s: test_config["TEST"])  # noqa: ARG005
    module = importlib.import_module("wwpdb.io.misc.Compression")
    importlib.reload(module)


@pytest.fixture
def config():
    from wwpdb.utils.config.ConfigInfo import ConfigInfo  # noqa: PLC0415 pylint: disable=redefined-outer-name,reimported

    return ConfigInfo(siteId="TEST")


@pytest.fixture
def archive_dir(mock_config, config):  # noqa: ARG001 pylint: disable=unused-argument,redefined-outer-name
    onedep_base = config.get("SITE_ARCHIVE_STORAGE_PATH")

    if onedep_base is None or not onedep_base.startswith("/tmp"):  # noqa: S108
        raise Exception("Error getting test archive dir")  # noqa: EM101,TRY002,TRY003 pylint: disable=broad-exception-raised

    l_archive_dir = os.path.join(onedep_base, "archive")
    cold_archive_dir = os.path.join(onedep_base, "cold_archive")
    os.makedirs(l_archive_dir, exist_ok=True)
    os.makedirs(cold_archive_dir, exist_ok=True)

    yield l_archive_dir

    shutil.rmtree(onedep_base)


def test_compression(monkeypatch, archive_dir):  # noqa: ARG001  pylint: disable=unused-argument,redefined-outer-name
    dep_dir = os.path.join(archive_dir, "D_800001")
    os.makedirs(dep_dir, exist_ok=True)
    open(os.path.join(dep_dir, "foo"), "w").close()

    mock_db = Mock()
    mock_db.runSelectNQ.return_value = [["", ""]]
    compression = Compression(ConfigInfo(), mock_db)

    # compression
    compression.compress(dep_id="D_800001")

    assert os.path.exists(os.path.join(archive_dir, "..", "cold_archive", "D_800001.tar.gz"))
    assert not os.path.exists(dep_dir)

    # non-existing deposition
    with pytest.raises(Exception):
        compression.compress(dep_id="miltão")

    # decompression
    compression.decompress(dep_id="D_800001")

    assert os.path.exists(dep_dir)
    assert os.path.exists(os.path.join(dep_dir, "foo"))


def test_overwrite_compression(monkeypatch, archive_dir):  # noqa: ARG001  pylint: disable=unused-argument,redefined-outer-name
    dep_dir = os.path.join(archive_dir, "D_800001")
    os.makedirs(dep_dir, exist_ok=True)

    mock_db = Mock()
    mock_db.runSelectNQ.return_value = [["", ""]]
    compression = Compression(ConfigInfo(), mock_db)
    compression.compress(dep_id="D_800001")

    with pytest.raises(Exception):
        compression.compress(dep_id="D_800001")

    os.makedirs(dep_dir, exist_ok=True)
    open(os.path.join(dep_dir, "foo"), "w").close()
    compression.compress(dep_id="D_800001", overwrite=True)

    compression.decompress(dep_id="D_800001")

    with pytest.raises(Exception):
        compression.decompress(dep_id="D_800001")


def test_corrupted_file(archive_dir):  # pylint: disable=redefined-outer-name
    dep_dir = os.path.join(archive_dir, "D_800001")
    cold_archive = os.path.join(archive_dir, "..", "cold_archive")
    os.makedirs(dep_dir, exist_ok=True)
    shutil.copy("./wwpdb/io/tests-io/fixtures/corrupt.tar.gz", os.path.join(cold_archive, "D_800001.tar.gz"))
    compression = Compression(ConfigInfo(), Mock())

    with pytest.raises(Exception):
        # early end of file
        compression.check_tarball(dep_id="D_800001")

    assert os.path.exists(os.path.join(cold_archive, "D_800001.tar.gz"))


def test_count(archive_dir):  # pylint: disable=redefined-outer-name
    cold_archive = os.path.join(archive_dir, "..", "cold_archive")
    compression = Compression(ConfigInfo(), Mock())

    for i in range(5):
        open(os.path.join(cold_archive, f"{i}.tar.gz"), "w").close()

    for i in range(3):
        open(os.path.join(cold_archive, f"{i}.txt"), "w").close()

    assert compression.get_compressed_count() == 5


def test_compression_precheck(archive_dir, monkeypatch):  # noqa: ARG001  pylint: disable=unused-argument,redefined-outer-name
    dep_dir = os.path.join(archive_dir, "D_800001")
    os.makedirs(dep_dir, exist_ok=True)

    mock_db = Mock()
    mock_db.runSelectNQ.return_value = [["*", ""]]

    compression = Compression(ConfigInfo(), mock_db)

    with pytest.raises(Exception):
        compression.compress(dep_id="D_800001")

    mock_db.return_value.runSelectNQ.return_value = [["foo", "WFM"]]

    with pytest.raises(Exception) as e:
        compression.compress(dep_id="D_800001", overwrite=True)

    assert str(e.value) == "Deposition D_800001 cannot be compressed"

    def mock_select_comm(table, select, where):  # noqa: ARG001 pylint: disable=unused-argument
        if table == "communication":
            return [["working"]]
        return [["", ""]]

    mock_db.return_value.runSelectNQ = mock_select_comm

    with pytest.raises(Exception) as e:
        compression.compress(dep_id="D_800001", overwrite=True)

    assert str(e.value) == "Deposition D_800001 cannot be compressed"
