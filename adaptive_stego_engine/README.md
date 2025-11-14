# Adaptive Steganography Engine v2.0.0

Adaptive Steganography Engine v2.0.0 is a production-ready Python 3.12 project that combines
texture-aware embedding, hardened cryptography, and a PyQt6 desktop application.

## Features

- **PNG-only workflow** with strict validation to avoid lossy formats.
- **Adaptive capacity planning** using Sobel gradients and local entropy analysis.
- **Multi-bit LSB embedder** with predictive noise control, deterministic pixel ordering, and block-level drift checks.
- **Optional hardened cryptography** using Argon2id, AES-GCM, or AES-CTR+HMAC with encrypted headers.
- **Comprehensive extractor** that reconstructs pixel ordering, capacities, and decrypts payloads when required.
- **Quality assurance** enforcing PSNR ≥ 48 dB and SSIM ≥ 0.985.
- **PyQt6 GUI** featuring embedding/extraction tabs, previews, encryption controls, and progress feedback.
- **CLI utilities** for automated embedding/extraction workflows.

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
│   ├── embed_tab.py
│   ├── extract_tab.py
│   ├── main_window.py
│   └── resources.py
├── util/
│   ├── bitstream.py
│   ├── crypto.py
│   ├── header.py
│   ├── image_io.py
│   ├── metrics.py
│   └── prng.py
└── (user-provided cover and output assets)
```

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Python Dependencies

- numpy
- pillow
- scipy
- cryptography
- argon2-cffi
- tqdm
- PyQt6

Create a `requirements.txt` containing the above packages if desired.

## Running the GUI

```bash
python -m adaptive_stego_engine.main gui
```

The GUI provides two tabs:

1. **Embed** – select a cover PNG, enter or load text, configure encryption, and embed.
2. **Extract** – select a stego PNG, optionally provide the password, and recover the message.

## Command Line Usage

Embed payload:

```bash
python -m adaptive_stego_engine.main embed cover.png stego.png --text "Secret" --seed myseed
```

Extract payload:

```bash
python -m adaptive_stego_engine.main extract stego.png --seed myseed
```

## Hardened Header Format

- Plain header: `"STEGO" + uint32_be(length)`
- Hardened mode encrypts the header with AES (GCM or CTR+HMAC) using an Argon2id-derived key.
- Salt is stored before the encrypted header. Payload ciphertext metadata (nonce/tag lengths) is serialized
  inside the adaptive bitstream.

## Quality Guarantees

Embedding is aborted if PSNR or SSIM fall below the required thresholds. Statistical drift monitoring prevents
suspicious 8×8 regions and enforces consistency with the cover histogram.

## Disclaimer

This project is provided for educational and defensive research purposes. Ensure compliance with all applicable
laws and regulations when applying steganography or cryptography.
