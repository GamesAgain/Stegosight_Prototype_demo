"""Embedding tab implementation."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)

from ..embedder.embed_controller import EmbedController, EmbedMetrics
from ..util.image_io import load_png, save_png
from ..util.exceptions import StegoEngineError


class EmbedWorker(QThread):
    progress_changed = pyqtSignal(int, str)
    finished_success = pyqtSignal(object, object)
    finished_error = pyqtSignal(str)

    def __init__(
        self,
        cover_path: str,
        secret_text: str,
        mode: str,
        password: Optional[str],
        aes_enabled: bool,
        public_key_path: Optional[str],
    ) -> None:
        super().__init__()
        self.cover_path = cover_path
        self.secret_text = secret_text
        self.mode = mode
        self.password = password
        self.aes_enabled = aes_enabled
        self.public_key_path = public_key_path

    def run(self) -> None:
        controller = EmbedController()
        try:
            self.progress_changed.emit(5, "Loading cover image…")
            self.progress_changed.emit(25, "Analyzing texture…")
            stego, metrics = controller.embed_from_text(
                cover_path=self.cover_path,
                secret_text=self.secret_text,
                mode=self.mode,
                password=self.password,
                aes_enabled=self.aes_enabled,
                public_key_path=self.public_key_path,
            )
            self.progress_changed.emit(75, "Embedding payload…")
            self.progress_changed.emit(90, "Computing quality metrics…")
            self.progress_changed.emit(100, "Done.")
            self.finished_success.emit(stego, metrics)
        except Exception as exc:  # pragma: no cover - GUI path
            self.finished_error.emit(str(exc))


def _array_to_pixmap(arr: np.ndarray) -> QPixmap:
    h, w, _ = arr.shape
    image = QImage(arr.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(image.copy())


class EmbedTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.cover_path: Optional[str] = None
        self.cover_image: Optional[np.ndarray] = None
        self.stego_image: Optional[np.ndarray] = None
        self.public_key_path: Optional[str] = None

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        cover_group = QGroupBox("Cover Image")
        cover_layout = QHBoxLayout()
        self.cover_button = QPushButton("Select Cover PNG…")
        self.cover_button.clicked.connect(self._select_cover)
        self.cover_preview = QLabel("No cover selected")
        self.cover_preview.setFixedSize(240, 240)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_info = QLabel("–")
        cover_layout.addWidget(self.cover_button)
        cover_layout.addWidget(self.cover_preview)
        cover_layout.addWidget(self.cover_info)
        cover_group.setLayout(cover_layout)

        payload_group = QGroupBox("Payload")
        payload_layout = QVBoxLayout()
        self.payload_edit = QTextEdit()
        self.load_text_button = QPushButton("Load .txt…")
        self.load_text_button.clicked.connect(self._load_text_file)
        payload_layout.addWidget(self.payload_edit)
        payload_layout.addWidget(self.load_text_button)
        payload_group.setLayout(payload_layout)

        mode_group = QGroupBox("Mode")
        form = QFormLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Password (Symmetric)", "Public Key (Asymmetric)"])
        self.mode_combo.currentIndexChanged.connect(self._update_mode_visibility)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.aes_checkbox = QCheckBox("Enable AES Encryption")
        self.public_key_edit = QLineEdit()
        self.public_key_edit.setReadOnly(True)
        self.public_key_button = QPushButton("Browse…")
        self.public_key_button.clicked.connect(self._select_public_key)
        public_key_row = QHBoxLayout()
        public_key_row.addWidget(self.public_key_edit)
        public_key_row.addWidget(self.public_key_button)
        public_key_container = QWidget()
        public_key_container.setLayout(public_key_row)
        self.mode_info = QLabel("Header always encrypted; payload optional.")
        form.addRow("Mode", self.mode_combo)
        form.addRow("Password", self.password_edit)
        form.addRow("Payload Encryption", self.aes_checkbox)
        form.addRow("Public Key", public_key_container)
        form.addRow("Info", self.mode_info)
        mode_group.setLayout(form)

        controls_layout = QHBoxLayout()
        self.run_button = QPushButton("Run Adaptive Embed")
        self.run_button.clicked.connect(self._run_embedding)
        self.save_button = QPushButton("Save Stego…")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._save_stego)
        controls_layout.addWidget(self.run_button)
        controls_layout.addWidget(self.save_button)

        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Idle.")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)

        main_layout.addWidget(cover_group)
        main_layout.addWidget(payload_group)
        main_layout.addWidget(mode_group)
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(progress_layout)
        main_layout.addStretch(1)

        self._update_mode_visibility()

    def _select_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Cover PNG", str(Path.home()), "PNG Images (*.png)")
        if not path:
            return
        try:
            img = load_png(path)
        except StegoEngineError as exc:
            QMessageBox.critical(self, "Invalid Cover", str(exc))
            return
        self.cover_path = path
        self.cover_image = img
        pixmap = _array_to_pixmap(img)
        self.cover_preview.setPixmap(pixmap.scaled(self.cover_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.cover_info.setText(f"{img.shape[1]}×{img.shape[0]}")

    def _load_text_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Text", str(Path.home()), "Text Files (*.txt)")
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", str(exc))
            return
        self.payload_edit.setPlainText(text)

    def _select_public_key(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Public Key", str(Path.home()), "PEM Files (*.pem)")
        if not path:
            return
        self.public_key_path = path
        self.public_key_edit.setText(path)

    def set_public_key_path(self, path: str) -> None:
        self.public_key_path = path
        self.public_key_edit.setText(path)

    def _update_mode_visibility(self) -> None:
        is_symmetric = self.mode_combo.currentIndex() == 0
        self.password_edit.setEnabled(is_symmetric)
        self.aes_checkbox.setEnabled(is_symmetric)
        self.public_key_button.setEnabled(not is_symmetric)
        self.mode_info.setText(
            "Public key mode hides header+payload inside hybrid RSA+AES" if not is_symmetric else "Header always encrypted"
        )

    def _run_embedding(self) -> None:
        if not self.cover_path:
            QMessageBox.warning(self, "Missing Cover", "Select a cover PNG first.")
            return
        payload_text = self.payload_edit.toPlainText()
        if not payload_text:
            QMessageBox.warning(self, "Empty Payload", "Enter a secret message or load a .txt file.")
            return
        mode = "password" if self.mode_combo.currentIndex() == 0 else "public"
        password = self.password_edit.text() if mode == "password" else None
        if mode == "password" and not password:
            QMessageBox.warning(self, "Password Required", "Enter a password for symmetric mode.")
            return
        public_key_path = self.public_key_path if mode == "public" else None
        if mode == "public" and not public_key_path:
            QMessageBox.warning(self, "Public Key Required", "Select a public key PEM file.")
            return
        self.progress_bar.setValue(0)
        self.status_label.setText("Preparing…")
        self.run_button.setEnabled(False)
        self.worker = EmbedWorker(
            cover_path=self.cover_path,
            secret_text=payload_text,
            mode=mode,
            password=password,
            aes_enabled=self.aes_checkbox.isChecked(),
            public_key_path=public_key_path,
        )
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.finished_success.connect(self._on_embed_finished)
        self.worker.finished_error.connect(self._on_embed_error)
        self.worker.start()

    def _on_progress(self, value: int, text: str) -> None:
        self.progress_bar.setValue(value)
        self.status_label.setText(text)

    def _on_embed_finished(self, stego: np.ndarray, metrics: EmbedMetrics) -> None:
        self.run_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.stego_image = stego
        pixmap = _array_to_pixmap(stego)
        self.cover_preview.setPixmap(pixmap.scaled(self.cover_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.status_label.setText(
            f"Embed complete – PSNR {metrics.psnr:.2f} dB, SSIM {metrics.ssim:.4f}, drift {metrics.hist_drift:.4f}"
        )
        self.progress_bar.setValue(100)

    def _on_embed_error(self, message: str) -> None:
        self.run_button.setEnabled(True)
        self.status_label.setText("Idle.")
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Embedding Failed", message)

    def _save_stego(self) -> None:
        if self.stego_image is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Stego PNG", str(Path.home()), "PNG Images (*.png)")
        if not path:
            return
        try:
            save_png(path, self.stego_image)
            QMessageBox.information(self, "Saved", f"Stego image saved to {path}")
        except StegoEngineError as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
