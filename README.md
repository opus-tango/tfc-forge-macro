# TFC Forge Macro

`tfc-forge-macro` is a small desktop automation tool for `TerraFirmaCraft` forging.
It records the screen coordinates of the anvil and recipe UIs, then replays mouse clicks
against named slots and buttons so you can run repeatable forging sequences.

## Table of Contents

- [What It Does](#what-it-does)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Installation (details)](#installation-details)
- [Coordinate Setup](#coordinate-setup)
- [Writing macro scripts](#writing-macro-scripts)
- [Calculating the forge recipes](#calculating-the-forge-recipes)
- [Running the Macro](#running-the-macro)
- [Running the macro through Macro Deck](#running-the-macro-through-macro-deck)
- [Shift-Click Support](#shift-click-support)
- [Using a Sequence File](#using-a-sequence-file)
- [Command Reference](#command-reference)
- [How `coords.json` Works](#how-coordsjson-works)
- [Safety and Usage Notes](#safety-and-usage-notes)
- [Troubleshooting](#troubleshooting)
- [Recommended Workflow](#recommended-workflow)
- [TODO](#todo)

## What It Does

The macro works by:

1. Recording the outer rectangle of the anvil and recipe boxes.
2. Storing button and slot positions as normalized offsets inside those rectangles.
3. Moving the mouse to named targets such as `L`, `M`, `D`, `R`, `i1`, or `r1`.
4. Left-clicking each target in order, with configurable timing between clicks.

Because the coordinates are normalized, the same `coords.json` can usually survive small
position changes as long as the UI layout stays consistent. If your resolution or UI scale
changes, you can refresh the saved rectangles without fully recalibrating everything.

## Requirements

- Python `3.12+`
- `pynput`
- A desktop session where Python is allowed to control the mouse and keyboard
- The TerraFirmaCraft anvil UI open and visible, and an ingot with more than one page worth of recipes (like wrought iron) when you run the setup.py script
- The [TFC Anvil Helper](https://www.curseforge.com/minecraft/texture-packs/tfc-anvil-helper) resource pack installed. This is not _strictly_ required, the scripts will work the same, but letter codes for different actions is based on the colors from the resource pack, so it might be difficult to write scripts without it until you've done it a million times.
- The TerraFirmaCraft anvil UI open and visible when you run the macro
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed if you want to use it to install the dependencies and run the scripts

## Quick Start

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) (a rust based python package manager)
2. Clone this repository
3. Install the dependencies using uv

```powershell
uv sync
```

2. Open TerraFirmaCraft and open the anvil UI with an ingot with more than one page worth of recipes (like wrought iron) in your inventory (not in the top left inventory slot).
3. Run a full calibration once:

```powershell
uv run setup.py -f
```

4. Test the macro:

```powershell
uv run main.py -s 2000
```

5. Once you confirm the clicks land correctly, run longer sequences directly or from a file. (The `-s 2000` is a 2 second delay before the macro starts, you can remove it if you want the macro to start immediately).

## Installation (details)

### Option 1: Use `uv`

From the `tfc-forge-macro` folder:

```powershell
uv sync
```

Then run commands with:

```powershell
uv run setup.py --help
uv run main.py --help
```

### Option 2: Use a normal virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install pynput
```

Then run:

```powershell
python setup.py --help
python main.py --help
```

If you use a normal virtual environment, replace `uv run` with `python` in all the example commands in this README.

## Coordinate Setup

`setup.py` is interactive. It waits for you to click points on the screen and writes the
results to `coords.json`.

Press `Esc` at any time during setup to abort.

### Full Setup

Run this the first time, or any time the stored offsets are wrong:

```powershell
uv run setup.py -f
```

Full setup records:

- Anvil outer box: `tl`, `br`, `width`, `height`. (`tl` stands for top left corner, `br` stands for bottom right corner)
- Anvil buttons and controls:
  `plans`, `weld`, `input1`, `input2`, `L`, `M`, `D`, `P`, `G`, `Y`, `O`, `R`. (The letters correspond to the color of the anvil actions in the anvil GUI in the game)
- Inventory and hotbar slots:
  `i1` through `i27`, and `h1` through `h9` (i2 through h9 are derived from i1)
- Recipe outer box: `tl`, `br`, `width`, `height`
- Recipe controls:
  `rlb`, `rrb`, and `r1` through `r18` (r2 through r18 are derived from r1)

### What Full Setup Asks You To Click

For the anvil UI:

1. Top-left corner of the anvil GUI
2. Bottom-right corner of the anvil GUI
3. The center of each named anvil control
4. The center of `i1` (top-left slot of the 9x3 inventory grid)
5. Two transition clicks while moving the ingot between input slots
6. The `plans` button after the prompt sequence reaches it

For the recipe UI:

1. Top-left corner of the recipe GUI
2. Bottom-right corner of the recipe GUI
3. Left and right recipe scroll/page buttons: `rlb`, `rrb`
4. The center of `r1`

### Refresh Only the GUI Rectangles

If you already have a good `coords.json`, and only the UI position/scale changed, run setup
without `-f`:

```powershell
uv run setup.py
```

In this mode:

- the existing `coords.json` must already exist
- only the anvil and recipe rectangles are updated
- existing slot/button offsets are preserved

This is useful after changing resolution, window placement, or UI scale while keeping the
same relative layout, and is a much faster way to recalibrate than a full setup. You can still perform a full setup any time you want, which will overwrite the existing coordinates file when you're done.

## Writing macro scripts

The scripting language is based on the colors from the TFC Anvil Helper resource pack.

| Symbol | Value | Color       | Action Name |
| ------ | ----- | ----------- | ----------- |
| `L`    | -3    | Light Blue  | Light Hit   |
| `M`    | -6    | Medium Blue | Medium Hit  |
| `D`    | -9    | Dark Blue   | Hard Hit    |
| `P`    | -15   | Purple      | Draw        |
| `G`    | +2    | Green       | Punch       |
| `Y`    | +7    | Yellow      | Bend        |
| `O`    | +13   | Orange      | Upset       |
| `R`    | +16   | Red         | Shrink      |

Other than the action letters, you can also perform the following actions:

| Symbol             | Action                                                                                           |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| `plans`            | Open the plans menu                                                                              |
| `weld`             | Click the weld button                                                                            |
| `input1`           | Click the first input slot                                                                       |
| `input2`           | Click the second input slot                                                                      |
| `rlb`              | Click the left recipe scroll button on the recipe UI                                             |
| `rrb`              | Click the right recipe scroll button on the recipe UI                                            |
| `i1` through `i27` | Click the corresponding inventory slot, top left to bottom right, in the anvil screen (9x3 grid) |
| `h1` through `h9`  | Click the corresponding hotbar slot, left to right                                               |
| `r1` through `r18` | Click the corresponding recipe slot, top left to bottom right                                    |

## Calculating the forge recipes

You can manually figure out the optimal forge recipe with the [TFC Anvil Helper](https://www.curseforge.com/minecraft/texture-packs/tfc-anvil-helper) resource pack, but even with the helper it can be a pain to figure out the optimal recipe. This is where the `calculate_forge.py` script comes in.

It is an interactive script that will ask for three final actions and the target value (you need TFC Anvil Helper to know the target value for the action). It then calculates the optimal recipe for you, and outputs the string of anvil actions. You can copy that and run it through the macro directly, or load it up into a file with other actions to run lots at a time.

```powershell
uv run calculate_forge.py
```

## Running the macro directly

The main runner replays a list of slot names:

```powershell
uv run main.py SLOT SLOT SLOT
```

Example:

```powershell
uv run main.py -s 1500 i1 i2 i3
```

This waits for the start delay, then clicks the first three inventory slots in order.

### Default Test Sequence

If you run `main.py` with no slot arguments and no `--file`, it uses this built-in test:

```text
i1 i2 i3 i4 i5 i6 i7 i8 i9 i1
```

That is useful for validating that your inventory row calibration is correct.

### Speeding up the macro

The default delays for click actions are about as fast as they can be while still being reliable. The best way to speed up the macro is to decrease the delay between actions, which you can do by passing the `-d` flag to `main.py` with a smaller number. `-d 5` is reliable, and quite fast, with only 5 milliseconds between clicks, not counting the delay built into the clicks themselves to keep everything reliable.

## Running the macro through Macro Deck

The whole reason for making this macro program in the first place was so I could run it through Macro Deck, a macro recording and playback program for Windows that allows you to trigger actions through your phone.

### Setup Instructions

Assuming you already followed the [Quick Start](#quick-start) and [Coordinate Setup](#coordinate-setup) instructions and have a coords.json file. The run.vbs file is a wrapper that runs the macro through uv, so you MUST have uv installed and the dependencies synced.

1. Install the Macro Deck server and a client from https://macro-deck.app/
2. Open the server and client and connect them
3. In the server interface (on your computer), install the windows utils plugin
4. Create a new macro
   - Add a new action to the macro
   - Select "Start Application" from windows utils
   - Set the to the run.vbs file in your tfc-forge-macro folder.
   - Set the arguments something like `-d 5 --file scripts/bloom-wi_ingot-9.txt`. Any arguments just get passed through to main.py
   - Save your changes
5. Open the anvil UI in the game
6. Trigger the macro from a client (like your phone)

## Shift-Click Support

Prefix any slot token with `_` to hold `Shift` while clicking it.

Example:

```powershell
uv run main.py _i1 _i2 _i3
```

`_i2` means "shift-click `i2`".

This is the only special token syntax recognized by `main.py`.

## Using a Sequence File

Instead of passing slots on the command line, you can put them in a text file and use `--file`.

Example file:

```text
_i1
R R O Y L L L
_i2
R R Y Y Y L L L
```

Run it with:

```powershell
uv run main.py --file scripts\example.txt
```

Token parsing rules:

- commas, spaces, tabs, and newlines all work as separators
- empty entries are ignored
- if `--file` is provided, slot arguments passed on the command line are ignored
- every token must be a valid slot name, or `_slotname` for shift-click

## Command Reference

### `main.py`

```powershell
python main.py [options] [SLOT ...]
```

Options:

- `-s`, `--start-delay MS`
  Wait before starting the sequence. Default: `700` ms.
- `-d`, `--delay MS`
  Wait between clicks. Default: `200` ms.
- `--move-settle-ms MS`
  Pause after moving the cursor before mouse-down. Default: `20` ms.
- `--click-hold-ms MS`
  How long to hold the mouse button down. Default: `30` ms.
- `--post-click-ms MS`
  Pause after mouse-up. Default: `30` ms.
- `-c`, `--coords-file PATH`
  Use a custom coordinates file instead of `coords.json`.
- `-f`, `--file PATH`
  Read tokens from a text file instead of positional arguments.

Examples:

```powershell
uv run main.py -s 1200 -d 150 L M D
uv run main.py -c alt-coords.json R R O Y
uv run main.py --file scripts\forge-sequence.txt
uv run main.py --move-settle-ms 40 --click-hold-ms 50 --post-click-ms 40 L L L
```

### `setup.py`

```powershell
uv run setup.py [options]
```

Options:

- `-f`, `--full`
  Perform a full calibration from scratch.
- `-o`, `--output PATH`
  Write the generated coordinates file to a custom path.

Examples:

```powershell
uv run setup.py -f
uv run setup.py
uv run setup.py -f -o custom-coords.json
```

## How `coords.json` Works

The saved file has two top-level sections:

- `anvil`
- `recipe`

Each section stores:

- `tl`: absolute top-left pixel
- `br`: absolute bottom-right pixel
- `width`
- `height`
- normalized offsets for the named clickable targets inside that box

`main.py` converts those normalized offsets back into screen pixels at runtime.

That means:

- changing the monitor resolution or GUI scale may require rerunning `setup.py`
- if only the GUI rectangle moved but the internal layout stayed the same, rectangle-only refresh mode may be enough

## Safety and Usage Notes

- This tool moves your real mouse cursor and sends real clicks.
- Do not touch the mouse while a sequence is running.
- Keep the game window visible and in the expected state before the start delay expires.
- Start with short sequences until you trust your calibration.
- There is no dedicated emergency stop hotkey in `main.py`; use cautious timings and small tests first.
- `setup.py` does support `Esc` to abort calibration.

## Troubleshooting

### Clicks land slightly off target

- Make sure the TFC Anvil Helper resource pack is installed if you're lost with the letter codes
- Rerun `uv run setup.py`
- If the layout changed completely, rerun `uv run setup.py -f`
- Increase `--move-settle-ms` a little
- Increase `--click-hold-ms` if the game misses short clicks

### The final click is sometimes missed

Increase:

- `--post-click-ms`
- or `--click-hold-ms`

### The wrong screen area is being clicked after changing resolution or UI scale

Refresh calibration:

```powershell
uv run setup.py
```

If that does not fix it:

```powershell
uv run setup.py -f
```

### `coords.json` is missing

Create it first:

```powershell
uv run setup.py -f
```

### A slot name causes an error

Make sure the token is one of the names listed in this README. `main.py` only understands:

- defined anvil controls
- inventory/hotbar slots
- recipe slots and recipe page buttons
- optional `_` prefix for shift-click

## TODO

- [x] - Double check the anvil action colors without the resource pack and possibly change the letters or update the README to reflect the base mod
- [ ] - Add support for actions other than clicking (like pressing keys)
