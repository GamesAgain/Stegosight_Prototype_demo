# Adaptive Steganography Engine v2.0.0

Adaptive Steganography Engine v2.0.0 is a production-ready Python 3.12 project delivering a
state-of-the-art, texture-aware steganography workflow with optional AES-GCM encryption and a
full PyQt6 GUI. The system supports adaptive, capacity-optimised embedding in 24-bit PNG covers
and guarantees precise payload recovery through a deterministic reverse pipeline.

## Key Features

- **Cover compliance** – accepts only 24-bit PNG images and preserves original dimensions.
- **Payload support** – embeds UTF-8 text from direct input or `.txt` files.
- **WARPLAN STEG2 hardening** – plaintext header (`STEGO` + payload length) or fully encrypted
  header/payload bundle with PBKDF2-HMAC-SHA256 derived keys and AES-GCM.
- **Adaptive analysis** – Sobel gradients and local entropy build a composite surface score used to
  classify regions into Smooth, Texture, and Edge zones with tiered bit capacities.
- **Predictive noise correction** – neighbourhood-aware capacity reduction prevents artifacts in
  smooth areas.
- **Drift-aware planning** – statistical simulations on 8×8 blocks downgrade risky regions before
  embedding, ensuring PSNR ≥ 48 dB and SSIM ≥ 0.985.
- **Deterministic embedding order** – pixels sorted by entropy and shuffled with a seed-controlled
  PRNG ensure reproducible placement during extraction.
- **Quality metrics** – PSNR, SSIM, and histogram drift calculated after embedding.
- **Full reverse pipeline** – extraction recomputes the adaptive capacity map, rebuilds the PRNG
  ordering, decrypts headers/payloads when required, and outputs UTF-8 text.
- **Modern GUI** – dual-tab PyQt6 interface for embedding and extraction with live previews,
  encryption toggles, and save options.

## Project Layout

```
adaptive_stego_engine/
├── main.py
├── README.md
├── analyzer/
│   ├── entropy.py
│   ├── gradient.py
│   ├── region_classifier.py
│   └── texture_map.py
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
│   └── main_window.py
└── util/
    ├── bitstream.py
    ├── crypto.py
    ├── header.py
    ├── image_io.py
    ├── metrics.py
    └── prng.py
```

## Installation

Create a virtual environment (Python 3.12.0) and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the GUI

```bash
python -m adaptive_stego_engine.main
```

### Embedding Workflow

1. Open the **Embed** tab.
2. Select a 24-bit PNG cover (other formats are rejected).
3. Enter secret text or load a UTF-8 `.txt` file.
4. Provide a seed/password used for PRNG ordering and optional encryption.
5. Toggle **Enable AES Encryption** to encrypt both header and payload (salt and nonce stored
   before ciphertext as per WARPLAN requirements).
6. Click **Run Adaptive Embed**. Quality metrics (PSNR, SSIM) are displayed upon success.
7. Save the stego PNG once satisfied.

### Extraction Workflow

1. Switch to the **Extract** tab and load the stego PNG.
2. Provide the original seed/password.
3. Tick **Payload is encrypted** if AES-GCM was used during embedding.
4. Click **Extract Payload** to recover the UTF-8 message. Save to a text file if needed.

## Command-Line Integration

All heavy lifting resides in the controller modules:

- `adaptive_stego_engine.embedder.embed_controller.embed_payload`
- `adaptive_stego_engine.extractor.extract_controller.extract_payload`

These functions operate directly on `numpy.ndarray` RGB images, enabling easy scripting or test
automation outside of the GUI layer.

## Security Notes

- PBKDF2-HMAC-SHA256 with a randomly generated 16-byte salt derives AES-GCM keys.
- The hardened mode encrypts header and payload, storing the salt, nonce, and tag ahead of the
  ciphertext. Decryption validates the `STEGO` magic before releasing the payload.
- Extraction raises descriptive errors on incorrect passwords or tampered data.

## Quality Guarantees

Every embedding run enforces:

- PSNR ≥ 48 dB
- SSIM ≥ 0.985
- Histogram drift monitoring via adaptive block simulation prior to writing bits

If the payload cannot be embedded without violating these constraints, the process aborts with a
clear error message.

## License

This prototype is provided for research and educational purposes. Ensure compliance with local laws
and regulations when using steganography in your environment.
