"""Main application window containing embed and extract tabs."""
from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from .embed_tab import EmbedTab
from .extract_tab import ExtractTab


class MainWindow(QMainWindow):
    """Main window hosting the embed and extract tabs."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Adaptive Steganography Engine v2.0.0")

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.embed_tab = EmbedTab(self)
        self.extract_tab = ExtractTab(self)

        self.tabs.addTab(self.embed_tab, "Embed")
        self.tabs.addTab(self.extract_tab, "Extract")
