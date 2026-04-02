"""
Record mouse click coordinates to stdout. Run: python setup.py
"""

from __future__ import annotations

from pynput import keyboard, mouse


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
