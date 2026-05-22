"""GovRadar - 한국 정부지원 정책/보조금 수집 레이더."""

import sys
from importlib import import_module

__version__ = "0.2.0"

from govradar.storage import RadarStorage

_MODULE_ALIASES = {
    "collector": "radar_core.collector",
    "exceptions": "radar_core.exceptions",
    "nl_query": "radar_core.nl_query",
    "raw_logger": "radar_core.raw_logger",
    "search_index": "radar_core.search_index",
}

for _module_name, _target in _MODULE_ALIASES.items():
    sys.modules[f"{__name__}.{_module_name}"] = import_module(_target)


__all__ = ["RadarStorage", "__version__"]
