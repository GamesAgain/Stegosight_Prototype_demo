# Adaptive Steganography Engine v3.0.0

Adaptive Steganography Engine v3.0.0 delivers a hardened multi-mode hiding pipeline with an asynchronous PyQt6 desktop interface.  It performs texture-aware multi-bit LSB embedding for PNG RGB images, supports password-based and public-key-based payload protection, and enforces strict visual quality thresholds.

## Features

- **Adaptive embedding** – gradient, entropy, and surface analysis determine safe per-pixel capacity, enforce predictive noise correction, and enable block-level drift rollback.
- **Symmetric (Password) mode** – passwords are converted to AES-256 keys via PBKDF2.  Headers are always encrypted with AES-GCM, and payloads can optionally be AES-GCM protected with a GUI toggle.
- **Public-Key mode** – RSA-OAEP encrypts a random AES session key which protects both header and payload (hybrid cryptosystem).  The GUI can generate, load, and manage RSA PEM key pairs without external tooling.
- **Async PyQt6 GUI** – embedding and extraction run inside worker threads so the window stays responsive.  Progress bars and status labels describe each pipeline phase.  Tabs provide embedding, extraction, and key-management flows with previews and save dialogs.
- **Quality enforcement** – PSNR ≥ 48 dB, SSIM ≥ 0.985, and histogram drift ≤ 0.02 are required; otherwise embedding is aborted with a clear error.

## Using the Application

1. Install Python 3.12 plus the dependencies listed below.
2. Launch the GUI:

```bash
cd adaptive_stego_engine
python main.py
```

3. In the **Embed** tab:
   - Load a 24-bit RGB PNG cover image.
   - Enter or import UTF-8 text.
   - Choose *Password* mode (enter password, optional AES payload encryption) or *Public Key* mode (browse for a public PEM).  Pixel ordering is tied to the password or public-key fingerprint.
   - Start embedding.  Review metrics, then save the stego PNG.

4. In the **Extract** tab:
   - Load the stego PNG and choose the correct mode.
   - Provide the original password or the matching private PEM.
   - Run extraction; the payload appears in the text area and can be saved to `.txt`.

5. In the **Keys** tab:
   - Generate RSA key pairs (2048/3072-bit) and save PEM files.
   - Load existing keys to populate the Embed/Extract tabs automatically.

## Architecture Overview

- **Analyzer** – produces grayscale, gradient, entropy, and surface maps to classify pixels into smooth/texture/edge regions.
- **Embedder** – sorts pixels by entropy, shuffles them via seeded PRNG, and embeds bits with predictive noise limits and 8×8 drift control.  Mode-specific bitstreams encapsulate encrypted headers/payloads.
- **Extractor** – rebuilds the same pixel order, recovers bits, parses the mode-tagged stream, and decrypts payloads via PBKDF2/AES-GCM or RSA-OAEP/AES-GCM.
- **Utilities** – strict PNG I/O, cryptography helpers, stream/headers, quality metrics, and deterministic PRNG.

## Requirements

- Python 3.12
- numpy
- pillow
- scipy
- cryptography
- PyQt6
- tqdm (optional future CLI progress)
- (Optional) opencv-python – not required but compatible.

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Notes

- Only 24-bit RGB PNG covers are accepted; any other format triggers a `StegoEngineError`.
- Payload capacity depends on local texture.  Large, smooth images may not meet payload size or quality thresholds.
- Headers never appear in plaintext inside the LSB stream; even legacy password mode encrypts header metadata with AES-GCM.
