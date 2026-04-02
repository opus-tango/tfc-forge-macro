"""
Interactive coordinate calibration for TFC forge macro.

Run from a terminal: python setup.py

Flow:
  1. Anvil GUI: click top-left, then bottom-right of the bounding box (defines tl, br, width, height).
  2. Click the center of each main inventory slot (i1–i27) and hotbar slot (h1–h9).
  3. Recipe GUI: same top-left / bottom-right for the recipe panel.
  4. Writes coords.json with full anvil and recipe maps (recipe button offsets stay 0 until you edit or extend this script).

Press Esc to abort at any time.
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from queue import Queue
from typing import Any

from pynput import keyboard, mouse

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "coords.json"


def _empty_anvil_map() -> dict[str, Any]:
    m: dict[str, Any] = {
        "tl": (0, 0),
        "br": (0, 0),
        "width": 0,
        "height": 0,
        "plans": (0.0, 0.0),
        "weld": (0.0, 0.0),
        "input1": (0.0, 0.0),
        "input2": (0.0, 0.0),
        "L": (0.0, 0.0),
        "M": (0.0, 0.0),
        "D": (0.0, 0.0),
        "P": (0.0, 0.0),
        "G": (0.0, 0.0),
        "Y": (0.0, 0.0),
        "O": (0.0, 0.0),
        "R": (0.0, 0.0),
    }
    for i in range(1, 28):
        m[f"i{i}"] = (0.0, 0.0)
    for i in range(1, 10):
        m[f"h{i}"] = (0.0, 0.0)
    return m


def _empty_recipe_map() -> dict[str, Any]:
    m: dict[str, Any] = {
        "tl": (0, 0),
        "br": (0, 0),
        "width": 0,
        "height": 0,
        "rlb": (0.0, 0.0),
        "rrb": (0.0, 0.0),
    }
    for i in range(1, 19):
        m[f"r{i}"] = (0.0, 0.0)
    return m


ANVIL_INVENTORY_KEYS = [f"i{i}" for i in range(1, 28)] + [f"h{i}" for i in range(1, 10)]


def apply_top_left_bottom_right(
    coord_map: dict[str, Any], tl_corner: tuple[int, int], br_corner: tuple[int, int]
) -> None:
    """Set tl, br, width, height from top-left and bottom-right corners."""
    if br_corner[0] <= tl_corner[0] or br_corner[1] <= tl_corner[1]:
        raise ValueError(
            f"Invalid box: top-left {tl_corner}, bottom-right {br_corner}. "
            "Bottom-right should be farther right (larger x) and lower down (larger y) than top-left."
        )
    coord_map["tl"] = (tl_corner[0], tl_corner[1])
    coord_map["br"] = (br_corner[0], br_corner[1])
    coord_map["width"] = int(br_corner[0] - tl_corner[0])
    coord_map["height"] = int(br_corner[1] - tl_corner[1])


def set_offset(coord_map: dict[str, Any], coord_name: str, x: int, y: int) -> None:
    """Store normalized offset relative to tl and box size (matches main.get_coord)."""
    if coord_name in ("tl", "br"):
        coord_map[coord_name] = (x, y)
        return
    w = coord_map["width"]
    h = coord_map["height"]
    if w <= 0 or h <= 0:
        raise ValueError("width and height must be set and positive before recording offsets")
    tl = coord_map["tl"]
    ox = (x - tl[0]) / w
    oy = (y - tl[1]) / h
    coord_map[coord_name] = (ox, oy)


def _serialize_value(v: Any) -> Any:
    if isinstance(v, tuple):
        return [_serialize_value(x) for x in v]
    if isinstance(v, float):
        return round(v, 8)
    return v


def coord_map_to_json_dict(coord_map: dict[str, Any]) -> dict[str, Any]:
    return {k: _serialize_value(v) for k, v in coord_map.items()}


class _ClickSession:
    def __init__(self) -> None:
        self._q: Queue[tuple[int, int] | None] = Queue()
        self._abort = threading.Event()

    def on_click(self, x: float, y: float, button: mouse.Button, pressed: bool) -> None:
        if not pressed or button != mouse.Button.left or self._abort.is_set():
            return
        self._q.put((int(round(x)), int(round(y))))

    def on_release(self, key: keyboard.Key | keyboard.KeyCode) -> bool | None:
        if key == keyboard.Key.esc:
            self._abort.set()
            self._q.put(None)
            return False
        return None

    def wait_click(self, prompt: str) -> tuple[int, int]:
        print(prompt, flush=True)
        item = self._q.get()
        if item is None:
            raise SystemExit("Aborted (Esc).")
        return item


def run_setup(output_path: Path) -> None:
    anvil = _empty_anvil_map()
    recipe = _empty_recipe_map()
    session = _ClickSession()

    mouse_listener = mouse.Listener(on_click=session.on_click)
    mouse_listener.start()
    try:
        with keyboard.Listener(on_release=session.on_release) as kbd_listener:
            print(
                "=== Anvil GUI ===\n"
                "Open the anvil / forge screen. You will define the full GUI rectangle, then inventory slots.\n",
                flush=True,
            )
            tl_pt = session.wait_click("1/2 Click the TOP-LEFT corner of the anvil GUI (outer box).")
            br_pt = session.wait_click("2/2 Click the BOTTOM-RIGHT corner of the same GUI box.")
            apply_top_left_bottom_right(anvil, tl_pt, br_pt)
            print(
                f"   Box: tl={anvil['tl']} br={anvil['br']} size={anvil['width']}x{anvil['height']}\n",
                flush=True,
            )

            total = len(ANVIL_INVENTORY_KEYS)
            for n, key in enumerate(ANVIL_INVENTORY_KEYS, start=1):
                xy = session.wait_click(
                    f"Inventory {n}/{total}: click the center of slot {key} "
                    "(i1–i27: main inventory, usually 9×3 left-to-right, top-to-bottom; then h1–h9: hotbar)."
                )
                set_offset(anvil, key, xy[0], xy[1])

            print(
                "\n=== Recipe GUI ===\n"
                "Open the recipe selector panel (or the screen where it appears). Same corner convention.\n",
                flush=True,
            )
            rtl = session.wait_click("1/2 Click the TOP-LEFT corner of the recipe GUI box.")
            rbr = session.wait_click("2/2 Click the BOTTOM-RIGHT corner of the recipe GUI box.")
            apply_top_left_bottom_right(recipe, rtl, rbr)
            print(
                f"   Box: tl={recipe['tl']} br={recipe['br']} size={recipe['width']}x{recipe['height']}\n",
                flush=True,
            )
            print(
                "Recipe controls (rlb, rrb, r1–r18) are left at [0,0] in the file; calibrate them later if needed.\n",
                flush=True,
            )

            payload = {
                "anvil": coord_map_to_json_dict(anvil),
                "recipe": coord_map_to_json_dict(recipe),
            }
            output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote {output_path}", flush=True)
    finally:
        mouse_listener.stop()


def main() -> None:
    out = DEFAULT_OUTPUT
    if len(sys.argv) > 1:
        out = Path(sys.argv[1]).expanduser().resolve()
    try:
        run_setup(out)
    except SystemExit as e:
        print(str(e), flush=True)
        raise
    except ValueError as e:
        print(f"Error: {e}", flush=True)
        sys.exit(1)


# Backwards-compatible names for any imports
anvil_coord_map = _empty_anvil_map()
recipe_coord_map = _empty_recipe_map()
set_coord = set_offset

if __name__ == "__main__":
    main()
