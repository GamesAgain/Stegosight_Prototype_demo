"""Header construction and validation utilities."""
from __future__ import annotations

import os
from dataclasses import dataclass

from .crypto import AESEncrypted, aes_ctr_decrypt, aes_ctr_encrypt, aes_gcm_decrypt, aes_gcm_encrypt, derive_key

MAGIC = b"STEGO"
HEADER_LENGTH = len(MAGIC) + 4


@dataclass
class EncryptedPackage:
    mode: str
    salt: bytes
    nonce: bytes
    ciphertext: bytes
    tag: bytes | None = None
    hmac_tag: bytes | None = None

    def encode(self) -> bytes:
        header = bytearray()
        header.append(1 if self.mode == "AES-GCM" else 2)
        header.append(len(self.salt))
        header.extend(self.salt)
        header.append(len(self.nonce))
        header.extend(self.nonce)
        header.extend(len(self.ciphertext).to_bytes(4, "big"))
        header.extend(self.ciphertext)
        if self.mode == "AES-GCM":
            if self.tag is None:
                raise ValueError('Missing GCM authentication tag')
            header.append(len(self.tag))
            header.extend(self.tag)
        else:
            if self.hmac_tag is None:
                raise ValueError('Missing HMAC tag for AES-CTR')
            header.append(len(self.hmac_tag))
            header.extend(self.hmac_tag)
        return bytes(header)

    @staticmethod
    def decode(data: bytes) -> "EncryptedPackage":
        cursor = 0
        if len(data) < 3:
            raise ValueError('Encrypted package too short')
        mode_id = data[cursor]
        cursor += 1
        mode = "AES-GCM" if mode_id == 1 else "AES-CTR"
        salt_len = data[cursor]
        cursor += 1
        if cursor + salt_len > len(data):
            raise ValueError('Invalid salt length in encrypted package')
        salt = data[cursor:cursor + salt_len]
        cursor += salt_len
        nonce_len = data[cursor]
        cursor += 1
        if cursor + nonce_len > len(data):
            raise ValueError('Invalid nonce length in encrypted package')
        nonce = data[cursor:cursor + nonce_len]
        cursor += nonce_len
        if cursor + 4 > len(data):
            raise ValueError('Encrypted package truncated before ciphertext length')
        ct_len = int.from_bytes(data[cursor:cursor + 4], "big")
        cursor += 4
        if cursor + ct_len > len(data):
            raise ValueError('Ciphertext length exceeds package size')
        ciphertext = data[cursor:cursor + ct_len]
        cursor += ct_len
        tag = None
        hmac_tag = None
        if mode == "AES-GCM":
            if cursor >= len(data):
                raise ValueError('Missing GCM tag length byte')
            tag_len = data[cursor]
            cursor += 1
            if cursor + tag_len > len(data):
                raise ValueError('Invalid GCM tag length')
            tag = data[cursor:cursor + tag_len]
            cursor += tag_len
        else:
            if cursor >= len(data):
                raise ValueError('Missing HMAC length byte')
            hmac_len = data[cursor]
            cursor += 1
            if cursor + hmac_len > len(data):
                raise ValueError('Invalid HMAC length')
            hmac_tag = data[cursor:cursor + hmac_len]
            cursor += hmac_len
        return EncryptedPackage(
            mode=mode,
            salt=salt,
            nonce=nonce,
            ciphertext=ciphertext,
            tag=tag,
            hmac_tag=hmac_tag,
        )


def build_plain_header(payload_length: int) -> bytes:
    return MAGIC + payload_length.to_bytes(4, "big")


def encrypt_payload(header: bytes, payload: bytes, password: str, mode: str) -> EncryptedPackage:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    plaintext = header + payload
    if mode == "AES-GCM":
        encrypted = aes_gcm_encrypt(key, plaintext, associated_data=MAGIC)
        return EncryptedPackage(
            mode=mode,
            salt=salt,
            nonce=encrypted.nonce,
            ciphertext=encrypted.ciphertext,
            tag=encrypted.tag,
        )
    encrypted = aes_ctr_encrypt(key, plaintext)
    return EncryptedPackage(
        mode=mode,
        salt=salt,
        nonce=encrypted.nonce,
        ciphertext=encrypted.ciphertext,
        hmac_tag=encrypted.hmac_tag,
    )


def decrypt_payload(package: EncryptedPackage, password: str) -> bytes:
    key = derive_key(password, package.salt)
    if package.mode == "AES-GCM":
        encrypted = AESEncrypted(
            ciphertext=package.ciphertext,
            nonce=package.nonce,
            tag=package.tag,
        )
        return aes_gcm_decrypt(key, encrypted, associated_data=MAGIC)
    encrypted = AESEncrypted(
        ciphertext=package.ciphertext,
        nonce=package.nonce,
        hmac_tag=package.hmac_tag,
    )
    return aes_ctr_decrypt(key, encrypted)


def validate_header(header: bytes) -> int:
    if len(header) < HEADER_LENGTH:
        raise ValueError("Header is too short")
    magic = header[:5]
    if magic != MAGIC:
        raise ValueError("Header magic mismatch")
    length = int.from_bytes(header[5:9], "big")
    return length
