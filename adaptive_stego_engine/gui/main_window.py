"""Main window with embed and extract tabs."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from . import resources
from .embed_tab import EmbedTab
from .extract_tab import ExtractTab


class MainWindow(QMainWindow):
    def __init__(self, app: Optional[QApplication] = None) -> None:
        super().__init__()
        self.setWindowTitle("Adaptive Steganography Engine v2.0.0")
        self.resize(960, 720)

        if app is not None:
            stylesheet = resources.load_stylesheet()
            app.setStyleSheet(stylesheet)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(EmbedTab(self), "Embed")
        self.tabs.addTab(ExtractTab(self), "Extract")
        self.setCentralWidget(self.tabs)
