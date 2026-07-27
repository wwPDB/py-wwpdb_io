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


def test_falls_back_silently_when_config_file_malformed(tmp_path):
    path = tmp_path / "malformed.yml"
    path.write_text("key: [unclosed")
    ra = ResourceAllocation(config_file=str(path))
    assert ra._config == {}


def test_falls_back_silently_when_config_root_is_not_a_dict(tmp_path):
    path = tmp_path / "not_a_dict.yml"
    path.write_text(yaml.safe_dump([1, 2, 3]))
    ra = ResourceAllocation(config_file=str(path))
    assert ra._config == {}


def test_get_cpus_from_job_override(config_file):
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("entity_transform_img_generator") == 4


def test_get_cpus_all_from_job_override(config_file, monkeypatch):
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(8)), raising=False)
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("cif_validator") == 8


def test_get_cpus_all_over_n_from_job_override(config_file, monkeypatch):
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(8)), raising=False)
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("map_calculation") == 2  # 8 // 4


def test_get_cpus_falls_back_to_defaults(config_file, monkeypatch):
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(8)), raising=False)
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("unlisted_job") == 4  # defaults.cpus = all/2, 8 // 2


def test_get_cpus_falls_back_to_system_when_config_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(6)), raising=False)
    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    assert ra.get_cpus("anything") == 6


def test_get_cpus_plain_number_string(tmp_path):
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"jobs": {"job_a": {"cpus": "4"}}}))
    ra = ResourceAllocation(config_file=str(path))
    assert ra.get_cpus("job_a") == 4


def test_get_cpus_falls_back_to_cpu_count_off_linux(tmp_path, monkeypatch):
    monkeypatch.delattr(os, "sched_getaffinity", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 3)
    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    assert ra.get_cpus("anything") == 3


def test_get_memory_mb_from_job_override(config_file):
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_memory_mb("entity_transform_img_generator") == 16384


def test_get_memory_mb_falls_back_to_defaults(config_file):
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_memory_mb("unlisted_job") == 8192  # defaults.memory = 8G


def test_get_memory_mb_falls_back_to_defaults_for_job_without_override(config_file):
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_memory_mb("cif_validator") == 8192  # no job-level memory key, so defaults.memory = 8G applies


def test_get_memory_mb_all_is_unconstrained(tmp_path):
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"defaults": {"memory": "all"}}))
    ra = ResourceAllocation(config_file=str(path))
    assert ra.get_memory_mb("anything") is None


def test_get_memory_mb_megabyte_suffix(tmp_path):
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"jobs": {"job_a": {"memory": "8M"}}}))
    ra = ResourceAllocation(config_file=str(path))
    assert ra.get_memory_mb("job_a") == 8


def test_get_memory_mb_unconstrained_when_config_empty(tmp_path):
    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    assert ra.get_memory_mb("anything") is None


def test_get_memory_mb_plain_number_string(tmp_path):
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"jobs": {"job_a": {"memory": "5"}}}))
    ra = ResourceAllocation(config_file=str(path))
    assert ra.get_memory_mb("job_a") == 5
