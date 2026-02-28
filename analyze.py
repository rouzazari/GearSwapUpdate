"""
GearSwap inventory checker.

Parses:
  - Windower items.lua   -> item name <-> ID mapping
  - findAll player.lua   -> character inventory (ID -> bags)
  - GearSwap thf.lua     -> gear sets (name + expected bag)

Reports for each referenced item:
  OK       - found in the expected bag
  WRONG BAG - found, but in a different bag
  MISSING  - not in inventory at all
  UNKNOWN  - name not found in items database
"""

import re
import sys

_player     = sys.argv[1] if len(sys.argv) > 1 else "player"

ITEMS_LUA   = r"C:\windower\res\items.lua"
FINDALL_LUA = rf"C:\windower\addons\findAll\data\{_player}.lua"
GEARSWAP    = r"C:\windower\addons\GearSwap\data\thf.lua"


# ---------------------------------------------------------------------------
# 1. Parse items.lua  ->  {name_lower: id},  {id: name}
# ---------------------------------------------------------------------------
def parse_items(path):
    name_to_id = {}
    id_to_name = {}
    pattern = re.compile(r'\[(\d+)\]\s*=\s*\{id=\d+,en="([^"]+)"')
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                item_id = int(m.group(1))
                name    = m.group(2)
                name_to_id[name.lower()] = item_id
                id_to_name[item_id]      = name
    return name_to_id, id_to_name


# ---------------------------------------------------------------------------
# 2. Parse findAll player.lua  ->  {item_id: [bag, ...]}
# ---------------------------------------------------------------------------
def parse_findall(path):
    id_to_bags = {}   # int id -> list of bag names where qty > 0

    current_bag = None
    bag_pattern  = re.compile(r'^\["([^"]+)"\]\s*=\s*\{')
    item_pattern = re.compile(r'^\s*\["(\d+)"\]\s*=\s*(\d+)')

    with open(path, encoding="utf-8") as f:
        for line in f:
            bm = bag_pattern.match(line)
            if bm:
                current_bag = bm.group(1)
                continue

            if current_bag:
                im = item_pattern.match(line)
                if im:
                    item_id = int(im.group(1))
                    qty     = int(im.group(2))
                    if qty > 0:
                        id_to_bags.setdefault(item_id, []).append(current_bag)

    return id_to_bags


# ---------------------------------------------------------------------------
# 3. Parse thf.lua  ->  list of (name, bag)
# ---------------------------------------------------------------------------
def parse_gearswap(path):
    items = []
    # match:  name = "Foo Bar", bag = "wardrobe2"
    pattern = re.compile(r'name\s*=\s*"([^"]+)"(?:[^}]*bag\s*=\s*"([^"]+)")?')
    with open(path, encoding="utf-8") as f:
        for line in f:
            # skip comment lines
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            for m in pattern.finditer(line):
                name = m.group(1)
                bag  = m.group(2) or "?"
                items.append((name, bag))
    return items


# ---------------------------------------------------------------------------
# 4. Cross-reference and report
# ---------------------------------------------------------------------------
def main():
    print("Loading items database...")
    name_to_id, id_to_name = parse_items(ITEMS_LUA)
    print(f"  {len(name_to_id)} items loaded.")

    print("Loading findAll inventory...")
    id_to_bags = parse_findall(FINDALL_LUA)
    print(f"  {len(id_to_bags)} unique item IDs found across all bags.")

    print("Loading GearSwap file...")
    gear_items = parse_gearswap(GEARSWAP)
    # Deduplicate while preserving order
    seen = set()
    unique_items = []
    for name, bag in gear_items:
        key = (name.lower(), bag)
        if key not in seen:
            seen.add(key)
            unique_items.append((name, bag))
    print(f"  {len(unique_items)} unique gear references found.\n")

    # Categorise
    ok        = []
    wrong_bag = []
    missing   = []
    unknown   = []

    for name, expected_bag in unique_items:
        item_id = name_to_id.get(name.lower())
        if item_id is None:
            unknown.append((name, expected_bag))
            continue

        actual_bags = id_to_bags.get(item_id, [])
        if not actual_bags:
            missing.append((name, expected_bag, item_id))
        elif expected_bag in actual_bags:
            ok.append((name, expected_bag, item_id))
        else:
            wrong_bag.append((name, expected_bag, item_id, actual_bags))

    # --- Report ---
    print("=" * 70)
    print(f"OK           ({len(ok)})")
    print("=" * 70)
    for name, bag, item_id in ok:
        print(f"  [id={item_id:>6}]  {name!r:35}  bag={bag}")

    print()
    print("=" * 70)
    print(f"WRONG BAG    ({len(wrong_bag)})  -- item exists but in a different bag")
    print("=" * 70)
    for name, expected, item_id, actuals in wrong_bag:
        print(f"  [id={item_id:>6}]  {name!r:35}  expected={expected!r}  found_in={actuals}")

    print()
    print("=" * 70)
    print(f"MISSING      ({len(missing)})  -- not found in any bag")
    print("=" * 70)
    for name, bag, item_id in missing:
        print(f"  [id={item_id:>6}]  {name!r:35}  (expected bag={bag})")

    print()
    print("=" * 70)
    print(f"UNKNOWN NAME ({len(unknown)})  -- not found in items database")
    print("=" * 70)
    for name, bag in unknown:
        print(f"  {name!r:40}  (expected bag={bag})")

    print()
    print("Summary:")
    total = len(ok) + len(wrong_bag) + len(missing) + len(unknown)
    print(f"  Total references : {total}")
    print(f"  OK               : {len(ok)}")
    print(f"  Wrong bag        : {len(wrong_bag)}")
    print(f"  Missing          : {len(missing)}")
    print(f"  Unknown name     : {len(unknown)}")


if __name__ == "__main__":
    main()
