"""QQ bot integrations for the Minecraft knowledge project."""
from __future__ import annotations

from .settings import load_settings

# Runs before any submodule is imported, which is what makes ``.env`` cover the
# four variables ``web.py`` reads at import time.  Nothing here opens a socket
# or touches a model; it reads a config file and fills ``os.environ``.
load_settings()
