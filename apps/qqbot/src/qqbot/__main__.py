"""``python -m qqbot`` -- show the configuration this process would use.

A ``__main__`` module rather than ``python -m qqbot.settings`` on purpose: the
package imports ``.settings`` to load ``.env`` early, so running that submodule
by dotted path re-executes it and raises a runpy warning.  This entry point is
not already in ``sys.modules``, so there is nothing to warn about.
"""
from __future__ import annotations

from .settings import main

if __name__ == "__main__":
    raise SystemExit(main())
