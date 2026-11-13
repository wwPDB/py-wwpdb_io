# ruff: noqa: S101

import logging
import os
from pathlib import Path
from typing import Any, Dict

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
def config_file(tmp_path: Path) -> str:
    path = tmp_path / "resource_allocation.yml"
    path.write_text(yaml.safe_dump(SAMPLE_CONFIG))
    return str(path)


def test_loads_config_from_explicit_file(config_file: str) -> None:
    ra = ResourceAllocation(config_file=config_file)
    assert ra._config == SAMPLE_CONFIG


def test_falls_back_silently_when_config_file_missing(tmp_path: Path) -> None:
    missing = str(tmp_path / "does_not_exist.yml")
    ra = ResourceAllocation(config_file=missing)
    assert ra._config == {}


def test_falls_back_silently_when_config_key_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ConfigInfo, "get", lambda self, keyWord, default=None: default)  # noqa: ARG005
    ra = ResourceAllocation(site_id="TEST")
    assert ra._config == {}


def test_resolves_config_path_via_config_info(monkeypatch: pytest.MonkeyPatch, config_file: str) -> None:
    def fake_get(self: Any, keyWord: Any, default: Any = None) -> Any:  # noqa: ARG001
        if keyWord == "RESOURCE_ALLOCATION_CONFIG_FILE":
            return config_file
        return default

    monkeypatch.setattr(ConfigInfo, "get", fake_get)
    ra = ResourceAllocation(site_id="TEST")
    assert ra._config == SAMPLE_CONFIG


def test_falls_back_silently_when_config_file_malformed(tmp_path: Path) -> None:
    path = tmp_path / "malformed.yml"
    path.write_text("key: [unclosed")
    ra = ResourceAllocation(config_file=str(path))
    assert ra._config == {}


def test_falls_back_silently_when_config_root_is_not_a_dict(tmp_path: Path) -> None:
    path = tmp_path / "not_a_dict.yml"
    path.write_text(yaml.safe_dump([1, 2, 3]))
    ra = ResourceAllocation(config_file=str(path))
    assert ra._config == {}


def test_get_cpus_from_job_override(config_file: str) -> None:
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("entity_transform_img_generator") == 4


def test_get_cpus_all_from_job_override(config_file: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(8)), raising=False)
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("cif_validator") == 8


def test_get_cpus_all_over_n_from_job_override(config_file: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(8)), raising=False)
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("map_calculation") == 2  # 8 // 4


def test_get_cpus_falls_back_to_defaults(config_file: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(8)), raising=False)
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("unlisted_job") == 4  # defaults.cpus = all/2, 8 // 2


def test_get_cpus_falls_back_to_system_when_config_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(6)), raising=False)
    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    assert ra.get_cpus("anything") == 6


def test_get_cpus_plain_number_string(tmp_path: Path) -> None:
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"jobs": {"job_a": {"cpus": "4"}}}))
    ra = ResourceAllocation(config_file=str(path))
    assert ra.get_cpus("job_a") == 4


def test_get_cpus_falls_back_to_cpu_count_off_linux(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(os, "sched_getaffinity", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 3)
    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    assert ra.get_cpus("anything") == 3


def test_get_memory_mb_from_job_override(config_file: str) -> None:
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_memory_mb("entity_transform_img_generator") == 16384


def test_get_memory_mb_falls_back_to_defaults(config_file: str) -> None:
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_memory_mb("unlisted_job") == 8192  # defaults.memory = 8G


def test_get_memory_mb_falls_back_to_defaults_for_job_without_override(config_file: str) -> None:
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_memory_mb("cif_validator") == 8192  # no job-level memory key, so defaults.memory = 8G applies


def test_get_memory_mb_all_is_unconstrained(tmp_path: Path) -> None:
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"defaults": {"memory": "all"}}))
    ra = ResourceAllocation(config_file=str(path))
    assert ra.get_memory_mb("anything") is None


def test_get_memory_mb_megabyte_suffix(tmp_path: Path) -> None:
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"jobs": {"job_a": {"memory": "8M"}}}))
    ra = ResourceAllocation(config_file=str(path))
    assert ra.get_memory_mb("job_a") == 8


