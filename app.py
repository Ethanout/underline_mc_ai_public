"""Compatibility launcher for the retained QQ bot web service."""
from workspace_bootstrap import add_workspace_packages

add_workspace_packages()

from qqbot.web import app, main  # noqa: E402,F401


if __name__ == "__main__":
    main()
