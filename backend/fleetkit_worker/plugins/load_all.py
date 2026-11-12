"""Import all unique plugins so @job handlers register."""

from __future__ import annotations

import importlib
import pkgutil

from fleetkit_worker import plugins


def load_plugins() -> int:
    loaded = 0
    for mod in pkgutil.iter_modules(plugins.__path__, plugins.__name__ + "."):
        if mod.name.endswith(".load_all"):
            continue
        importlib.import_module(mod.name)
        loaded += 1
    return loaded
