#!/usr/bin/env python3
"""Insert schedule lines into Day.md after the **Schedule:** marker.

Usage:
    python3 update-day-schedule.py "0800 Standup" "1000 Deep work" "1400 Call with Alice"
    python3 update-day-schedule.py   # no args → inserts "No events scheduled."
"""

import sys

DAY_MD = "/Users/ph/Documents/Obsidian Notes/Day.md"
MARKER = "**Schedule:**\n"


def main():
    events = sys.argv[1:]
    if events:
        insert_block = "\n".join(events) + "\n\n"
    else:
        insert_block = "No events scheduled.\n\n"

    with open(DAY_MD, "r") as f:
        content = f.read()

    idx = content.find(MARKER)
    if idx == -1:
        print("ERROR: Could not find '**Schedule:**' marker in Day.md", file=sys.stderr)
        sys.exit(1)

    insert_pos = idx + len(MARKER)

    # Replace previous CoS insertion (block ending at next \n\n)
    prev_end = content.find("\n\n", insert_pos)
    if prev_end != -1:
        prev_end += 2
        content = content[:insert_pos] + insert_block + content[prev_end:]
    else:
        content = content[:insert_pos] + insert_block + content[insert_pos:]

    with open(DAY_MD, "w") as f:
        f.write(content)

    n = len(events)
    print(f"Day.md updated — {n} event{'s' if n != 1 else ''} written")


if __name__ == "__main__":
    main()
