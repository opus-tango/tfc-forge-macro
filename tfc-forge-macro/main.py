from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Button, Controller as MouseController

DEFAULT_COORDS_PATH = Path(__file__).resolve().parent / "coords.json"

# Timing tuned for games that poll input each frame: move must settle before click,
# and a short pause after mouse-up helps the last click flush before the process exits.
MOVE_SETTLE_SEC = 0.02
CLICK_HOLD_SEC = 0.03
POST_CLICK_SEC = 0.03

DEFAULT_TEST_SLOTS = ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8", "i9", "i1"]


def get_coord(coord_map: dict[str, Any], coord_name: str) -> tuple[float, float]:
    """Pixel position for a named slot. tl/br are absolute pixels; others use normalized offsets."""
    if coord_name in ("tl", "br"):
        v = coord_map[coord_name]
        return (float(v[0]), float(v[1]))
    offsets = coord_map[coord_name]
    tl = coord_map["tl"]
    width = coord_map["width"]
    height = coord_map["height"]
    x = tl[0] + (offsets[0] * width)
    y = tl[1] + (offsets[1] * height)
    return (x, y)


def load_coords(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if "anvil" not in data or "recipe" not in data:
        raise ValueError("coords.json must contain 'anvil' and 'recipe' keys")
    return data


def resolve_coord_map(payload: dict[str, Any], name: str) -> dict[str, Any]:
    """Return the anvil or recipe sub-map that contains this slot name."""
    if name in ("width", "height"):
        raise ValueError(f"{name!r} is metadata, not a clickable slot.")
    for section in ("anvil", "recipe"):
        m = payload[section]
        if name not in m:
            continue
        val = m[name]
        if isinstance(val, (int, float)):
            raise ValueError(f"{name!r} in {section!r} is not a coordinate pair.")
        return m
    raise KeyError(f"Unknown slot {name!r} (not in anvil or recipe).")


def parse_slot_token(token: str) -> tuple[str, bool]:
    """Underscore prefix means hold Shift for that click (_i2 -> i2 with shift)."""
    if token.startswith("_"):
        return token[1:], True
    return token, False


def run_sequence(
    payload: dict[str, Any],
    slots: list[str],
    delay_ms: float,
    move_settle_sec: float = MOVE_SETTLE_SEC,
    click_hold_sec: float = CLICK_HOLD_SEC,
    post_click_sec: float = POST_CLICK_SEC,
) -> None:
    mouse = MouseController()
    keyboard = KeyboardController()

    for i, token in enumerate(slots):
        name, use_shift = parse_slot_token(token)
        if not name:
            raise ValueError(f"Empty slot name in token {token!r}")

        coord_map = resolve_coord_map(payload, name)
        x, y = get_coord(coord_map, name)
        xi, yi = int(round(x)), int(round(y))

        mouse.position = (xi, yi)
        time.sleep(move_settle_sec)

        if use_shift:
            keyboard.press(Key.shift)
            time.sleep(move_settle_sec)

        try:
            mouse.press(Button.left)
            time.sleep(click_hold_sec)
            mouse.release(Button.left)
        finally:
            if use_shift:
                keyboard.release(Key.shift)

        time.sleep(post_click_sec)

        if i + 1 < len(slots) and delay_ms > 0:
            time.sleep(delay_ms / 1000.0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Move the mouse to slots from coords.json and left-click.",
    )
    parser.add_argument(
        "-s",
        "--start-delay",
        type=int,
        default=700,
        metavar="MS",
        help="Milliseconds to wait before starting the sequence (default: 1000).",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=int,
        default=200,
        metavar="MS",
        help="Milliseconds to wait after each click before the next (default: 200).",
    )
    parser.add_argument(
        "--move-settle-ms",
        type=float,
        default=MOVE_SETTLE_SEC * 1000,
        metavar="MS",
        help=(
            "Milliseconds to wait after moving the cursor before mouse down "
            f"(default: {MOVE_SETTLE_SEC * 1000:.0f}). Helps clicks register on the new position."
        ),
    )
    parser.add_argument(
        "--post-click-ms",
        type=float,
        default=POST_CLICK_SEC * 1000,
        metavar="MS",
        help=(
            "Milliseconds to wait after each mouse up (including the last) "
            f"(default: {POST_CLICK_SEC * 1000:.0f}). Helps the final click flush before exit."
        ),
    )
    parser.add_argument(
        "--click-hold-ms",
        type=float,
        default=CLICK_HOLD_SEC * 1000,
        metavar="MS",
        help=f"Milliseconds to hold the mouse button down (default: {CLICK_HOLD_SEC * 1000:.0f}).",
    )
    parser.add_argument(
        "-c",
        "--coords-file",
        type=Path,
        default=None,
        help=f"Path to coords.json (default: {DEFAULT_COORDS_PATH}).",
    )
    parser.add_argument(
        "slots",
        nargs="*",
        metavar="SLOT",
        help="Slot names from coords.json, e.g. M D P G i9 h6. Use _NAME for shift-click.",
    )
    args = parser.parse_args()
    path = args.coords_file.expanduser().resolve() if args.coords_file else DEFAULT_COORDS_PATH

    if not path.is_file():
        print(f"Missing coords file: {path}", file=sys.stderr)
        sys.exit(1)

    slots = args.slots if args.slots else DEFAULT_TEST_SLOTS

    time.sleep(args.start_delay / 1000)

    try:
        payload = load_coords(path)
        run_sequence(
            payload,
            slots,
            args.delay,
            move_settle_sec=args.move_settle_ms / 1000.0,
            click_hold_sec=args.click_hold_ms / 1000.0,
            post_click_sec=args.post_click_ms / 1000.0,
        )
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
