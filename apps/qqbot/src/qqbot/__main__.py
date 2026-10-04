"""``python -m qqbot`` -- show the configuration this process would use.

``python -m qqbot start`` instead syncs NapCat and starts everything; see
:mod:`qqbot.start`.

A ``__main__`` module rather than ``python -m qqbot.settings`` on purpose: the
package imports ``.settings`` to load ``.env`` early, so running that submodule
by dotted path re-executes it and raises a runpy warning.  This entry point is
not already in ``sys.modules``, so there is nothing to warn about.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    if sys.argv[1:2] == ["start"]:
        from .start import main as start_main

        raise SystemExit(start_main(sys.argv[2:]))
    from .settings import main

    raise SystemExit(main())
