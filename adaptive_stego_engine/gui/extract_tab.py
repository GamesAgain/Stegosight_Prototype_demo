"""Extraction tab UI."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)

from ..extractor.extract_controller import ExtractController
from ..util.exceptions import StegoEngineError
from ..util.image_io import load_png


def _array_to_pixmap(arr):
    h, w, _ = arr.shape
    image = QImage(arr.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(image.copy())


class ExtractWorker(QThread):
    progress_changed = pyqtSignal(int, str)
    finished_success = pyqtSignal(str)
    finished_error = pyqtSignal(str)

    def __init__(
        self,
        stego_path: str,
        mode: str,
        password: Optional[str],
        private_key_path: Optional[str],
    ) -> None:
        super().__init__()
        self.stego_path = stego_path
        self.mode = mode
        self.password = password
        self.private_key_path = private_key_path

    def run(self) -> None:
        controller = ExtractController()
        try:
            self.progress_changed.emit(5, "Loading stego image…")
            self.progress_changed.emit(25, "Analyzing texture…")
            if self.mode == "password":
                payload = controller.extract_from_image_symmetric(self.stego_path, self.password or "")
            else:
                payload = controller.extract_from_image_asymmetric(self.stego_path, self.private_key_path or "")
            self.progress_changed.emit(75, "Decrypting / validating header…")
            text = payload.decode("utf-8", errors="replace")
            self.progress_changed.emit(100, "Done.")
            self.finished_success.emit(text)
        except Exception as exc:  # pragma: no cover - GUI path
            self.finished_error.emit(str(exc))


class ExtractTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.stego_path: Optional[str] = None
        self.private_key_path: Optional[str] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        image_group = QGroupBox("Stego Image")
        image_layout = QHBoxLayout()
        self.select_button = QPushButton("Select Stego PNG…")
        self.select_button.clicked.connect(self._select_stego)
        self.preview = QLabel("No image")
        self.preview.setFixedSize(240, 240)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label = QLabel("–")
        image_layout.addWidget(self.select_button)
        image_layout.addWidget(self.preview)
        image_layout.addWidget(self.info_label)
        image_group.setLayout(image_layout)

        mode_group = QGroupBox("Mode")
        form = QFormLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Password (Symmetric)", "Public Key (Asymmetric)"])
        self.mode_combo.currentIndexChanged.connect(self._update_mode)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.aes_hint = QCheckBox("Payload is AES encrypted (legacy)")
        self.private_key_edit = QLineEdit()
        self.private_key_edit.setReadOnly(True)
        self.private_key_button = QPushButton("Browse…")
        self.private_key_button.clicked.connect(self._select_private_key)
        private_row = QHBoxLayout()
        private_row.addWidget(self.private_key_edit)
        private_row.addWidget(self.private_key_button)
        private_widget = QWidget()
        private_widget.setLayout(private_row)
        self.mode_info = QLabel("Symmetric mode requires password used during embedding.")
        form.addRow("Mode", self.mode_combo)
        form.addRow("Password", self.password_edit)
        form.addRow("AES Hint", self.aes_hint)
        form.addRow("Private Key", private_widget)
        form.addRow("Info", self.mode_info)
        mode_group.setLayout(form)

        output_group = QGroupBox("Extracted Payload")
        output_layout = QVBoxLayout()
        self.output_edit = QTextEdit()
        self.save_text_button = QPushButton("Save as .txt…")
        self.save_text_button.clicked.connect(self._save_text)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.save_text_button)
        output_group.setLayout(output_layout)

        controls = QHBoxLayout()
        self.run_button = QPushButton("Run Extraction")
        self.run_button.clicked.connect(self._run_extraction)
        controls.addWidget(self.run_button)

        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Idle.")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)

        layout.addWidget(image_group)
        layout.addWidget(mode_group)
        layout.addWidget(output_group)
        layout.addLayout(controls)
        layout.addLayout(progress_layout)
        layout.addStretch(1)

        self._update_mode()

    def _select_stego(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Stego PNG", str(Path.home()), "PNG Images (*.png)")
        if not path:
            return
        try:
            img = load_png(path)
        except StegoEngineError as exc:
            QMessageBox.critical(self, "Invalid Image", str(exc))
            return
        self.stego_path = path
        pixmap = _array_to_pixmap(img)
        self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.info_label.setText(f"{img.shape[1]}×{img.shape[0]}")

    def _select_private_key(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Private Key", str(Path.home()), "PEM Files (*.pem)")
        if not path:
            return
        self.private_key_path = path
        self.private_key_edit.setText(path)

    def set_private_key_path(self, path: str) -> None:
        self.private_key_path = path
        self.private_key_edit.setText(path)

    def _update_mode(self) -> None:
        is_symmetric = self.mode_combo.currentIndex() == 0
        self.password_edit.setEnabled(is_symmetric)
        self.aes_hint.setEnabled(is_symmetric)
        self.private_key_button.setEnabled(not is_symmetric)
        self.mode_info.setText(
            "Public-key mode requires matching private key" if not is_symmetric else "Provide password used for embedding"
        )

    def _run_extraction(self) -> None:
        if not self.stego_path:
            QMessageBox.warning(self, "Missing Stego", "Select a stego PNG first.")
            return
        mode = "password" if self.mode_combo.currentIndex() == 0 else "public"
        password = self.password_edit.text() if mode == "password" else None
        if mode == "password" and not password:
            QMessageBox.warning(self, "Password Required", "Enter password used during embedding.")
            return
        private_key_path = self.private_key_path if mode == "public" else None
        if mode == "public" and not private_key_path:
            QMessageBox.warning(self, "Key Required", "Select private key PEM used for embedding.")
            return
        self.run_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Working…")
        self.worker = ExtractWorker(
            stego_path=self.stego_path,
            mode=mode,
            password=password,
            private_key_path=private_key_path,
        )
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.finished_success.connect(self._on_success)
        self.worker.finished_error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, value: int, text: str) -> None:
        self.progress_bar.setValue(value)
        self.status_label.setText(text)

    def _on_success(self, text: str) -> None:
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText("Extraction complete.")
        self.output_edit.setPlainText(text)

    def _on_error(self, message: str) -> None:
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Idle.")
        QMessageBox.critical(self, "Extraction Failed", message)

    def _save_text(self) -> None:
        text = self.output_edit.toPlainText()
        if not text:
            QMessageBox.information(self, "No Data", "No text to save.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Text", str(Path.home()), "Text Files (*.txt)")
        if not path:
            return
        Path(path).write_text(text, encoding="utf-8")
        QMessageBox.information(self, "Saved", f"Text saved to {path}")