def test_get_memory_mb_unconstrained_when_config_empty(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    assert ra.get_memory_mb("anything") is None


def test_get_memory_mb_plain_number_string(tmp_path: Path) -> None:
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"jobs": {"job_a": {"memory": "5"}}}))
    ra = ResourceAllocation(config_file=str(path))
    assert ra.get_memory_mb("job_a") == 5


def test_set_cpu_affinity_pins_subset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    available = {0, 1, 2, 3, 4, 5, 6, 7}
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: available, raising=False)
    calls = []
    monkeypatch.setattr(os, "sched_setaffinity", lambda pid, cpus: calls.append((pid, cpus)), raising=False)

    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    ra.set_cpu_affinity(3)

    assert len(calls) == 1
    pid, cpus = calls[0]
    assert pid == 0
    assert len(cpus) == 3
    assert cpus.issubset(available)


def test_set_cpu_affinity_randomizes_selection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    available = set(range(100))
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: available, raising=False)
    calls = []
    monkeypatch.setattr(os, "sched_setaffinity", lambda pid, cpus: calls.append(cpus), raising=False)

    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    ra.set_cpu_affinity(5)
    ra.set_cpu_affinity(5)

    assert calls[0] != calls[1]


def test_set_cpu_affinity_clamps_to_available_when_requested_exceeds_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    available = {0, 1, 2, 3}
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: available, raising=False)
    calls = []
    monkeypatch.setattr(os, "sched_setaffinity", lambda pid, cpus: calls.append(cpus), raising=False)

    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    ra.set_cpu_affinity(10)

    assert len(calls) == 1
    assert calls[0] == available


def test_set_cpu_affinity_noop_when_unsupported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(os, "sched_setaffinity", raising=False)
    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    ra.set_cpu_affinity(2)  # must not raise


def test_get_cpus_all_over_n_floors_to_one_when_division_hits_zero(config_file: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(2)), raising=False)
    ra = ResourceAllocation(config_file=config_file)
    assert ra._resolve_cpu_value("all/4") == 1  # 2 // 4 == 0, floored to 1


def test_set_cpu_affinity_does_not_call_sched_setaffinity_with_empty_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: {0, 1, 2, 3}, raising=False)
    calls = []
    monkeypatch.setattr(os, "sched_setaffinity", lambda pid, cpus: calls.append((pid, cpus)), raising=False)

    ra = ResourceAllocation(config_file=str(tmp_path / "missing.yml"))
    ra.set_cpu_affinity(0)  # must not raise OSError: [Errno 22] Invalid argument

    assert all(cpus != set() for _pid, cpus in calls)
    assert len(calls) == 0


def test_get_memory_mb_empty_string_is_ignored_with_warning(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump({"jobs": {"job_a": {"memory": ""}}}))
    ra = ResourceAllocation(config_file=str(path))
    with caplog.at_level(logging.WARNING):
        assert ra.get_memory_mb("job_a", default=2000) == 2000
    assert any("job_a" in r.getMessage() for r in caplog.records)


# ---------------------------------------------------------------------------
# Caller-supplied defaults (an omitted default keeps the original behaviour)
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, data: Any) -> str:
    path = tmp_path / "cfg.yml"
    path.write_text(yaml.safe_dump(data))
    return str(path)


def test_get_cpus_unconfigured_returns_explicit_default(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.get_cpus("job_a", default=7) == 7


def test_get_cpus_explicit_none_default_is_distinguishable_from_omitted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: {0, 1, 2}, raising=False)
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.get_cpus("job_a", default=None) is None
    assert ra.get_cpus("job_a") == 3


def test_get_cpus_configured_value_beats_default(config_file: str) -> None:
    ra = ResourceAllocation(config_file=config_file)
    assert ra.get_cpus("entity_transform_img_generator", default=1) == 4


