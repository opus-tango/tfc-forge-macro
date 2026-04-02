"""
Interactive coordinate calibration for TFC forge macro.

Run from a terminal: python setup.py

Flow:
  1. Anvil GUI: click top-left, then bottom-right of the bounding box (defines tl, br, width, height).
  2. With -f/--full: click only the first main inventory slot (i1); i2–i27 and h1–h9 are filled from grid steps (see SLOT_STEP_X / INV_ROW_STEP_Y below).
  3. Recipe GUI: same top-left / bottom-right for the recipe panel.
  4. With -f/--full: click the first recipe slot (r1); r2–r18 are filled from grid steps; scroll buttons rlb/rrb are still clicked manually.
  5. Writes coords.json. With -f/--full, every named offset is recorded; otherwise only anvil and recipe GUI rectangles (other offsets stay 0).

Press Esc to abort at any time.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path
from queue import Queue
from typing import Any

from pynput import keyboard, mouse

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "coords.json"

# Normalized grid steps (fraction of GUI width / height). One row = 9 slots left-to-right;
# inventory is 4 rows (i1–i27 then hotbar h1–h9); recipe panel is 2 rows (r1–r18).
SLOT_STEP_X = 1.0 / 9.5
INV_ROW_STEP_Y = 1.0 / 11.0
RECIPE_ROW_STEP_Y = 1.0 / 8.35


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


# Normalized offsets relative to anvil GUI box (after tl/br/width/height are set).
ANVIL_UI_OFFSET_KEYS = [
    "weld",
    "input1",
    "input2",
    "L",
    "M",
    "D",
    "P",
    "G",
    "Y",
    "O",
    "R",
]
RECIPE_SCROLL_KEYS = ["rrb","rlb"]


def fill_anvil_inventory_from_i1(coord_map: dict[str, Any]) -> None:
    """Fill i1–i27 and h1–h9 from i1's normalized offset and SLOT_STEP_X / INV_ROW_STEP_Y."""
    ox0, oy0 = coord_map["i1"]
    for k in range(1, 28):
        idx = k - 1
        row, col = idx // 9, idx % 9
        coord_map[f"i{k}"] = (ox0 + col * SLOT_STEP_X, oy0 + row * INV_ROW_STEP_Y)
    for k in range(1, 10):
        col = k - 1
        coord_map[f"h{k}"] = (ox0 + col * SLOT_STEP_X, oy0 + 3 * INV_ROW_STEP_Y)


def fill_recipe_slots_from_r1(coord_map: dict[str, Any]) -> None:
    """Fill r1–r18 from r1's normalized offset and SLOT_STEP_X / RECIPE_ROW_STEP_Y."""
    ox0, oy0 = coord_map["r1"]
    for k in range(1, 19):
        idx = k - 1
        row, col = idx // 9, idx % 9
        coord_map[f"r{k}"] = (ox0 + col * SLOT_STEP_X, oy0 + row * RECIPE_ROW_STEP_Y)

_ANVIL_UI_LABELS: dict[str, str] = {
    "weld": "weld button",
    "input1": "first anvil input slot",
    "input2": "second anvil input slot",
    "L": "Light Hit",
    "M": "Medium Hit",
    "D": "Heavy Hit",
    "P": "Draw",
    "G": "Punch",
    "Y": "Bend",
    "O": "Upset",
    "R": "Shrink",
}


def _recipe_offset_label(key: str) -> str:
    if key == "rlb":
        return "recipe panel left scroll / page button"
    if key == "rrb":
        return "recipe panel right scroll / page button"
    return f"recipe slot {key}"


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


