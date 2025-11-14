# Adaptive Steganography Engine v2.0.0

Adaptive Steganography Engine v2.0.0 is a production-grade Python 3.12 application that combines a hardened, texture-aware steganographic core with a desktop GUI built on PyQt6. The system operates exclusively on 24-bit PNG cover images, supports optional Argon2id/AES-based encryption, and enforces PSNR/SSIM quality thresholds during embedding to minimise detectability.

## Features

- **PNG-only cover enforcement** – rejects lossy formats to preserve LSB integrity.
- **Adaptive capacity planning** – Sobel gradient, local entropy, and drift controls determine per-pixel bit budgets (0–3 bits).
- **Predictive noise correction** – dynamically reduces capacity near smooth regions.
- **Deterministic PRNG ordering** – entropy-ranked pixels shuffled with a seed-derived PRNG for repeatable embedding/extraction.
- **Quality assurance** – PSNR ≥ 48 dB and SSIM ≥ 0.985 enforced after embedding.
- **Hardened headers** – plaintext header `STEGO + length` with optional full payload encryption (AES-GCM or AES-CTR + HMAC) using Argon2id-derived keys and per-payload salts.
- **GUI workflow** – intuitive tabs for embedding and extraction, live metrics, and support for direct text entry or `.txt` payloads.

## Project Structure

```
adaptive_stego_engine/
├── main.py
├── README.md
├── analyzer/
│   ├── gradient.py
│   ├── entropy.py
│   ├── texture_map.py
│   └── region_classifier.py
├── embedder/
│   ├── capacity.py
│   ├── drift_control.py
│   ├── embed_controller.py
│   ├── embedding.py
│   ├── noise_predictor.py
│   └── pixel_order.py
├── extractor/
│   ├── bit_reader.py
│   ├── extract_controller.py
│   └── extraction.py
├── gui/
│   ├── __init__.py
│   ├── assets/theme.qss
│   ├── embed_tab.py
│   ├── extract_tab.py
│   ├── main_window.py
│   └── resources.py
└── util/
    ├── bitstream.py
    ├── crypto.py
    ├── header.py
    ├── image_io.py
    ├── metrics.py
    └── prng.py
```

## Installation

1. **Create a Python 3.12 environment** (conda, venv, or your tool of choice).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Required packages:
   - `numpy`
   - `pillow`
   - `scipy`
   - `cryptography`
   - `argon2-cffi`
   - `tqdm`
   - `PyQt6`

3. (Optional) Install `opencv-python` if you want to experiment with alternative gradient implementations.

> **Note:** A `requirements.txt` file is not provided automatically; install the packages above manually or generate your own.

## Running the GUI

```bash
python -m adaptive_stego_engine.main
```

### Embedding Workflow

1. Load a 24-bit PNG cover image via **Select Cover PNG**.
2. Type or import UTF-8 text into the payload editor.
3. Enter a seed/password. This value drives the PRNG ordering and (when enabled) the Argon2id key derivation for encryption.
4. Optionally enable **AES Encryption** and choose either **AES-GCM** or **AES-CTR + HMAC**.
5. Click **Run Adaptive Embed** to embed the payload. PSNR/SSIM metrics appear if successful.
6. Save the generated stego PNG.

### Extraction Workflow

1. Load the stego PNG via **Select Stego PNG**.
2. Enter the same seed/password used during embedding.
3. If the payload was encrypted, tick **Payload is encrypted** before extraction.
4. Click **Extract** to recover the payload, then optionally export it to a `.txt` file.

## Core Algorithms

- **Texture analysis**: `analyzer/gradient.py` and `analyzer/entropy.py` produce gradient magnitudes and 5×5 local entropy scores. `texture_map.surface_map` combines them into a surface score driving region classification.
- **Capacity planning**: `embedder/capacity.py` derives per-pixel bit budgets, corrected by `noise_predictor.predictor_penalty` and `drift_control.safe_capacity_mask` (8×8 statistical checks).
- **Embedding**: `embedder/embed_controller.py` orders pixels by entropy, shuffles with a seed-driven PRNG, embeds multi-bit payloads, and validates PSNR/SSIM thresholds using `util.metrics`.
- **Extraction**: `extractor/extraction.py` mirrors the analysis pipeline to read multi-bit payloads, while `extractor/extract_controller.py` parses headers, validates magic constants, and optionally decrypts ciphertext with Argon2id-derived AES keys.

## Cryptography Details

- **Header format**: `MAGIC ("STEGO") + payload length (uint32 big-endian)`.
- **Hardened mode**: Generates a 16-byte random salt per payload, derives a 256-bit key with Argon2id, and encrypts header + payload using AES-GCM or AES-CTR + HMAC-SHA256. Salts, nonces, ciphertext, and authentication tags are serialized compactly before embedding.
- **Validation**: Extraction re-derives keys, authenticates the ciphertext, and verifies the decrypted header magic before returning payload bytes.

## CLI/Automation

While the GUI is the primary interface, the embedding/extraction controllers can be imported directly in Python for headless automation:

```python
from adaptive_stego_engine.embedder.embed_controller import AdaptiveEmbedder
from adaptive_stego_engine.extractor.extract_controller import AdaptiveExtractor

embedder = AdaptiveEmbedder(seed="secret-seed", encrypt=True, password="secret-seed", mode="AES-GCM")
result = embedder.embed(cover_array, payload_bytes)

extractor = AdaptiveExtractor(seed="secret-seed", password="secret-seed")
payload = extractor.extract(stego_array).payload
```

Ensure arrays are `numpy.uint8` RGB images loaded via `util.image_io.load_png` to maintain expected pre-processing.

## License

This project is provided as-is for educational and research purposes. Review and adjust cryptographic policies before deploying in production environments subject to local regulations.
