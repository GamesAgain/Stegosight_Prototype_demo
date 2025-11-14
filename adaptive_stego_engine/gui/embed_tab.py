"""Embed tab implementation for the adaptive steganography GUI."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from ..embedder import embed_controller
from ..util import header as header_util, image_io


class EmbedTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.cover_image: Optional[np.ndarray] = None
        self.stego_image: Optional[np.ndarray] = None
        self.cover_path: Optional[Path] = None

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        file_layout = QHBoxLayout()
        self.cover_label = QLabel("No cover selected")
        self.btn_select_cover = QPushButton("Select Cover PNG")
        self.btn_select_cover.clicked.connect(self._select_cover)
        file_layout.addWidget(self.cover_label)
        file_layout.addWidget(self.btn_select_cover)
        layout.addLayout(file_layout)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(320, 320)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter secret text or load a .txt file")
        layout.addWidget(self.text_edit)

        load_layout = QHBoxLayout()
        self.btn_load_text = QPushButton("Load .txt")
        self.btn_load_text.clicked.connect(self._load_text_file)
        load_layout.addWidget(self.btn_load_text)
        layout.addLayout(load_layout)

        form_layout = QGridLayout()
        form_layout.addWidget(QLabel("Seed / Password"), 0, 0)
        self.seed_input = QLineEdit()
        form_layout.addWidget(self.seed_input, 0, 1)

        self.chk_encrypt = QCheckBox("Enable AES Encryption")
        self.chk_encrypt.stateChanged.connect(self._toggle_mode)
        form_layout.addWidget(self.chk_encrypt, 1, 0, 1, 2)

        form_layout.addWidget(QLabel("Cipher Mode"), 2, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([header_util.MODE_GCM, header_util.MODE_CTR_HMAC])
        self.mode_combo.setEnabled(False)
        form_layout.addWidget(self.mode_combo, 2, 1)
        layout.addLayout(form_layout)

        self.btn_run = QPushButton("Run Adaptive Embed")
        self.btn_run.clicked.connect(self._run_embedding)
        layout.addWidget(self.btn_run)

        metrics_layout = QHBoxLayout()
        self.psnr_label = QLabel("PSNR: N/A")
        self.ssim_label = QLabel("SSIM: N/A")
        metrics_layout.addWidget(self.psnr_label)
        metrics_layout.addWidget(self.ssim_label)
        layout.addLayout(metrics_layout)

        self.btn_save = QPushButton("Save Stego PNG")
        self.btn_save.clicked.connect(self._save_stego)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)

    def _toggle_mode(self, state: int) -> None:
        self.mode_combo.setEnabled(state == Qt.CheckState.Checked.value)

    def _select_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "PNG Images (*.png)")
        if not path:
            return
        try:
            self.cover_image = image_io.load_png(path)
        except Exception as exc:
            QMessageBox.critical(self, "Invalid Cover", str(exc))
            return
        self.cover_path = Path(path)
        self.cover_label.setText(self.cover_path.name)
        self._update_preview(self.cover_image)

    def _update_preview(self, image: Optional[np.ndarray]) -> None:
        if image is None:
            self.preview_label.clear()
            return
        h, w, _ = image.shape
        qimage = QImage(image.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage).scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(pixmap)

    def _load_text_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Payload Text", "", "Text Files (*.txt)")
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "File Error", str(exc))
            return
        self.text_edit.setPlainText(text)

    def _payload_bytes(self) -> bytes:
        text = self.text_edit.toPlainText()
        return text.encode("utf-8")

    def _run_embedding(self) -> None:
        if self.cover_image is None:
            QMessageBox.warning(self, "Missing Cover", "Please select a cover PNG.")
            return
        payload = self._payload_bytes()
        if not payload:
            QMessageBox.warning(self, "Empty Payload", "Please enter secret text or load a file.")
            return
        seed = self.seed_input.text().strip() or "default-seed"
        password = None
        if self.chk_encrypt.isChecked():
            password = self.seed_input.text()
            if not password:
                QMessageBox.warning(self, "Missing Password", "Provide a password when encryption is enabled.")
                return
        mode = self.mode_combo.currentText()

        try:
            result = embed_controller.embed(
                cover_image=self.cover_image,
                payload=payload,
                seed=seed,
                password=password,
                mode=mode,
            )
        except embed_controller.QualityError as exc:
            QMessageBox.critical(self, "Quality Error", str(exc))
            return
        except embed_controller.EncryptionError as exc:
            QMessageBox.critical(self, "Encryption Error", str(exc))
            return
        except embed_controller.EmbeddingError as exc:
            QMessageBox.critical(self, "Embedding Error", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Unexpected Error", str(exc))
            return

        self.stego_image = result.stego_image
        self.psnr_label.setText(f"PSNR: {result.psnr:.2f} dB")
        self.ssim_label.setText(f"SSIM: {result.ssim:.4f}")
        self.btn_save.setEnabled(True)
        self._update_preview(self.stego_image)

    def _save_stego(self) -> None:
        if self.stego_image is None:
            return
        default_name = "stego.png"
        path, _ = QFileDialog.getSaveFileName(self, "Save Stego Image", str(self.cover_path.parent if self.cover_path else Path.home()), "PNG Images (*.png)", options=QFileDialog.Option.DontUseNativeDialog)
        if not path:
            return
        try:
            image_io.save_png(path, self.stego_image)
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            return
        QMessageBox.information(self, "Stego Saved", f"Stego image saved to {path}")
