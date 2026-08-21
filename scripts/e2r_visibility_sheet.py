#!/usr/bin/env python3
"""Build contact-sheet and selected-vs-present diff artifacts for E2R dumps."""

from __future__ import annotations

import argparse
from pathlib import Path


def _read_token(data: bytes, offset: int) -> tuple[bytes, int]:
    while offset < len(data) and data[offset] in b" \t\r\n":
        offset += 1
    if offset < len(data) and data[offset] == ord("#"):
        while offset < len(data) and data[offset] not in b"\r\n":
            offset += 1
        return _read_token(data, offset)
    start = offset
    while offset < len(data) and data[offset] not in b" \t\r\n":
        offset += 1
    return data[start:offset], offset


def read_netpbm(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    magic, offset = _read_token(data, 0)
    width_token, offset = _read_token(data, offset)
    height_token, offset = _read_token(data, offset)
    max_token, offset = _read_token(data, offset)
    if magic not in (b"P5", b"P6") or max_token != b"255":
        raise ValueError(f"{path} is not an 8-bit PGM/PPM file")
    if offset < len(data) and data[offset] in b" \t\r\n":
        offset += 1
    width = int(width_token)
    height = int(height_token)
    pixels = data[offset:]
    if magic == b"P6":
        expected = width * height * 3
        if len(pixels) < expected:
            raise ValueError(f"{path} is truncated")
        return width, height, pixels[:expected]
    expected = width * height
    if len(pixels) < expected:
        raise ValueError(f"{path} is truncated")
    rgb = bytearray(width * height * 3)
    for i, value in enumerate(pixels[:expected]):
        rgb[i * 3:i * 3 + 3] = bytes((value, value, value))
    return width, height, bytes(rgb)


def write_ppm(path: Path, width: int, height: int, pixels: bytes) -> None:
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + pixels)


def blit(dst: bytearray, dst_width: int, src: bytes, src_width: int, src_height: int,
         x0: int, y0: int) -> None:
    for y in range(src_height):
        src_start = y * src_width * 3
        src_end = src_start + src_width * 3
        dst_start = ((y0 + y) * dst_width + x0) * 3
        dst[dst_start:dst_start + src_width * 3] = src[src_start:src_end]


def parse_selected_surface(state_path: Path) -> int:
    try:
        text = state_path.read_text(encoding="ascii", errors="replace")
    except FileNotFoundError:
        return 3
    for token in text.replace("\n", " ").split():
        if token.startswith("selected_surface="):
            return int(token.split("=", 1)[1], 0)
    return 3


def make_contact_sheet(prefix: Path, output: Path) -> None:
    names = [
        "s0.ppm",
        "s1.ppm",
        "s2.ppm",
        "s3.ppm",
        "sdl-present.ppm",
        "sdl-window.ppm",
    ]
    images = []
    for name in names:
        path = Path(f"{prefix}-{name}")
        if path.exists():
            images.append(read_netpbm(path))
        else:
            images.append((1, 1, b"\0\0\0"))
    tile_width = max(width for width, _, _ in images)
    tile_height = max(height for _, height, _ in images)
    columns = 3
    rows = 2
    sheet = bytearray(tile_width * columns * tile_height * rows * 3)
    for index, (width, height, pixels) in enumerate(images):
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        blit(sheet, tile_width * columns, pixels, width, height, x, y)
    write_ppm(output, tile_width * columns, tile_height * rows, bytes(sheet))


def make_diff(prefix: Path, output: Path) -> bool:
    selected = parse_selected_surface(Path(f"{prefix}-state.txt"))
    selected_path = Path(f"{prefix}-s{selected}.ppm")
    present_path = Path(f"{prefix}-sdl-present.ppm")
    if not selected_path.exists() or not present_path.exists():
        return False
    sw, sh, sp = read_netpbm(selected_path)
    pw, ph, pp = read_netpbm(present_path)
    if (sw, sh) != (pw, ph):
        return False
    diff = bytearray(sw * sh * 3)
    for i in range(0, len(diff), 3):
        delta = max(abs(sp[i] - pp[i]), abs(sp[i + 1] - pp[i + 1]),
                    abs(sp[i + 2] - pp[i + 2]))
        if delta:
            diff[i:i + 3] = bytes((255, min(delta * 4, 255), min(delta * 4, 255)))
    write_ppm(output, sw, sh, bytes(diff))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prefix", type=Path)
    parser.add_argument("--contact", type=Path)
    parser.add_argument("--diff", type=Path)
    args = parser.parse_args()
    contact = args.contact or Path(f"{args.prefix}-contact.ppm")
    diff = args.diff or Path(f"{args.prefix}-selected-vs-present-diff.ppm")
    make_contact_sheet(args.prefix, contact)
    made_diff = make_diff(args.prefix, diff)
    print(f"wrote {contact}")
    if made_diff:
        print(f"wrote {diff}")
    else:
        print("skipped selected-vs-present diff")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
