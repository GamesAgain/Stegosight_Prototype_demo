"""Resource helpers for loading icons and QSS themes."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6 import QtGui


PACKAGE_ROOT = Path(__file__).resolve().parent
RESOURCE_DIR = PACKAGE_ROOT / "assets"


def resource_path(name: str) -> Path:
    path = RESOURCE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Resource {name} not found in {RESOURCE_DIR}")
    return path


def load_icon(name: str) -> QtGui.QIcon:
    try:
        return QtGui.QIcon(str(resource_path(name)))
    except FileNotFoundError:
        return QtGui.QIcon()


def load_stylesheet(name: str) -> Optional[str]:
    try:
        with resource_path(name).open("r", encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        return None
