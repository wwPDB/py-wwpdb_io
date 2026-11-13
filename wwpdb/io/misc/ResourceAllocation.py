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
  inside whatever it was given.  Code that starts worker processes asks for it with :meth:`get_worker_count`,
  passing the count it used before as the code-owned default (for example ``"cpus / 2"``), so a site without a
  resource file behaves as it did.

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

A CPU ``default`` supplied by the calling code is an integer or an expression, ``cpus`` or ``cpus / N`` (``cpus`` is the
number of CPUs available to the process; division rounds down; never less than 1).  It is parsed, never evaluated.  An
invalid expression is a programming error and raises :class:`ValueError`, in contrast to a mistake in the file.

CPUs are counted from the process affinity mask where the platform provides one, so the number reflects what this
process may use rather than what the machine has.  Whether that equals a batch scheduler's per-job allocation depends
on how the scheduler is configured.
"""

from __future__ import annotations

import logging
import os
import random
import re
from typing import Any, Dict, Optional

import yaml
from wwpdb.utils.config.ConfigInfo import ConfigInfo

logger = logging.getLogger(__name__)

CONFIG_KEY = "RESOURCE_ALLOCATION_CONFIG_FILE"

_UNSET: Any = object()  # distinguishes "no default given" from an explicit ``default=None``
_INVALID: Any = object()  # internal marker for a value that could not be interpreted
_UNLIMITED: Any = object()  # internal marker for ``memory: all``

# A code-owned CPU default: ``cpus`` or ``cpus / N`` (N a positive whole number).  ASCII digits only.
_CPU_EXPRESSION = re.compile(r"\s*cpus\s*(?:/\s*([0-9]+)\s*)?", re.ASCII)


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

        ``default`` is the value the calling code wants when nothing valid is configured.  It is an integer, ``None``
        (meaning "no value"), or an expression: ``"cpus"`` or ``"cpus / N"`` where ``cpus`` is :meth:`available_cpus`
        and N is a positive whole number.  Division rounds down and the result is at least 1, so ``"cpus / 2"`` is the
        usual "half of what this process may use".  When ``default`` is omitted, every available CPU is returned.

        A ``default`` that is not one of these raises :class:`ValueError` whether or not a value is configured: it is a
        mistake in the calling code, unlike a mistake in the configuration file, which only logs a warning.
        """
        fallback = self._code_default(default)
        value = self._lookup(job_name, "cpus", self._resolve_cpu_value)
        return fallback if value is _INVALID else value

    def _code_default(self, default: Any) -> Any:
        """Validate a caller's CPU default and return its value (``None`` stays ``None``)."""
        if default is _UNSET:
            return self.available_cpus()
        if default is None:
            return None
        if isinstance(default, bool):
            raise ValueError(f"Invalid default {default!r}: expected an integer, None, 'cpus' or 'cpus / N'")  # noqa: TRY004
        if isinstance(default, int):
            return default
        if isinstance(default, str):
            match = _CPU_EXPRESSION.fullmatch(default)
            if match is not None:
                if match.group(1) is None:
                    return self.available_cpus()
                divisor = int(match.group(1))
                if divisor > 0:
                    return max(1, self.available_cpus() // divisor)
        raise ValueError(f"Invalid default {default!r}: expected an integer, None, 'cpus' or 'cpus / N' with N greater than zero")

    def get_worker_count(self, call_site: str, default: Any, cap: Optional[int] = None) -> int:
        """Return how many worker processes the code at ``call_site`` should start.

        ``default`` is what the calling code used before this class existed, as an integer or an expression (see
        :meth:`get_cpus`); ``cap`` is an upper limit the calling code already had.  The rules are:

        * The default is validated first, so a wrong default raises :class:`ValueError` even when the file has a value.
        * When a value is configured for ``call_site`` it is used, reduced to :meth:`available_cpus` if larger.
        * Otherwise the default is used as given, so an integer such as the number of items is never reduced.
        * ``cap`` then limits the result, whether it came from the file or from the default.
        * Every reduction of a configured value is reported with a warning.  The result is at least 1, because
          ``MultiProcUtil`` treats fewer than one worker as "automatic" and starts twice the node's CPUs.
        """
        if default is None:
            raise ValueError("Invalid default None for a worker count: expected an integer, 'cpus' or 'cpus / N'")
        if cap is not None and (isinstance(cap, bool) or not isinstance(cap, int) or cap < 1):
            raise ValueError(f"Invalid cap {cap!r}: expected a positive integer")

        resolved_default = self._code_default(default)
        configured = self.get_cpus(call_site, default=None)
        if configured is None:
            workers = resolved_default
        else:
            workers = configured
            available = self.available_cpus()
            if workers > available:
                logger.warning("Resource allocation: %s is configured for %d workers but only %d CPUs are available; using %d", call_site, workers, available, available)
                workers = available
        if cap is not None and workers > cap:
            if configured is not None:
                logger.warning("Resource allocation: %s is configured for %d workers but at most %d are allowed; using %d", call_site, workers, cap, cap)
            workers = cap
        return max(1, int(workers))

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
