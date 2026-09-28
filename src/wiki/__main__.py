"""Allows `python -m wiki ...` as well as the installed `wiki` command."""

import sys

from .cli import main

sys.exit(main())