def test_get_memory_mb_unconfigured_returns_explicit_default(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.get_memory_mb("job_a", default=2000) == 2000


def test_get_memory_mb_omitted_default_is_none_and_explicit_none_is_none(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.get_memory_mb("job_a") is None
    assert ra.get_memory_mb("job_a", default=None) is None


def test_get_memory_mb_explicit_all_is_none_even_with_default(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {"jobs": {"job_a": {"memory": "all"}}}))
    assert ra.get_memory_mb("job_a", default=2000) is None


def test_get_memory_mb_defaults_section_all_is_none_even_with_default(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {"defaults": {"memory": "all"}}))
    assert ra.get_memory_mb("job_a", default=2000) is None


def test_get_memory_mb_job_overrides_defaults_section(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {"defaults": {"memory": "8G"}, "jobs": {"job_a": {"memory": "4G"}}}))
    assert ra.get_memory_mb("job_a", default=2000) == 4096
    assert ra.get_memory_mb("job_b", default=2000) == 8192


# ---------------------------------------------------------------------------
# Invalid values: the job value counts as absent, then defaults, then the caller default
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [True, False, 0, -2, 1.5, "all/0", "abc", "", "0", "-3", "all/x"])
def test_invalid_cpu_value_falls_back_to_caller_default(tmp_path: Path, bad: Any, caplog: pytest.LogCaptureFixture) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {"jobs": {"job_a": {"cpus": bad}}}))
    with caplog.at_level(logging.WARNING):
        assert ra.get_cpus("job_a", default=5) == 5
    assert caplog.records


@pytest.mark.parametrize("bad", [True, False, 0, -2, 1.5, "1.5G", "2T", "abc", "", "0", "-3G", "G"])
def test_invalid_memory_value_falls_back_to_caller_default(tmp_path: Path, bad: Any, caplog: pytest.LogCaptureFixture) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {"jobs": {"job_a": {"memory": bad}}}))
    with caplog.at_level(logging.WARNING):
        assert ra.get_memory_mb("job_a", default=2000) == 2000
    assert caplog.records


def test_invalid_job_cpu_value_uses_valid_defaults_section(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {"defaults": {"cpus": 3}, "jobs": {"job_a": {"cpus": "bogus"}}}))
    assert ra.get_cpus("job_a", default=9) == 3


def test_invalid_job_memory_value_uses_valid_defaults_section(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {"defaults": {"memory": "8G"}, "jobs": {"job_a": {"memory": "bogus"}}}))
    assert ra.get_memory_mb("job_a", default=2000) == 8192


def test_job_and_defaults_both_invalid_use_caller_default(tmp_path: Path) -> None:
    cfg = {"defaults": {"cpus": "bogus", "memory": "bogus"}, "jobs": {"job_a": {"cpus": 0, "memory": 0}}}
    ra = ResourceAllocation(config_file=_write(tmp_path, cfg))
    assert ra.get_cpus("job_a", default=2) == 2
    assert ra.get_memory_mb("job_a", default=1500) == 1500


@pytest.mark.parametrize(
    "cfg",
    [
        {"jobs": ["a", "b"]},
        {"jobs": "text"},
        {"jobs": {"job_a": 5}},
        {"jobs": {"job_a": ["cpus"]}},
        {"defaults": 7},
        {"defaults": ["cpus"]},
        {"jobs": None, "defaults": None},
    ],
)
def test_wrongly_shaped_sections_are_ignored(tmp_path: Path, cfg: Dict[str, Any]) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, cfg))
    assert ra.get_cpus("job_a", default=2) == 2
    assert ra.get_memory_mb("job_a", default=1500) == 1500


# ---------------------------------------------------------------------------
# Where the configuration comes from
# ---------------------------------------------------------------------------


class _FakeConfigInfo:
    def __init__(self, value: Any) -> None:
        self._value = value

    def get(self, key: Any, default: Any = None) -> Any:
        return self._value if key == "RESOURCE_ALLOCATION_CONFIG_FILE" else default


class _BrokenConfigInfo:
    def get(self, key: Any, default: Any = None) -> Any:  # noqa: ARG002
        raise RuntimeError("site configuration unavailable")


