"""Bit readers for extracting payloads from the bitstream."""
from __future__ import annotations

from typing import List

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..util import bitstream, header
from ..util.asym_crypto import load_private_key_pem, rsa_decrypt_key
from ..util.crypto import PBKDF2_SALT_LEN, aes_gcm_decrypt, derive_key_pbkdf2
from ..util.exceptions import StegoEngineError


def read_payload_symmetric_from_bits(bits: List[int], password: str) -> bytes:
    if not password:
        raise StegoEngineError("Password is required for extraction")
    data = bitstream.bits_to_bytes(bits)
    info = bitstream.unpack_symmetric_stream(data)
    salt = info["salt"]
    if len(salt) != PBKDF2_SALT_LEN:
        raise StegoEngineError("Invalid salt length")
    key = derive_key_pbkdf2(password, salt)
    header_plain = header.decrypt_header(info["header_nonce"], info["header_ct"], key)
    payload_len = header.validate_header(header_plain)
    if info["payload_encrypted"]:
        payload_nonce = info["payload_nonce"]
        payload_ct = info["payload_data"]
        expected_len = payload_len + 16
        if len(payload_ct) != expected_len:
            raise StegoEngineError("Corrupted encrypted payload length")
        payload = aes_gcm_decrypt(key, payload_nonce, payload_ct)
    else:
        payload = info["payload_data"]
        if len(payload) < payload_len:
            raise StegoEngineError("Payload truncated")
        payload = payload[:payload_len]
    return payload


def read_payload_asymmetric_from_bits(bits: List[int], private_key_path: str) -> bytes:
    data = bitstream.bits_to_bytes(bits)
    info = bitstream.unpack_public_stream(data)
    private_key = load_private_key_pem(private_key_path)
    session_key = rsa_decrypt_key(private_key, info["ek"])
    aesgcm = AESGCM(session_key)
    plaintext = aesgcm.decrypt(info["aes_nonce"], info["aes_ct"], None)
    header_plain = plaintext[: header.HEADER_LEN]
    payload_len = header.validate_header(header_plain)
    payload = plaintext[header.HEADER_LEN : header.HEADER_LEN + payload_len]
    if len(payload) != payload_len:
        raise StegoEngineError("Payload length mismatch")
    return payload
