"""Entry point for the Adaptive Steganography Engine v2.0.0 GUI."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from .gui.main_window import MainWindow


def main() -> None:
    """Launch the PyQt6 GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Adaptive Steganography Engine v2.0.0")

    window = MainWindow()
    window.resize(1100, 720)
    window.show()

    if getattr(sys, "frozen", False):  # pragma: no cover - defensive guard
        # When bundled, ensure working directory is project root for IO dialogs.
        os.chdir(Path(sys.executable).resolve().parent)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
