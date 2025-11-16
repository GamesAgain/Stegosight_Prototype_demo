"""Key management tab."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..util.asym_crypto import (
    fingerprint_public_key,
    generate_rsa_keypair,
    load_private_key_pem,
    load_public_key_pem,
    save_private_key_pem,
    save_public_key_pem,
)


class KeyTab(QWidget):
    def __init__(self, embed_tab, extract_tab) -> None:
        super().__init__()
        self.embed_tab = embed_tab
        self.extract_tab = extract_tab
        self.public_path: Optional[str] = None
        self.private_path: Optional[str] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        generate_group = QGroupBox("Generate RSA Key Pair")
        generate_layout = QFormLayout()
        self.size_combo = QComboBox()
        self.size_combo.addItems(["2048", "3072"])
        self.generate_button = QPushButton("Generate Key Pair")
        self.generate_button.clicked.connect(self._generate_keys)
        generate_layout.addRow("Key Size", self.size_combo)
        generate_layout.addRow(self.generate_button)
        generate_group.setLayout(generate_layout)

        manage_group = QGroupBox("Loaded Keys")
        manage_layout = QFormLayout()
        self.public_label = QLabel("No public key loaded")
        self.private_label = QLabel("No private key loaded")
        load_public_btn = QPushButton("Load Public Key…")
        load_public_btn.clicked.connect(self._load_public)
        load_private_btn = QPushButton("Load Private Key…")
        load_private_btn.clicked.connect(self._load_private)
        manage_layout.addRow("Public Key", self.public_label)
        manage_layout.addRow(load_public_btn)
        manage_layout.addRow("Private Key", self.private_label)
        manage_layout.addRow(load_private_btn)
        manage_group.setLayout(manage_layout)

        layout.addWidget(generate_group)
        layout.addWidget(manage_group)
        layout.addStretch(1)

    def _generate_keys(self) -> None:
        key_size = int(self.size_combo.currentText())
        try:
            private_key, public_key = generate_rsa_keypair(key_size)
        except Exception as exc:
            QMessageBox.critical(self, "Key Generation Failed", str(exc))
            return
        priv_path, _ = QFileDialog.getSaveFileName(self, "Save Private Key", str(Path.home()), "PEM Files (*.pem)")
        if not priv_path:
            return
        pub_path, _ = QFileDialog.getSaveFileName(self, "Save Public Key", str(Path.home()), "PEM Files (*.pem)")
        if not pub_path:
            return
        try:
            save_private_key_pem(private_key, priv_path)
            save_public_key_pem(public_key, pub_path)
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))
            return
        fingerprint = fingerprint_public_key(public_key)
        QMessageBox.information(
            self,
            "Keys Generated",
            f"Private key saved to {priv_path}\nPublic key saved to {pub_path}\nFingerprint: {fingerprint}",
        )
        self.public_path = pub_path
        self.private_path = priv_path
        self.public_label.setText(pub_path)
        self.private_label.setText(priv_path)
        self.embed_tab.set_public_key_path(pub_path)
        self.extract_tab.set_private_key_path(priv_path)

    def _load_public(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Public Key", str(Path.home()), "PEM Files (*.pem)")
        if not path:
            return
        try:
            public = load_public_key_pem(path)
        except Exception as exc:
            QMessageBox.critical(self, "Load Failed", str(exc))
            return
        self.public_path = path
        self.public_label.setText(path)
        fingerprint = fingerprint_public_key(public)
        QMessageBox.information(self, "Public Key Loaded", f"Fingerprint: {fingerprint}")
        self.embed_tab.set_public_key_path(path)

    def _load_private(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Private Key", str(Path.home()), "PEM Files (*.pem)")
        if not path:
            return
        try:
            private = load_private_key_pem(path)
        except Exception as exc:
            QMessageBox.critical(self, "Load Failed", str(exc))
            return
        self.private_path = path
        self.private_label.setText(path)
        fingerprint = fingerprint_public_key(private.public_key())
        QMessageBox.information(self, "Private Key Loaded", f"Fingerprint: {fingerprint}")
        self.extract_tab.set_private_key_path(path)