def test_config_info_object_supplies_path(config_file: str) -> None:
    ra = ResourceAllocation(config_info=_FakeConfigInfo(config_file))
    assert ra.get_cpus("entity_transform_img_generator") == 4


def test_config_file_beats_config_info(tmp_path: Path, config_file: str) -> None:
    ra = ResourceAllocation(config_file=config_file, config_info=_FakeConfigInfo(str(tmp_path / "nope.yml")))
    assert ra.get_cpus("entity_transform_img_generator") == 4


def test_failing_config_info_lookup_does_not_raise(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        ra = ResourceAllocation(config_info=_BrokenConfigInfo())
    assert ra.get_cpus("job_a", default=3) == 3
    assert caplog.records


def test_unset_config_path_is_silent(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        ra = ResourceAllocation(config_info=_FakeConfigInfo(None))
    assert ra.get_cpus("job_a", default=3) == 3
    assert not caplog.records


def test_configured_but_missing_file_warns_once(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        ra = ResourceAllocation(config_file=str(tmp_path / "nope.yml"))
        ra.get_cpus("job_a")
        ra.get_memory_mb("job_a")
    assert len(caplog.records) == 1


def test_configured_but_malformed_file_warns(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    path = tmp_path / "bad.yml"
    path.write_text("key: [unclosed")
    with caplog.at_level(logging.WARNING):
        ResourceAllocation(config_file=str(path))
    assert caplog.records


# ---------------------------------------------------------------------------
# available_cpus()
# ---------------------------------------------------------------------------


def test_available_cpus_uses_affinity_mask(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: {4, 5}, raising=False)
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.available_cpus() == 2


def test_available_cpus_falls_back_when_affinity_raises_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_pid: Any) -> Any:
        raise OSError("not permitted")

    monkeypatch.setattr(os, "sched_getaffinity", boom, raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 6)
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.available_cpus() == 6


def test_available_cpus_falls_back_when_affinity_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(os, "sched_getaffinity", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 3)
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.available_cpus() == 3


def test_available_cpus_is_at_least_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(os, "sched_getaffinity", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: None)
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.available_cpus() == 1


# ---------------------------------------------------------------------------
# The shipped example
# ---------------------------------------------------------------------------

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "resource_allocation.yaml"


CALL_SITE_KEYS = [
    "validation.mogul",
    "validation.ed_pictures",
    "validation.diagram",
    "ccmodule.instance_reports",
    "ccmodule.assign_validation",
    "seqmodule.blast",
    "seqmodule.ref_alignments",
    "seqmodule.same_seq_annotation",
    "releasemodule.update",
]


def test_example_file_is_valid_and_resolves_validation_values() -> None:
    ra = ResourceAllocation(config_file=str(EXAMPLE))
    assert ra.get_memory_mb("annot-wwpdb-validate-all-v2") == 4096
    assert ra.get_cpus("annot-wwpdb-validate-all-v2") == 3
    assert ra.get_cpus("seqmodule.blast", default=None) == 4
    assert ra.get_memory_mb("seq-blastp", default=0) == 20480


@pytest.mark.parametrize("key", CALL_SITE_KEYS)
def test_example_file_documents_every_call_site_key(key: str) -> None:
    assert ResourceAllocation(config_file=str(EXAMPLE)).get_cpus(key, default=None) is not None


def test_example_file_does_not_change_unlisted_call_sites() -> None:
    """The example must not carry a ``defaults`` block that silently overrides every call site's own default."""
    ra = ResourceAllocation(config_file=str(EXAMPLE))
    assert ra.get_cpus("some.unlisted.call_site", default=None) is None
    assert ra.get_memory_mb("some-unlisted-operation", default=None) is None


# ---------------------------------------------------------------------------
# Code-owned CPU defaults: an integer or an expression such as "cpus / 2"
# ---------------------------------------------------------------------------


def _with_cpus(monkeypatch: pytest.MonkeyPatch, count: int) -> None:
    monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(count)), raising=False)


@pytest.mark.parametrize(("cpus", "expected"), [(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (64, 32)])
def test_expression_default_halves_and_floors_with_a_minimum_of_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cpus: int, expected: int) -> None:
    _with_cpus(monkeypatch, cpus)
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.get_cpus("job_a", default="cpus / 2") == expected


@pytest.mark.parametrize(("expression", "expected"), [("cpus", 6), ("cpus/2", 3), ("  cpus  /  3  ", 2), ("cpus / 4", 1), ("cpus / 100", 1)])
def test_expression_default_accepts_the_documented_forms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, expression: str, expected: int) -> None:
    _with_cpus(monkeypatch, 6)
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.get_cpus("job_a", default=expression) == expected


