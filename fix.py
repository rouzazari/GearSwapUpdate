"""
GearSwap bag fixer.

Reads the analysis results and patches thf.lua so every item's
bag= field matches where it actually lives in the findAll inventory.

A backup is written to thf.lua.bak before any changes are made.
"""

import re
import shutil
from analyze import parse_items, parse_findall, parse_gearswap

ITEMS_LUA   = r"C:\windower\res\items.lua"
FINDALL_LUA = r"C:\windower\addons\findAll\data\player.lua"
GEARSWAP    = r"C:\windower\addons\GearSwap\data\thf.lua"


def build_corrections(name_to_id, id_to_bags, gear_items):
    """
    Returns a dict: {item_name_lower: correct_bag}
    for every item whose bag in the gear file doesn't match inventory.
    """
    corrections = {}
    for name, expected_bag in gear_items:
        item_id = name_to_id.get(name.lower())
        if item_id is None:
            continue
        actual_bags = id_to_bags.get(item_id, [])
        if not actual_bags:
            continue
        if expected_bag not in actual_bags:
            # Use the first bag the item is found in
            corrections[name.lower()] = (name, actual_bags[0])
    return corrections


def apply_fixes(path, corrections):
    """
    Rewrites path in-place, updating bag= values for items in corrections.
    Returns the number of lines changed.
    """
    # Pattern captures: prefix, item name, mid (stuff between name and bag), bag value, suffix
    line_pattern = re.compile(
        r'(name\s*=\s*")([^"]+)("(?:[^}]*?)bag\s*=\s*")([^"]+)(")'
    )

    changes = 0
    new_lines = []

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            new_lines.append(line)
            continue

        def replacer(m):
            nonlocal changes
            item_name = m.group(2)
            correction = corrections.get(item_name.lower())
            if correction is None:
                return m.group(0)
            _, correct_bag = correction
            old_bag = m.group(4)
            if old_bag == correct_bag:
                return m.group(0)
            changes += 1
            return m.group(1) + item_name + m.group(3) + correct_bag + m.group(5)

        new_line = line_pattern.sub(replacer, line)
        new_lines.append(new_line)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return changes


def main():
    print("Loading data...")
    name_to_id, _ = parse_items(ITEMS_LUA)
    id_to_bags     = parse_findall(FINDALL_LUA)
    gear_items     = parse_gearswap(GEARSWAP)

    corrections = build_corrections(name_to_id, id_to_bags, gear_items)

    if not corrections:
        print("Nothing to fix — all bag assignments are correct.")
        return

    print(f"\nItems to fix ({len(corrections)}):")
    for name_lower, (name, correct_bag) in sorted(corrections.items()):
        print(f"  {name!r:35} -> bag={correct_bag!r}")

    # Backup
    backup = GEARSWAP + ".bak"
    shutil.copy2(GEARSWAP, backup)
    print(f"\nBackup written to: {backup}")

    # Apply
    changed = apply_fixes(GEARSWAP, corrections)
    print(f"Lines updated: {changed}")
    print("Done.")


if __name__ == "__main__":
    main()
