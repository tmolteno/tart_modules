"""Make the tart_tools tests runnable from a plain source checkout.

The tests import both ``tart_tools`` and ``tart``. ``tart`` is a sibling
package in this repository and may not be installed (e.g. a fresh clone, or
an offline machine), so fall back to the in-repo sources. Running pytest
from the repository root can otherwise pick up the *project* directory
``<repo>/tart`` as an empty namespace package, which hides the real one.
"""
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from tart.operation import settings  # noqa: F401  (what api_handler needs)
except ImportError:
    # Drop any half-imported placeholder before re-pointing at the sources.
    for _name in list(sys.modules):
        if _name == "tart" or _name.startswith("tart."):
            del sys.modules[_name]
    _tart_src = os.path.join(_REPO_ROOT, "tart")
    if os.path.isdir(_tart_src) and _tart_src not in sys.path:
        sys.path.insert(0, _tart_src)