INVALID_EXPRESSIONS = ["", "cpu / 2", "cpus / 0", "cpus * 2", "cpus / 2.5", "cpus /", "/ 2", "cpus / -1", "cpus / 2 / 2", "2 + 2", "4", "all/2", "__import__('os')", "cpus / ٢"]


@pytest.mark.parametrize("expression", INVALID_EXPRESSIONS)
def test_invalid_expression_default_raises_value_error(tmp_path: Path, expression: str) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    with pytest.raises(ValueError, match="default"):
        ra.get_cpus("job_a", default=expression)


@pytest.mark.parametrize("bad", [True, False, 2.5, ["cpus"], {"cpus": 2}])
def test_default_of_the_wrong_type_raises_value_error(tmp_path: Path, bad: Any) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    with pytest.raises(ValueError, match="default"):
        ra.get_cpus("job_a", default=bad)


def test_invalid_expression_raises_even_when_the_file_has_a_valid_value(tmp_path: Path) -> None:
    ra = ResourceAllocation(config_file=_write(tmp_path, {"jobs": {"job_a": {"cpus": 3}}}))
    with pytest.raises(ValueError, match="default"):
        ra.get_cpus("job_a", default="cpus * 2")


def test_expression_default_is_never_evaluated_as_code(tmp_path: Path) -> None:
    marker = tmp_path / "evaluated"
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    with pytest.raises(ValueError, match="default"):
        ra.get_cpus("job_a", default=f"__import__('pathlib').Path({str(marker)!r}).touch()")
    assert not marker.exists()


def test_no_resource_file_gives_the_code_default(monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 8)
    monkeypatch.setattr(ConfigInfo, "get", lambda self, keyWord, default=None: default)  # noqa: ARG005
    ra = ResourceAllocation(site_id="TEST")
    assert ra.get_cpus("job_a", default="cpus / 2") == 4
    assert ra.get_cpus("job_a", default=7) == 7


@pytest.mark.parametrize("data", [{}, {"jobs": {}}, {"defaults": {}}, {"jobs": {"other": {"cpus": 5}}}, {"jobs": {"job_a": {"memory": "1G"}}}])
def test_missing_yaml_keys_give_the_code_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data: Dict[str, Any]) -> None:
    _with_cpus(monkeypatch, 8)
    ra = ResourceAllocation(config_file=_write(tmp_path, data))
    assert ra.get_cpus("job_a", default="cpus / 2") == 4


def test_malformed_yaml_warns_and_gives_the_code_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    _with_cpus(monkeypatch, 8)
    path = tmp_path / "bad.yml"
    path.write_text("jobs: [unclosed")
    with caplog.at_level(logging.WARNING):
        ra = ResourceAllocation(config_file=str(path))
    assert ra.get_cpus("job_a", default="cpus / 2") == 4
    assert caplog.records


def test_configured_value_overrides_the_code_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 8)
    ra = ResourceAllocation(config_file=_write(tmp_path, {"jobs": {"job_a": {"cpus": 3}}}))
    assert ra.get_cpus("job_a", default="cpus / 2") == 3
    assert ra.get_cpus("job_a", default=7) == 3


def test_omitted_default_still_returns_every_available_cpu(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 5)
    ra = ResourceAllocation(config_file=_write(tmp_path, {}))
    assert ra.get_cpus("job_a") == 5


# ---------------------------------------------------------------------------
# Worker-process counts for call sites inside a job
# ---------------------------------------------------------------------------


