"""RSA key utilities for the adaptive engine."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def generate_rsa_keypair(key_size: int = 2048) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return private_key, private_key.public_key()


def save_private_key_pem(
    private_key: rsa.RSAPrivateKey,
    path: str | Path,
    password: Optional[str] = None,
) -> None:
    if password:
        encryption = serialization.BestAvailableEncryption(password.encode("utf-8"))
    else:
        encryption = serialization.NoEncryption()
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )
    Path(path).write_bytes(pem)


def save_public_key_pem(public_key: rsa.RSAPublicKey, path: str | Path) -> None:
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    Path(path).write_bytes(pem)


def load_private_key_pem(path: str | Path, password: Optional[str] = None) -> rsa.RSAPrivateKey:
    data = Path(path).read_bytes()
    pwd = password.encode("utf-8") if password else None
    return serialization.load_pem_private_key(data, password=pwd)


def load_public_key_pem(path: str | Path) -> rsa.RSAPublicKey:
    data = Path(path).read_bytes()
    return serialization.load_pem_public_key(data)


def rsa_encrypt_key(public_key: rsa.RSAPublicKey, key_bytes: bytes) -> bytes:
    return public_key.encrypt(
        key_bytes,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


def rsa_decrypt_key(private_key: rsa.RSAPrivateKey, ek_bytes: bytes) -> bytes:
    return private_key.decrypt(
        ek_bytes,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


def fingerprint_public_key(public_key: rsa.RSAPublicKey) -> str:
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    digest = hashlib.sha256(der).hexdigest()
    return digest[:32]
