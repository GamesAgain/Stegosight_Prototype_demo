"""Extraction tab implementation."""
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
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..extractor.extract_controller import extract_payload
from ..util import image_io


class ExtractTab(QWidget):
    """Tab widget that performs the reverse pipeline to recover payloads."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.stego_path: Optional[Path] = None
        self.stego_image: Optional[np.ndarray] = None
        self.extracted_text: Optional[str] = None

        self._build_ui()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        stego_group = QGroupBox("Stego Image")
        stego_layout = QGridLayout(stego_group)

        self.stego_label = QLabel("No stego image selected")
        self.stego_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stego_label.setMinimumHeight(220)
        self.stego_label.setStyleSheet("border: 1px solid #444; background: #111;")

        select_stego_btn = QPushButton("Select Stego PNG")
        select_stego_btn.clicked.connect(self._on_select_stego)

        stego_layout.addWidget(self.stego_label, 0, 0, 1, 2)
        stego_layout.addWidget(select_stego_btn, 1, 0, 1, 2)

        controls_group = QGroupBox("Extraction Settings")
        controls_layout = QGridLayout(controls_group)

        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("Seed / Password")
        self.seed_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.encrypted_checkbox = QCheckBox("Payload is encrypted")
        self.encrypted_checkbox.setChecked(True)

        self.extract_button = QPushButton("Extract Payload")
        self.extract_button.clicked.connect(self._on_extract)

        self.status_label = QLabel("Idle")
        self.status_label.setWordWrap(True)

        controls_layout.addWidget(QLabel("Seed / Password:"), 0, 0)
        controls_layout.addWidget(self.seed_input, 0, 1)
        controls_layout.addWidget(self.encrypted_checkbox, 1, 0, 1, 2)
        controls_layout.addWidget(self.extract_button, 2, 0, 1, 2)
        controls_layout.addWidget(self.status_label, 3, 0, 1, 2)

        payload_group = QGroupBox("Recovered Payload")
        payload_layout = QVBoxLayout(payload_group)

        self.payload_view = QPlainTextEdit()
        self.payload_view.setReadOnly(True)
        payload_layout.addWidget(self.payload_view)

        save_btn = QPushButton("Save Payload as .txt")
        save_btn.clicked.connect(self._on_save_text)
        payload_layout.addWidget(save_btn)

        layout.addWidget(stego_group)
        layout.addWidget(controls_group)
        layout.addWidget(payload_group)
        layout.addStretch(1)

    # -------------------------------------------------------------- Handlers --
    def _on_select_stego(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Stego PNG",
            "",
            "PNG Images (*.png)",
        )
        if not file_path:
            return

        try:
            image = image_io.load_png(Path(file_path))
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Stego", str(exc))
            return

        self.stego_path = Path(file_path)
        self.stego_image = image
        self.extracted_text = None
        self.payload_view.clear()
        self._update_preview(image)
        self.status_label.setText(
            f"Loaded stego: {self.stego_path.name} ({image.shape[1]}x{image.shape[0]})"
        )

    def _on_extract(self) -> None:
        if self.stego_image is None:
            QMessageBox.warning(self, "Missing Stego", "Please select a PNG stego image first.")
            return

        seed = self.seed_input.text().strip()
        if not seed:
            QMessageBox.warning(self, "Missing Seed", "Provide the seed/password used during embedding.")
            return

        self.status_label.setText("Running extraction…")
        self.extract_button.setEnabled(False)

        try:
            result = extract_payload(
                stego_image=self.stego_image,
                seed=seed,
                encrypted=self.encrypted_checkbox.isChecked(),
            )
        except Exception as exc:  # pragma: no cover - UI feedback path
            self.extract_button.setEnabled(True)
            self.status_label.setText("Extraction failed")
            QMessageBox.critical(self, "Extraction Error", str(exc))
            return

        self.extract_button.setEnabled(True)
        self.extracted_text = result.payload
        self.payload_view.setPlainText(result.payload)
        self.status_label.setText(
            f"Recovered payload with {result.bits_read} bits read in total."
        )

    def _on_save_text(self) -> None:
        if not self.extracted_text:
            QMessageBox.information(self, "Nothing to Save", "Run extraction to obtain payload text first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Payload Text",
            "payload.txt",
            "Text Files (*.txt)",
        )
        if not file_path:
            return

        try:
            Path(file_path).write_text(self.extracted_text, encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Save Error", f"Failed to write file: {exc}")
            return

        QMessageBox.information(self, "Payload Saved", f"Payload saved to {file_path}")

    # ------------------------------------------------------------- Utilities --
    def _update_preview(self, image: np.ndarray) -> None:
        h, w, _ = image.shape
        buffer = np.ascontiguousarray(image)
        qimage = QImage(buffer.data, w, h, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage.copy()).scaled(
            400,
            400,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.stego_label.setPixmap(pixmap)
