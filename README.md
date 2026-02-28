# windower-GearSwapUpdate

Keeps GearSwap `.lua` files in sync with your actual in-game inventory by cross-referencing [findAll](https://github.com/Windower/Lua/tree/4.0/addons/findAll) snapshot data.

## How it works

| File | Role |
|------|------|
| `C:\windower\res\items.lua` | Windower's item database — maps item IDs to English names |
| `C:\windower\addons\findAll\data\<char>.lua` | findAll snapshot — every item you own, by bag |
| `C:\windower\addons\GearSwap\data\thf.lua` | GearSwap gear set file to check / fix |

`analyze.py` looks up each item name in the gear file, finds its ID in the item database, then checks whether it lives in the bag the gear file claims. `fix.py` writes the corrections back to the gear file.

## Usage

### 1. Update your findAll snapshot

Log in to the character, then run in the Windower console:

```
//findall update
```

### 2. Analyze

```bash
python analyze.py
```

Prints a report grouped by status:

- **OK** — item is in the expected bag
- **WRONG BAG** — item exists but is in a different bag
- **MISSING** — item not found in any bag
- **UNKNOWN NAME** — item name not found in the item database

### 3. Fix

```bash
python fix.py
```

- Creates a backup at `thf.lua.bak`
- Rewrites every `bag=` value to match the actual inventory location
- Prints a summary of lines changed

Run `analyze.py` again afterwards to confirm everything is clean.

## Configuration

Both scripts share constants at the top of `analyze.py`. Edit them to point at a different character or job file:

```python
ITEMS_LUA   = r"C:\windower\res\items.lua"
FINDALL_LUA = r"C:\windower\addons\findAll\data\player.lua"
GEARSWAP    = r"C:\windower\addons\GearSwap\data\thf.lua"
```

## Requirements

- Python 3.x
- [Windower 4](https://www.windower.net/) with the **findAll** addon installed


## To do

Currently this refers to a specific user ("player") and a specific job (THF). This needs to be refactored.