def _workers(tmp_path: Path, jobs: Any = None) -> ResourceAllocation:
    return ResourceAllocation(config_file=_write(tmp_path, {"jobs": jobs or {}}))


@pytest.mark.parametrize(("cpus", "expected"), [(16, 8), (3, 1), (2, 1), (1, 1)])
def test_worker_count_expression_default_is_half_the_cpus_and_at_least_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cpus: int, expected: int) -> None:
    _with_cpus(monkeypatch, cpus)
    assert _workers(tmp_path).get_worker_count("validation.mogul", "cpus / 2") == expected


def test_worker_count_integer_default_is_not_clamped_by_the_cpus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 2)
    assert _workers(tmp_path).get_worker_count("validation.mogul", 40) == 40


def test_worker_count_configured_value_beats_the_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 16)
    assert _workers(tmp_path, {"validation.mogul": {"cpus": 3}}).get_worker_count("validation.mogul", "cpus / 2") == 3


def test_worker_count_configured_above_available_is_clamped_with_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    _with_cpus(monkeypatch, 4)
    with caplog.at_level(logging.WARNING):
        assert _workers(tmp_path, {"validation.mogul": {"cpus": 20}}).get_worker_count("validation.mogul", "cpus / 2") == 4
    assert any("validation.mogul" in record.getMessage() for record in caplog.records)


def test_worker_count_cap_bounds_the_code_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 64)
    assert _workers(tmp_path).get_worker_count("validation.mogul", "cpus / 2", cap=10) == 10


def test_worker_count_cap_bounds_a_configured_value_with_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    _with_cpus(monkeypatch, 32)
    with caplog.at_level(logging.WARNING):
        assert _workers(tmp_path, {"validation.mogul": {"cpus": 20}}).get_worker_count("validation.mogul", "cpus / 2", cap=10) == 10
    assert any("validation.mogul" in record.getMessage() and "10" in record.getMessage() for record in caplog.records)


def test_worker_count_cap_below_a_configured_value_within_the_cpus_does_not_warn_when_not_reduced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    _with_cpus(monkeypatch, 32)
    with caplog.at_level(logging.WARNING):
        assert _workers(tmp_path, {"validation.mogul": {"cpus": 6}}).get_worker_count("validation.mogul", "cpus / 2", cap=10) == 6
    assert not caplog.records


def test_worker_count_without_a_cap_only_the_cpus_limit_a_configured_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 4)
    assert _workers(tmp_path, {"validation.mogul": {"cpus": 20}}).get_worker_count("validation.mogul", "cpus / 2") == 4


def test_worker_count_uses_the_defaults_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 16)
    ra = ResourceAllocation(config_file=_write(tmp_path, {"defaults": {"cpus": "all/4"}}))
    assert ra.get_worker_count("validation.mogul", "cpus / 2") == 4


def test_worker_count_invalid_configuration_falls_back_to_the_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 16)
    assert _workers(tmp_path, {"validation.mogul": {"cpus": "lots"}}).get_worker_count("validation.mogul", 5) == 5


def test_worker_count_is_never_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _with_cpus(monkeypatch, 1)
    assert _workers(tmp_path).get_worker_count("validation.mogul", 0) == 1


@pytest.mark.parametrize("expression", ["cpus * 2", "", "cpus / 0"])
def test_worker_count_invalid_default_raises_even_when_configured(tmp_path: Path, expression: str) -> None:
    with pytest.raises(ValueError, match="default"):
        _workers(tmp_path, {"validation.mogul": {"cpus": 3}}).get_worker_count("validation.mogul", expression)


def test_worker_count_none_default_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="default"):
        _workers(tmp_path).get_worker_count("validation.mogul", None)  # type: ignore[arg-type]


@pytest.mark.parametrize("cap", [0, -1, True, 2.5, "10"])
def test_worker_count_invalid_cap_raises(tmp_path: Path, cap: Any) -> None:
    with pytest.raises(ValueError, match="cap"):
        _workers(tmp_path).get_worker_count("validation.mogul", "cpus / 2", cap=cap)
