"""Resource helpers for the PyQt6 GUI."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QIcon

PACKAGE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PACKAGE_DIR / "assets"
DEFAULT_THEME = (
    "QWidget { background-color: #10141c; color: #f0f3ff; }\n"
    "QLineEdit, QTextEdit { background-color: #182030; border: 1px solid #2c3648; }\n"
    "QPushButton { background-color: #2d89ef; border: none; padding: 6px; color: white; }\n"
    "QPushButton:disabled { background-color: #3a3f4b; color: #8892b0; }\n"
)


def resource_path(name: str) -> Path:
    path = ASSETS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Resource {name!r} not found in {ASSETS_DIR}")
    return path


def load_icon(name: str) -> Optional[QIcon]:
    try:
        path = resource_path(name)
    except FileNotFoundError:
        return None
    return QIcon(str(path))


def load_stylesheet(name: str = "theme.qss") -> str:
    try:
        return resource_path(name).read_text(encoding="utf-8")
    except FileNotFoundError:
        return DEFAULT_THEME
