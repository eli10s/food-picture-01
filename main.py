#!/usr/bin/env python3
"""food-picture-01 entry: copy the repo-held image to the output directory.

Standard library only. Deterministic: no network, no randomness, no
timestamps. The grader runs this in a container where /output exists;
outside that container MAKEFUN_OUTPUT_DIR stands in for /output.

The copy is verified, not assumed: the source is checked to exist, be
readable, be a real image of the expected size and dimensions, and the
written file is compared byte-for-byte with the source. Any failure
exits non-zero with a clear message instead of silently producing a
bad or missing output.
"""

import hashlib
import os
import shutil
import struct
import sys
from pathlib import Path

SOURCE_NAME = "entry.png"
DEFAULT_OUTPUT_DIR = "/output"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_SOURCE_BYTES = 1024 * 1024  # entry must stay under 1 MiB

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def fail(message: str) -> "SystemExit":
    """Exit non-zero with a clear, single-line error."""
    print(f"error: {message}", file=sys.stderr)
    return SystemExit(1)


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Width and height from a PNG IHDR chunk (13 bytes, big-endian)."""
    if len(data) < 24:
        raise ValueError("PNG file too short for an IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Width and height from the first JPEG frame (SOF) marker."""
    pos = 2  # skip the SOI marker
    while pos + 9 <= len(data):
        if data[pos] != 0xFF:
            raise ValueError("malformed JPEG: expected a marker")
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2  # standalone marker, no length field
            continue
        (length,) = struct.unpack(">H", data[pos + 2 : pos + 4])
        if length < 2 or pos + 2 + length > len(data):
            raise ValueError("malformed JPEG: bad segment length")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[pos + 5 : pos + 9])
            return width, height
        pos += 2 + length
    raise ValueError("JPEG file has no frame (SOF) marker")


def validate_source(source: Path) -> bytes:
    """Read the source image and check it is the expected image."""
    if not source.is_file():
        raise FileNotFoundError(f"source image not found: {source}")
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise OSError(f"source image not readable: {source} ({exc})") from exc
    if not data:
        raise ValueError(f"source image is empty: {source}")
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError(
            f"source image is {len(data)} bytes, over the "
            f"{MAX_SOURCE_BYTES}-byte limit: {source}"
        )
    if data.startswith(PNG_MAGIC):
        width, height = png_dimensions(data)
        fmt = "PNG"
    elif data.startswith(JPEG_MAGIC):
        width, height = jpeg_dimensions(data)
        fmt = "JPEG"
    else:
        raise ValueError(f"source image is not a PNG or JPEG file: {source}")
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise ValueError(
            f"source image is {width}x{height} {fmt}, expected "
            f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}: {source}"
        )
    return data


def main() -> None:
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR)
    try:
        data = validate_source(source)
    except (OSError, ValueError) as exc:
        raise fail(str(exc)) from exc

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise fail(f"cannot create output directory {out_dir} ({exc})") from exc
    destination = out_dir / SOURCE_NAME
    try:
        shutil.copyfile(source, destination)
    except OSError as exc:
        raise fail(f"cannot write {destination} ({exc})") from exc

    written = destination.read_bytes()
    if hashlib.sha256(written).digest() != hashlib.sha256(data).digest():
        raise fail(
            f"copy verification failed: {destination} differs from {source}"
        )


if __name__ == "__main__":
    main()
