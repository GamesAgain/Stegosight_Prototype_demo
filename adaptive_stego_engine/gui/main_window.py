"""Main window hosting tabs."""
from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from .embed_tab import EmbedTab
from .extract_tab import ExtractTab
from .key_tab import KeyTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Adaptive Steganography Engine v3.0.0")
        tabs = QTabWidget()
        self.embed_tab = EmbedTab()
        self.extract_tab = ExtractTab()
        self.key_tab = KeyTab(self.embed_tab, self.extract_tab)
        tabs.addTab(self.embed_tab, "Embed")
        tabs.addTab(self.extract_tab, "Extract")
        tabs.addTab(self.key_tab, "Keys")
        self.setCentralWidget(tabs)
