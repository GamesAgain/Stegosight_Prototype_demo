"""Embed tab implementation for the Adaptive Steganography Engine GUI."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

from ..embedder.embed_controller import AdaptiveEmbedder
from ..util.image_io import InvalidImageFormatError, load_png, save_png


class EmbedTab(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._cover_array: Optional[np.ndarray] = None
        self._cover_mode: str = "RGB"
        self._stego_result: Optional[np.ndarray] = None
        self._seed_input = QtWidgets.QLineEdit()
        self._encryption_checkbox = QtWidgets.QCheckBox("Enable AES Encryption")
        self._mode_combo = QtWidgets.QComboBox()
        self._payload_edit = QtWidgets.QPlainTextEdit()
        self._psnr_label = QtWidgets.QLabel("PSNR: --")
        self._ssim_label = QtWidgets.QLabel("SSIM: --")
        self._preview_label = QtWidgets.QLabel()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        file_layout = QtWidgets.QHBoxLayout()
        select_button = QtWidgets.QPushButton("Select Cover PNG")
        select_button.clicked.connect(self._select_cover)
        file_layout.addWidget(select_button)
        load_txt_button = QtWidgets.QPushButton("Load .txt")
        load_txt_button.clicked.connect(self._load_text_file)
        file_layout.addWidget(load_txt_button)
        layout.addLayout(file_layout)

        self._preview_label.setFixedHeight(200)
        self._preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet("border: 1px solid #666;")
        layout.addWidget(self._preview_label)

        layout.addWidget(QtWidgets.QLabel("Secret Text (UTF-8):"))
        self._payload_edit.setPlaceholderText("Type or load secret text...")
        layout.addWidget(self._payload_edit)

        form = QtWidgets.QFormLayout()
        self._seed_input.setPlaceholderText("Seed / Password")
        form.addRow("Seed / Password:", self._seed_input)

        self._encryption_checkbox.stateChanged.connect(self._toggle_mode_combo)
        form.addRow(self._encryption_checkbox)

        self._mode_combo.addItems(["AES-GCM", "AES-CTR + HMAC"])
        self._mode_combo.setEnabled(False)
        form.addRow("Mode:", self._mode_combo)
        layout.addLayout(form)

        run_button = QtWidgets.QPushButton("Run Adaptive Embed")
        run_button.clicked.connect(self._run_embed)
        layout.addWidget(run_button)

        metrics_layout = QtWidgets.QHBoxLayout()
        metrics_layout.addWidget(self._psnr_label)
        metrics_layout.addWidget(self._ssim_label)
        layout.addLayout(metrics_layout)

        save_button = QtWidgets.QPushButton("Save Stego")
        save_button.clicked.connect(self._save_stego)
        layout.addWidget(save_button)

        layout.addStretch()

    def _toggle_mode_combo(self, state: int) -> None:
        self._mode_combo.setEnabled(state == QtCore.Qt.CheckState.Checked.value)

    def _select_cover(self) -> None:
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("PNG Images (*.png)")
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            path = file_dialog.selectedFiles()[0]
            try:
                array, mode = load_png(path)
            except InvalidImageFormatError as exc:
                QtWidgets.QMessageBox.critical(self, "Invalid Image", str(exc))
                return
            self._cover_array = array
            self._cover_mode = mode
            self._stego_result = None
            self._show_preview(array)

    def _load_text_file(self) -> None:
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("Text Files (*.txt)")
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            path = file_dialog.selectedFiles()[0]
            try:
                text = Path(path).read_text(encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                QtWidgets.QMessageBox.critical(self, "File Error", str(exc))
                return
            self._payload_edit.setPlainText(text)

    def _run_embed(self) -> None:
        if self._cover_array is None:
            QtWidgets.QMessageBox.warning(self, "No Cover", "Please load a cover PNG image first.")
            return
        payload_text = self._payload_edit.toPlainText()
        if not payload_text:
            QtWidgets.QMessageBox.warning(self, "No Payload", "Secret text cannot be empty.")
            return
        seed = self._seed_input.text().strip()
        if not seed:
            QtWidgets.QMessageBox.warning(self, "Missing Seed", "A seed/password is required.")
            return
        payload_bytes = payload_text.encode("utf-8")
        encrypt = self._encryption_checkbox.isChecked()
        mode = self._mode_combo.currentText()
        try:
            embedder = AdaptiveEmbedder(seed=seed, encrypt=encrypt, password=seed, mode=mode)
            result = embedder.embed(self._cover_array, payload_bytes)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Embedding Failed", str(exc))
            return
        self._stego_result = result.stego_image
        self._psnr_label.setText(f"PSNR: {result.psnr_value:.2f} dB")
        self._ssim_label.setText(f"SSIM: {result.ssim_value:.4f}")
        self._show_preview(result.stego_image)
        QtWidgets.QMessageBox.information(self, "Success", "Payload embedded successfully.")

    def _save_stego(self) -> None:
        if self._stego_result is None:
            QtWidgets.QMessageBox.warning(self, "No Stego", "Run embedding before saving.")
            return
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("PNG Images (*.png)")
        file_dialog.setDefaultSuffix("png")
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            path = file_dialog.selectedFiles()[0]
            try:
                save_png(path, self._stego_result, mode=self._cover_mode)
            except Exception as exc:  # noqa: BLE001
                QtWidgets.QMessageBox.critical(self, "Save Error", str(exc))
                return
            QtWidgets.QMessageBox.information(self, "Saved", "Stego image saved successfully.")

    def _show_preview(self, array: np.ndarray) -> None:
        height, width, _ = array.shape
        image = QtGui.QImage(array.data, width, height, width * 3, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(image.copy())
        self._preview_label.setPixmap(pixmap.scaled(
            self._preview_label.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        ))