def run_setup(output_path: Path, full: bool) -> None:
    anvil = _empty_anvil_map()
    recipe = _empty_recipe_map()
    session = _ClickSession()

    mouse_listener = mouse.Listener(on_click=session.on_click)
    mouse_listener.start()
    try:
        with keyboard.Listener(on_release=session.on_release) as kbd_listener:
            intro_anvil = (
                "=== Anvil GUI ===\n"
                "Open the anvil / forge screen. You will define the full GUI outer rectangle"
                + (" then every clickable offset.\n" if full else ".\n")
            )
            print(intro_anvil, flush=True)
            tl_pt = session.wait_click("1/2 Click the TOP-LEFT corner of the anvil GUI (outer box).")
            br_pt = session.wait_click("2/2 Click the BOTTOM-RIGHT corner of the same GUI box.")
            apply_top_left_bottom_right(anvil, tl_pt, br_pt)
            print(
                f"   Box: tl={anvil['tl']} br={anvil['br']} size={anvil['width']}x{anvil['height']}\n",
                flush=True,
            )

            if full:
                ui_total = len(ANVIL_UI_OFFSET_KEYS)
                for n, key in enumerate(ANVIL_UI_OFFSET_KEYS, start=1):
                    label = _ANVIL_UI_LABELS.get(key, key)
                    xy = session.wait_click(
                        f"Anvil UI {n}/{ui_total} ({key}): click the center of the {label}."
                    )
                    set_offset(anvil, key, xy[0], xy[1])

                xy_i1 = session.wait_click(
                    "Inventory: click the center of slot i1 (top-left of the 9×3 main grid). "
                    "i2–i27 and h1–h9 are filled using horizontal step 1/9.5 and vertical 1/11 per row (4 rows total including hotbar)."
                )
                set_offset(anvil, "i1", xy_i1[0], xy_i1[1])
                fill_anvil_inventory_from_i1(anvil)
                
                session.wait_click("Pickup your ingot to move to the second input slot.")
                session.wait_click("Move the ingot to the second input slot.")

                plansclick = session.wait_click("Click the PLAN button of the anvil GUI box.")
                set_offset(anvil, "plans", plansclick[0], plansclick[1])

            print(
                "\n=== Recipe GUI ===\n"
                "Open the recipe selector panel (or the screen where it appears). Same corner convention.\n",
                flush=True,
            )
            if not full:
                session.wait_click("Click the OPEN button of the recipe GUI box.")
            rtl = session.wait_click("1/2 Click the TOP-LEFT corner of the recipe GUI box.")
            rbr = session.wait_click("2/2 Click the BOTTOM-RIGHT corner of the recipe GUI box.")
            apply_top_left_bottom_right(recipe, rtl, rbr)
            print(
                f"   Box: tl={recipe['tl']} br={recipe['br']} size={recipe['width']}x{recipe['height']}\n",
                flush=True,
            )

            if full:
                for n, key in enumerate(RECIPE_SCROLL_KEYS, start=1):
                    xy = session.wait_click(
                        f"Recipe scroll {n}/{len(RECIPE_SCROLL_KEYS)} ({key}): "
                        f"click the center of the {_recipe_offset_label(key)}."
                    )
                    set_offset(recipe, key, xy[0], xy[1])
                xy_r1 = session.wait_click(
                    "Recipe: click the center of slot r1 (top-left of the recipe grid). "
                    "r2–r18 use horizontal step 1/9.5 and vertical 1/8.35 per row."
                )
                set_offset(recipe, "r1", xy_r1[0], xy_r1[1])
                fill_recipe_slots_from_r1(recipe)
                

            payload = {
                "anvil": coord_map_to_json_dict(anvil),
                "recipe": coord_map_to_json_dict(recipe),
            }
            output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote {output_path}", flush=True)
    finally:
        mouse_listener.stop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive coordinate calibration for TFC forge macro.",
    )
    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help=(
            "Record every offset: anvil UI (plans, weld, inputs, forge steps), i1 plus derived inventory/hotbar grid, "
            "and recipe UI (r1 plus derived r2–r18, then rlb/rrb). Default: only the anvil and recipe GUI rectangles."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to output coords.json (default: {DEFAULT_OUTPUT}).",
    )
    args = parser.parse_args()
    
    try:
        run_setup(args.output, args.full)
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
