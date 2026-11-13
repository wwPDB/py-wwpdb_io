"""Per-job CPU and memory allocation read from a YAML file.

The location of the YAML file is the site-configuration key ``RESOURCE_ALLOCATION_CONFIG_FILE``.  When that key is
unset the class behaves as if the file were empty.  A configured file that is missing, unreadable or malformed is
reported with a warning and treated as empty.  A mistake in the file never raises an exception.

File layout::

    defaults:            # optional, used for any job that does not set the key itself
      cpus: all/2
      memory: 8G
    jobs:
      <job name>:        # an operation name (what the batch job requests) or a call-site name (worker processes)
        cpus: 4
        memory: 16G

Two kinds of job name are used and they are independent controls:

* an *operation* name such as ``annot-wwpdb-validate-all-v2`` is what a cluster job requests for itself;
* a *call-site* name such as ``validation.mogul`` is how many worker processes that piece of code starts
  inside whatever it was given.

Values:

``cpus``
    A positive integer (``4`` or ``"4"``), ``all`` (every CPU available to this process), or ``all/N`` (that number
    divided by N, never less than 1).

``memory``
    A positive integer number of megabytes (``2048``), or an integer followed by ``M`` or ``G`` (``512M``, ``16G``).
    ``all`` means unconstrained: :meth:`ResourceAllocation.get_memory_mb` returns ``None``.

Resolution order for a key: ``jobs.<job name>.<key>``, then ``defaults.<key>``, then the ``default`` argument of the
getter.  A value that is not valid is reported with a warning and counts as absent, so an invalid job value falls
through to ``defaults`` and an invalid ``defaults`` value falls through to the caller's default.  When the getter is
called without a ``default``, :meth:`~ResourceAllocation.get_cpus` returns every available CPU and
:meth:`~ResourceAllocation.get_memory_mb` returns ``None``.

CPUs are counted from the process affinity mask where the platform provides one, so the number reflects what this
process may use rather than what the machine has.  Whether that equals a batch scheduler's per-job allocation depends
on how the scheduler is configured.
"""

from __future__ import annotations

import logging
import os
import random
from typing import Any, Dict, Optional

import yaml
from wwpdb.utils.config.ConfigInfo import ConfigInfo

logger = logging.getLogger(__name__)

CONFIG_KEY = "RESOURCE_ALLOCATION_CONFIG_FILE"

_UNSET: Any = object()  # distinguishes "no default given" from an explicit ``default=None``
_INVALID: Any = object()  # internal marker for a value that could not be interpreted
_UNLIMITED: Any = object()  # internal marker for ``memory: all``


