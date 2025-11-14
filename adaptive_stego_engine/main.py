"""Entry point for Adaptive Steganography Engine v2.0.0."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication

from .embedder import embed_controller
from .extractor import extract_controller
from .gui.main_window import MainWindow
from .util import header as header_util, image_io


def _load_payload(text: Optional[str], file_path: Optional[Path]) -> bytes:
    if file_path:
        return file_path.read_text(encoding="utf-8").encode("utf-8")
    if text is not None:
        return text.encode("utf-8")
    raise ValueError("No payload provided")


def run_cli(args: argparse.Namespace) -> None:
    cover = image_io.load_png(args.cover)
    payload = _load_payload(args.text, Path(args.payload) if args.payload else None)
    password = args.password if args.encrypt else None
    mode = args.mode
    result = embed_controller.embed(cover, payload, seed=args.seed, password=password, mode=mode)
    image_io.save_png(args.output, result.stego_image)
    print(f"Embedding complete. PSNR={result.psnr:.2f} dB SSIM={result.ssim:.4f}")


def run_extract(args: argparse.Namespace) -> None:
    stego = image_io.load_png(args.stego)
    password = args.password if args.encrypted else None
    result = extract_controller.extract(stego, seed=args.seed, password=password)
    payload_text = result.payload.decode("utf-8")
    if args.output:
        Path(args.output).write_text(payload_text, encoding="utf-8")
    else:
        print(payload_text)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Adaptive Steganography Engine")
    subparsers = parser.add_subparsers(dest="command")

    gui_parser = subparsers.add_parser("gui", help="Launch GUI")

    embed_parser = subparsers.add_parser("embed", help="Embed payload via CLI")
    embed_parser.add_argument("cover", help="Cover PNG path")
    embed_parser.add_argument("output", help="Output stego PNG path")
    embed_parser.add_argument("--seed", default="default-seed")
    embed_parser.add_argument("--text", help="Plaintext to embed")
    embed_parser.add_argument("--payload", help="Path to .txt payload file")
    embed_parser.add_argument("--encrypt", action="store_true")
    embed_parser.add_argument("--password", help="Encryption password")
    embed_parser.add_argument("--mode", choices=[header_util.MODE_GCM, header_util.MODE_CTR_HMAC], default=header_util.MODE_GCM)

    extract_parser = subparsers.add_parser("extract", help="Extract payload via CLI")
    extract_parser.add_argument("stego", help="Stego PNG path")
    extract_parser.add_argument("--seed", default="default-seed")
    extract_parser.add_argument("--encrypted", action="store_true")
    extract_parser.add_argument("--password")
    extract_parser.add_argument("--output", help="Output text file path")

    args = parser.parse_args(argv)

    if args.command == "gui" or args.command is None:
        app = QApplication(sys.argv)
        window = MainWindow(app)
        window.show()
        return app.exec()
    if args.command == "embed":
        run_cli(args)
        return 0
    if args.command == "extract":
        run_extract(args)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
