"""Main window containing embed and extract tabs."""
from __future__ import annotations

from PyQt6 import QtWidgets

from .embed_tab import EmbedTab
from .extract_tab import ExtractTab
from . import resources


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Adaptive Steganography Engine v2.0.0")
        self.resize(900, 700)
        self._tab_widget = QtWidgets.QTabWidget()
        self._tab_widget.addTab(EmbedTab(self), "Embed")
        self._tab_widget.addTab(ExtractTab(self), "Extract")
        self.setCentralWidget(self._tab_widget)
        self._load_theme()

    def _load_theme(self) -> None:
        stylesheet = resources.load_stylesheet("theme.qss")
        if stylesheet:
            self.setStyleSheet(stylesheet)
