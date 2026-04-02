"""
Record mouse click coordinates to stdout. Run: python setup.py
"""

from __future__ import annotations

from pynput import keyboard, mouse

anvil_coord_map = {
  # The top left and bottom right corners of the anvil box
  # These are to calculate the rest of the coordinates
  "tl": (0, 0),
  "br": (0, 0),
  "width": 0,
  "height": 0,

  # The offsets for the anvil
  "plans": (0, 0),
  "weld": (0, 0),
  "input1": (0, 0),
  "input2": (0, 0),
  "L": (0, 0),
  "M": (0, 0),
  "D": (0, 0),
  "P": (0, 0),
  "G": (0, 0),
  "Y": (0, 0),
  "O": (0, 0),
  "R": (0, 0),
  
  # The offsets for inventory slots
  "i1": (0, 0),
  "i2": (0, 0),
  "i3": (0, 0),
  "i4": (0, 0),
  "i5": (0, 0),
  "i6": (0, 0),
  "i7": (0, 0),
  "i8": (0, 0),
  "i9": (0, 0),
  "i10": (0, 0),
  "i11": (0, 0),
  "i12": (0, 0),
  "i13": (0, 0),
  "i14": (0, 0),
  "i15": (0, 0),
  "i16": (0, 0),
  "i17": (0, 0),
  "i18": (0, 0),
  "i19": (0, 0),
  "i20": (0, 0),
  "i21": (0, 0),
  "i22": (0, 0),
  "i23": (0, 0),
  "i24": (0, 0),
  "i25": (0, 0),
  "i26": (0, 0),
  "i27": (0, 0),

  # The offsets for the hotbar slots
  "h1": (0, 0),
  "h2": (0, 0),
  "h3": (0, 0),
  "h4": (0, 0),
  "h5": (0, 0),
  "h6": (0, 0),
  "h7": (0, 0),
  "h8": (0, 0),
  "h9": (0, 0),
}

recipe_coord_map = {
  # The top left and bottom right corners of the recipe box
  # These are to calculate the rest of the coordinates
  "tl": (0, 0),
  "br": (0, 0),
  "width": 0,
  "height": 0,

  # The offsets for the recipe box
  "rlb": (0, 0), # Left button
  "rrb": (0, 0), # Right button
  "r1": (0, 0),
  "r2": (0, 0),
  "r3": (0, 0),
  "r4": (0, 0),
  "r5": (0, 0),
  "r6": (0, 0),
  "r7": (0, 0),
  "r8": (0, 0),
  "r9": (0, 0),
  "r10": (0, 0),
  "r11": (0, 0),
  "r12": (0, 0),
  "r13": (0, 0),
  "r14": (0, 0),
  "r15": (0, 0),
  "r16": (0, 0),
  "r17": (0, 0),
  "r18": (0, 0),
}

def set_coord(coord_map, coord_name, x, y):
  if coord_name in ["tl", "br"]:
    coord_map[coord_name] = (x, y)
    return

  offset_x = (x - coord_map["tl"][0]) / coord_map["width"]
  offset_y = (y - coord_map["tl"][1]) / coord_map["height"]
  coord_map[coord_name] = (offset_x, offset_y)
  return


def main() -> None:
  print("Recording clicks (on press). Press Esc to stop.", flush=True)

  def on_click(x: float, y: float, button: mouse.Button, pressed: bool) -> None:
    if pressed:
      print(f"{int(round(x))}\t{int(round(y))}\t{button}", flush=True)

  def on_release(key: keyboard.Key | keyboard.KeyCode) -> bool | None:
    if key == keyboard.Key.esc:
      mouse_listener.stop()
      return False
    return None

  mouse_listener = mouse.Listener(on_click=on_click)
  mouse_listener.start()
  try:
    with keyboard.Listener(on_release=on_release) as kbd_listener:
      kbd_listener.join()
  finally:
    mouse_listener.stop()


if __name__ == "__main__":
  main()