class ResourceAllocation:
    """Look up CPU and memory allocations for named jobs.

    :param site_id: site identifier used to read ``RESOURCE_ALLOCATION_CONFIG_FILE`` through ``ConfigInfo``.
    :param config_file: path of the YAML file; takes precedence over ``config_info`` and ``site_id``.
    :param config_info: an existing ``ConfigInfo``-like object (anything with ``get(key)``); takes precedence over ``site_id``.
    """

    def __init__(self, site_id: Optional[str] = None, config_file: Optional[str] = None, config_info: Any = None) -> None:
        self._config: Dict[str, Any] = self._load_config(site_id, config_file, config_info)

    @staticmethod
    def _load_config(site_id: Optional[str], config_file: Optional[str], config_info: Any) -> Dict[str, Any]:
        path = config_file
        if path is None:
            try:
                info = config_info if config_info is not None else ConfigInfo(siteId=site_id)
                path = info.get(CONFIG_KEY)
            except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                logger.warning("Resource allocation: could not read %s from the site configuration: %s", CONFIG_KEY, exc)
                return {}

        if not path:
            return {}

        if not os.path.exists(path):
            logger.warning("Resource allocation: configuration file %s does not exist; using defaults", path)
            return {}

        try:
            with open(path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except (OSError, yaml.YAMLError) as exc:
            logger.warning("Resource allocation: cannot read configuration file %s: %s", path, exc)
            return {}

        if data is None:
            return {}
        if not isinstance(data, dict):
            logger.warning("Resource allocation: configuration file %s does not contain a mapping; ignoring it", path)
            return {}
        return data

    # -- lookup -----------------------------------------------------------------------------------------------

    def _section(self, name: str) -> Dict[str, Any]:
        section = self._config.get(name)
        return section if isinstance(section, dict) else {}

    def _lookup(self, job_name: str, key: str, resolver: Any) -> Any:
        """Return the first valid value for ``key``: the job's own, then ``defaults``; ``_INVALID`` if none."""
        job_cfg = self._section("jobs").get(job_name)
        if isinstance(job_cfg, dict) and key in job_cfg:
            value = resolver(job_cfg[key])
            if value is not _INVALID:
                return value
            logger.warning("Resource allocation: ignoring invalid %s %r for job %s", key, job_cfg[key], job_name)

        defaults_cfg = self._section("defaults")
        if key in defaults_cfg:
            value = resolver(defaults_cfg[key])
            if value is not _INVALID:
                return value
            logger.warning("Resource allocation: ignoring invalid default %s %r", key, defaults_cfg[key])

        return _INVALID

    # -- CPUs -------------------------------------------------------------------------------------------------

    @staticmethod
    def available_cpus() -> int:
        """Return the number of CPUs this process may use (at least 1)."""
        try:
            return max(1, len(os.sched_getaffinity(0)))
        except (AttributeError, OSError):
            return os.cpu_count() or 1

    def get_cpus(self, job_name: str, default: Any = _UNSET) -> Any:
        """Return the CPU count configured for ``job_name``.

        When nothing valid is configured, return ``default`` if one was given, otherwise :meth:`available_cpus`.
        """
        value = self._lookup(job_name, "cpus", self._resolve_cpu_value)
        if value is _INVALID:
            return self.available_cpus() if default is _UNSET else default
        return value

    def _resolve_cpu_value(self, value: Any) -> Any:
        if isinstance(value, bool):
            return _INVALID
        if isinstance(value, int):
            return value if value > 0 else _INVALID
        if not isinstance(value, str):
            return _INVALID

        text = value.strip()
        if text == "all":
            return self.available_cpus()
        if text.startswith("all/"):
            divisor = _positive_int(text.split("/", 1)[1])
            if divisor is None:
                return _INVALID
            return max(1, self.available_cpus() // divisor)

        count = _positive_int(text)
        return _INVALID if count is None else count

    # -- memory -----------------------------------------------------------------------------------------------

    def get_memory_mb(self, job_name: str, default: Any = _UNSET) -> Optional[int]:
        """Return the memory in megabytes configured for ``job_name``.

        ``None`` means unconstrained, which is what ``memory: all`` gives.  When nothing valid is configured, return
        ``default`` if one was given, otherwise ``None``.
        """
        value = self._lookup(job_name, "memory", self._resolve_memory_value)
        if value is _INVALID:
            return None if default is _UNSET else default
        if value is _UNLIMITED:
            return None
        return value  # type: ignore[no-any-return]

    @staticmethod
    def _resolve_memory_value(value: Any) -> Any:
        if isinstance(value, bool):
            return _INVALID
        if isinstance(value, int):
            return value if value > 0 else _INVALID
        if not isinstance(value, str):
            return _INVALID

        text = value.strip()
        if text == "all":
            return _UNLIMITED

        unit = text[-1:].upper()
        if unit == "G":
            amount = _positive_int(text[:-1])
            return _INVALID if amount is None else amount * 1024
        if unit == "M":
            amount = _positive_int(text[:-1])
            return _INVALID if amount is None else amount

        amount = _positive_int(text)
        return _INVALID if amount is None else amount

    # -- affinity ---------------------------------------------------------------------------------------------

    def set_cpu_affinity(self, num_cpus: int) -> None:
        """Pin the calling process to ``num_cpus`` randomly chosen CPUs from those it may already use.

        Intended for a subprocess ``preexec_fn``.  Does nothing where the platform has no affinity support.
        """
        if not hasattr(os, "sched_setaffinity"):
            return

        available = list(os.sched_getaffinity(0))
        k = min(num_cpus, len(available))
        pinned = set(random.sample(available, k)) if k > 0 else set()  # noqa: S311
        if not pinned:
            # Pinning to zero CPUs is meaningless and os.sched_setaffinity raises OSError (EINVAL) on an empty set,
            # so treat it as a no-op instead of crashing the caller's subprocess spawn.
            return
        os.sched_setaffinity(0, pinned)


def _positive_int(text: str) -> Optional[int]:
    """Parse ``text`` as a whole number greater than zero; return ``None`` if it is anything else."""
    text = text.strip()
    if not text.isdigit():
        return None
    number = int(text)
    return number if number > 0 else None
