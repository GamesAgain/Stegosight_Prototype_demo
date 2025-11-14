"""Entry point launching the PyQt6 GUI."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6 import QtWidgets

if __package__ in (None, ""):
    # When executed as a top-level script (``python adaptive_stego_engine/main.py``)
    # the relative imports fail. Ensure the project root is available on ``sys.path``
    # so that absolute imports resolve correctly.
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from adaptive_stego_engine.gui.main_window import MainWindow
else:
    from .gui.main_window import MainWindow


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
