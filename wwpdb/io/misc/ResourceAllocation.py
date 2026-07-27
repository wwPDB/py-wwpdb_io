from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml
from wwpdb.utils.config.ConfigInfo import ConfigInfo


class ResourceAllocation:
    def __init__(self, site_id: Optional[str] = None, config_file: Optional[str] = None) -> None:
        self._config: Dict[str, Any] = self._load_config(site_id, config_file)

    @staticmethod
    def _load_config(site_id: Optional[str], config_file: Optional[str]) -> Dict[str, Any]:
        path = config_file
        if path is None:
            path = ConfigInfo(siteId=site_id).get("RESOURCE_ALLOCATION_CONFIG_FILE")

        if not path or not os.path.exists(path):
            return {}

        try:
            with open(path) as fh:
                data = yaml.safe_load(fh)
        except (OSError, yaml.YAMLError):
            return {}

        return data if isinstance(data, dict) else {}

    def get_cpus(self, job_name: str) -> int:
        value = self._lookup(job_name, "cpus")
        if value is None:
            return self._available_cpu_count()
        return self._resolve_cpu_value(value)

    def _lookup(self, job_name: str, key: str) -> Optional[Any]:
        job_cfg = (self._config.get("jobs") or {}).get(job_name) or {}
        if key in job_cfg:
            return job_cfg[key]

        defaults_cfg = self._config.get("defaults") or {}
        if key in defaults_cfg:
            return defaults_cfg[key]

        return None

    @staticmethod
    def _available_cpu_count() -> int:
        if hasattr(os, "sched_getaffinity"):
            return len(os.sched_getaffinity(0))
        return os.cpu_count() or 1

    def _resolve_cpu_value(self, value: Any) -> int:
        if isinstance(value, int):
            return value

        text = str(value).strip()
        if text == "all":
            return self._available_cpu_count()

        if text.startswith("all/"):
            divisor = int(text.split("/", 1)[1])
            return self._available_cpu_count() // divisor

        return int(text)

    def get_memory_mb(self, job_name: str) -> Optional[int]:
        value = self._lookup(job_name, "memory")
        if value is None:
            return None
        return self._resolve_memory_value(value)

    @staticmethod
    def _resolve_memory_value(value: Any) -> Optional[int]:
        if isinstance(value, int):
            return value

        text = str(value).strip()
        if text == "all":
            return None

        unit = text[-1].upper()
        if unit == "G":
            return int(text[:-1]) * 1024
        if unit == "M":
            return int(text[:-1])

        return int(text)

    def set_cpu_affinity(self, num_cpus: int) -> None:
        if not hasattr(os, "sched_setaffinity"):
            return

        available = sorted(os.sched_getaffinity(0))
        pinned = set(available[:num_cpus])
        os.sched_setaffinity(0, pinned)
