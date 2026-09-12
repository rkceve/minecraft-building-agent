"""Astra edits this file. Keep `def build() -> Build` as the entry point."""
from __future__ import annotations

from mcbuild.dsl import Build
from mcbuild.palette import Palette


def build() -> Build:
    # Astra edits this file.
    return Build(origin=(0, 0, 0), palette=Palette())
