"""Extraction tab for adaptive steganography GUI."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..extractor import extract_controller
from ..util import image_io


class ExtractTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.stego_image: Optional[np.ndarray] = None
        self.stego_path: Optional[Path] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        file_layout = QHBoxLayout()
        self.stego_label = QLabel("No stego image selected")
        self.btn_select_stego = QPushButton("Select Stego PNG")
        self.btn_select_stego.clicked.connect(self._select_stego)
        file_layout.addWidget(self.stego_label)
        file_layout.addWidget(self.btn_select_stego)
        layout.addLayout(file_layout)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(320, 320)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_label)

        form_layout = QGridLayout()
        form_layout.addWidget(QLabel("Seed / Password"), 0, 0)
        self.seed_input = QLineEdit()
        form_layout.addWidget(self.seed_input, 0, 1)

        self.chk_encrypted = QCheckBox("Payload is encrypted")
        form_layout.addWidget(self.chk_encrypted, 1, 0, 1, 2)
        layout.addLayout(form_layout)

        self.btn_extract = QPushButton("Extract Payload")
        self.btn_extract.clicked.connect(self._run_extraction)
        layout.addWidget(self.btn_extract)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.btn_save = QPushButton("Save Payload .txt")
        self.btn_save.clicked.connect(self._save_payload)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)

    def _select_stego(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Stego Image", "", "PNG Images (*.png)")
        if not path:
            return
        try:
            self.stego_image = image_io.load_png(path)
        except Exception as exc:
            QMessageBox.critical(self, "Invalid Image", str(exc))
            return
        self.stego_path = Path(path)
        self.stego_label.setText(self.stego_path.name)
        self._update_preview(self.stego_image)

    def _update_preview(self, image: Optional[np.ndarray]) -> None:
        if image is None:
            self.preview_label.clear()
            return
        h, w, _ = image.shape
        qimage = QImage(image.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage).scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(pixmap)

    def _run_extraction(self) -> None:
        if self.stego_image is None:
            QMessageBox.warning(self, "Missing Image", "Select a stego PNG first.")
            return
        seed = self.seed_input.text().strip() or "default-seed"
        password = None
        if self.chk_encrypted.isChecked():
            password = self.seed_input.text()
            if not password:
                QMessageBox.warning(self, "Missing Password", "Provide the password used during embedding.")
                return
        try:
            result = extract_controller.extract(self.stego_image, seed=seed, password=password)
        except extract_controller.HeaderValidationError as exc:
            QMessageBox.critical(self, "Header Error", str(exc))
            return
        except extract_controller.ExtractionError as exc:
            QMessageBox.critical(self, "Extraction Error", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Unexpected Error", str(exc))
            return

        try:
            text = result.payload.decode("utf-8")
        except UnicodeDecodeError:
            text = result.payload.hex()
        self.output_text.setPlainText(text)
        self.btn_save.setEnabled(True)

    def _save_payload(self) -> None:
        text = self.output_text.toPlainText()
        if not text:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Payload Text", "payload.txt", "Text Files (*.txt)")
        if not path:
            return
        try:
            Path(path).write_text(text, encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            return
        QMessageBox.information(self, "Payload Saved", f"Saved to {path}")
