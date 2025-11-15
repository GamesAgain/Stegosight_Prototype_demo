"""Embedding tab implementation."""
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

from ..embedder.embed_controller import EmbeddingResult, embed_payload
from ..util import image_io


class EmbedTab(QWidget):
    """Tab widget orchestrating the adaptive embedding workflow."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.cover_path: Optional[Path] = None
        self.cover_image: Optional[np.ndarray] = None
        self.embed_result: Optional[EmbeddingResult] = None

        self._build_ui()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        cover_group = QGroupBox("Cover Image")
        cover_layout = QGridLayout(cover_group)

        self.cover_label = QLabel("No cover selected")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setMinimumHeight(220)
        self.cover_label.setStyleSheet("border: 1px solid #444; background: #111;")

        select_cover_btn = QPushButton("Select Cover PNG")
        select_cover_btn.clicked.connect(self._on_select_cover)

        cover_layout.addWidget(self.cover_label, 0, 0, 1, 2)
        cover_layout.addWidget(select_cover_btn, 1, 0, 1, 2)

        payload_group = QGroupBox("Secret Payload")
        payload_layout = QGridLayout(payload_group)

        self.payload_edit = QPlainTextEdit()
        self.payload_edit.setPlaceholderText("Enter secret text here or load a UTF-8 .txt file")

        load_txt_btn = QPushButton("Load .txt File")
        load_txt_btn.clicked.connect(self._on_load_text)

        payload_layout.addWidget(self.payload_edit, 0, 0, 1, 2)
        payload_layout.addWidget(load_txt_btn, 1, 1)

        controls_group = QGroupBox("Embedding Settings")
        controls_layout = QGridLayout(controls_group)

        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("Seed / Password")
        self.seed_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.aes_checkbox = QCheckBox("Enable AES Encryption")
        self.aes_checkbox.setChecked(True)

        self.run_button = QPushButton("Run Adaptive Embed")
        self.run_button.clicked.connect(self._on_run_embed)

        self.save_button = QPushButton("Save Stego Image")
        self.save_button.clicked.connect(self._on_save_stego)
        self.save_button.setEnabled(False)

        self.status_label = QLabel("Idle")
        self.status_label.setWordWrap(True)

        controls_layout.addWidget(QLabel("Seed / Password:"), 0, 0)
        controls_layout.addWidget(self.seed_input, 0, 1)
        controls_layout.addWidget(self.aes_checkbox, 1, 0, 1, 2)
        controls_layout.addWidget(self.run_button, 2, 0, 1, 2)
        controls_layout.addWidget(self.save_button, 3, 0, 1, 2)
        controls_layout.addWidget(self.status_label, 4, 0, 1, 2)

        layout.addWidget(cover_group)
        layout.addWidget(payload_group)
        layout.addWidget(controls_group)
        layout.addStretch(1)

    # -------------------------------------------------------------- Handlers --
    def _on_select_cover(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cover PNG",
            "",
            "PNG Images (*.png)",
        )
        if not file_path:
            return

        try:
            image = image_io.load_png(Path(file_path))
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Cover", str(exc))
            return

        self.cover_path = Path(file_path)
        self.cover_image = image
        self.embed_result = None
        self.save_button.setEnabled(False)
        self._update_preview(image)
        self.status_label.setText(
            f"Loaded cover: {self.cover_path.name} ({image.shape[1]}x{image.shape[0]})"
        )

    def _on_load_text(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load UTF-8 Text File",
            "",
            "Text Files (*.txt)",
        )
        if not file_path:
            return

        try:
            text = Path(file_path).read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Read Error", f"Failed to load file: {exc}")
            return

        self.payload_edit.setPlainText(text)
        self.status_label.setText(f"Loaded payload from {Path(file_path).name}")

    def _on_run_embed(self) -> None:
        if self.cover_image is None:
            QMessageBox.warning(self, "Missing Cover", "Please select a valid PNG cover image first.")
            return

        payload_text = self.payload_edit.toPlainText()
        if not payload_text:
            QMessageBox.warning(self, "Empty Payload", "Enter secret text or load a .txt file before embedding.")
            return

        seed = self.seed_input.text().strip()
        if not seed:
            QMessageBox.warning(self, "Missing Seed", "Provide a deterministic seed/password.")
            return

        self.status_label.setText("Running adaptive embedding…")
        self.run_button.setEnabled(False)

        try:
            result = embed_payload(
                cover_image=self.cover_image,
                payload_text=payload_text,
                seed=seed,
                enable_encryption=self.aes_checkbox.isChecked(),
            )
        except Exception as exc:  # pragma: no cover - UI feedback path
            self.run_button.setEnabled(True)
            self.status_label.setText("Embedding failed")
            QMessageBox.critical(self, "Embedding Error", str(exc))
            return

        self.run_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.embed_result = result

        self._update_preview(result.image)
        self.status_label.setText(
            f"Embedded {result.bits_embedded} bits (capacity {result.capacity_bits}).\n"
            f"PSNR: {result.metrics['psnr']:.2f} dB | SSIM: {result.metrics['ssim']:.4f}"
        )

    def _on_save_stego(self) -> None:
        if self.embed_result is None:
            QMessageBox.information(self, "Nothing to Save", "Run embedding first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Stego PNG",
            "stego_output.png",
            "PNG Images (*.png)",
        )
        if not file_path:
            return

        try:
            image_io.save_png(Path(file_path), self.embed_result.image)
        except OSError as exc:
            QMessageBox.critical(self, "Save Error", f"Failed to save PNG: {exc}")
            return

        QMessageBox.information(self, "Stego Saved", f"Stego image saved to {file_path}")

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
        self.cover_label.setPixmap(pixmap)
