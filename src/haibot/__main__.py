# -*- coding: utf-8 -*-
"""Allow running HaiBot via ``python -m haibot``."""
from .cli.main import cli

if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
