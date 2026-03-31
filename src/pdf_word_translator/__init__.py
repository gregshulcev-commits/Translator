"""Offline PDF word translator MVP package.

The package is intentionally split into small modules so that future work can
replace the UI toolkit, document provider, or dictionary provider without
rewriting the whole application.
"""

__all__ = [
    "config",
    "models",
    "plugin_api",
    "plugin_loader",
]
