"""Extraction tab implementation."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets

from ..extractor.extract_controller import AdaptiveExtractor
from ..util.image_io import InvalidImageFormatError, load_png


class ExtractTab(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._stego_array: Optional[np.ndarray] = None
        self._password_input = QtWidgets.QLineEdit()
        self._encrypted_checkbox = QtWidgets.QCheckBox("Payload is encrypted")
        self._output_edit = QtWidgets.QPlainTextEdit()
        self._preview_label = QtWidgets.QLabel()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        select_button = QtWidgets.QPushButton("Select Stego PNG")
        select_button.clicked.connect(self._select_stego)
        layout.addWidget(select_button)

        self._preview_label.setFixedHeight(200)
        self._preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet("border: 1px solid #666;")
        layout.addWidget(self._preview_label)

        form = QtWidgets.QFormLayout()
        self._password_input.setPlaceholderText("Seed / Password")
        form.addRow("Seed / Password:", self._password_input)
        form.addRow(self._encrypted_checkbox)
        layout.addLayout(form)

        extract_button = QtWidgets.QPushButton("Extract")
        extract_button.clicked.connect(self._run_extract)
        layout.addWidget(extract_button)

        layout.addWidget(QtWidgets.QLabel("Recovered Payload:"))
        self._output_edit.setReadOnly(False)
        layout.addWidget(self._output_edit)

        save_button = QtWidgets.QPushButton("Save .txt")
        save_button.clicked.connect(self._save_text)
        layout.addWidget(save_button)

        layout.addStretch()

    def _select_stego(self) -> None:
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setNameFilter("PNG Images (*.png)")
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            path = file_dialog.selectedFiles()[0]
            try:
                array, _ = load_png(path)
            except InvalidImageFormatError as exc:
                QtWidgets.QMessageBox.critical(self, "Invalid Image", str(exc))
                return
            self._stego_array = array
            self._show_preview(array)

    def _run_extract(self) -> None:
        if self._stego_array is None:
            QtWidgets.QMessageBox.warning(self, "No Stego", "Load a stego PNG first.")
            return
        seed = self._password_input.text().strip()
        if not seed:
            QtWidgets.QMessageBox.warning(self, "Missing Seed", "Seed/password is required.")
            return
        extractor = AdaptiveExtractor(seed=seed, password=seed if self._encrypted_checkbox.isChecked() else "")
        try:
            result = extractor.extract(self._stego_array)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Extraction Failed", str(exc))
            return
        if result.encrypted and not self._encrypted_checkbox.isChecked():
            QtWidgets.QMessageBox.warning(self, "Encrypted", "Payload was encrypted. Enable checkbox and retry.")
            return
        try:
            text = result.payload.decode("utf-8")
        except UnicodeDecodeError:
            text = "<binary payload>"
        self._output_edit.setPlainText(text)
        QtWidgets.QMessageBox.information(self, "Success", "Payload extracted successfully.")

    def _save_text(self) -> None:
        text = self._output_edit.toPlainText()
        if not text:
            QtWidgets.QMessageBox.warning(self, "No Text", "Nothing to save.")
            return
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix("txt")
        file_dialog.setNameFilter("Text Files (*.txt)")
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            path = file_dialog.selectedFiles()[0]
            try:
                Path(path).write_text(text, encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                QtWidgets.QMessageBox.critical(self, "Save Error", str(exc))
                return
            QtWidgets.QMessageBox.information(self, "Saved", "Payload written to disk.")

    def _show_preview(self, array: np.ndarray) -> None:
        height, width, _ = array.shape
        image = QtGui.QImage(array.data, width, height, width * 3, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(image.copy())
        self._preview_label.setPixmap(pixmap.scaled(
            self._preview_label.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        ))
