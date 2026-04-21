from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export frontend puzzle counts.")
    parser.add_argument("--puzzles", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    counts = Counter(path.name.split("-", 1)[0] for path in args.puzzles.glob("*.json"))
    ordered = {difficulty: counts.get(difficulty, 0) for difficulty in ("easy", "medium", "hard")}
    content = "window.PUZZLE_COUNTS = " + json.dumps(ordered, indent=2) + ";\n"
    args.out.write_text(content, encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

