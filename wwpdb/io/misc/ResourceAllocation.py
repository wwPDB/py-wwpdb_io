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
