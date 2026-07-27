# ruff: noqa: S101

import os

import pytest
import yaml
from wwpdb.utils.config.ConfigInfo import ConfigInfo

from wwpdb.io.misc.ResourceAllocation import ResourceAllocation

SAMPLE_CONFIG = {
    "defaults": {"cpus": "all/2", "memory": "8G"},
    "jobs": {
        "entity_transform_img_generator": {"cpus": 4, "memory": "16G"},
        "cif_validator": {"cpus": "all"},
        "map_calculation": {"cpus": "all/4", "memory": "32G"},
    },
}


@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "resource_allocation.yml"
    path.write_text(yaml.safe_dump(SAMPLE_CONFIG))
    return str(path)


def test_loads_config_from_explicit_file(config_file):
    ra = ResourceAllocation(config_file=config_file)
    assert ra._config == SAMPLE_CONFIG


def test_falls_back_silently_when_config_file_missing(tmp_path):
    missing = str(tmp_path / "does_not_exist.yml")
    ra = ResourceAllocation(config_file=missing)
    assert ra._config == {}


def test_falls_back_silently_when_config_key_unset(monkeypatch):
    monkeypatch.setattr(ConfigInfo, "get", lambda self, keyWord, default=None: default)  # noqa: ARG005
    ra = ResourceAllocation(site_id="TEST")
    assert ra._config == {}


def test_resolves_config_path_via_config_info(monkeypatch, config_file):
    def fake_get(self, keyWord, default=None):  # noqa: ARG001
        if keyWord == "RESOURCE_ALLOCATION_CONFIG_FILE":
            return config_file
        return default

    monkeypatch.setattr(ConfigInfo, "get", fake_get)
    ra = ResourceAllocation(site_id="TEST")
    assert ra._config == SAMPLE_CONFIG
