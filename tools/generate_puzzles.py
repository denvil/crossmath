from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from solver import count_solutions, validate_inventory, validate_solution, validate_template_structure
from templates import build_puzzle
from template_generator import generate_template_puzzle


def puzzle_id(difficulty: str, index: int) -> str:
    return f"{difficulty}-{index:04d}"


def shuffled_tray(puzzle: dict, seed: int) -> None:
    rng = random.Random(seed)
    rng.shuffle(puzzle["tray"])
    for index, tile in enumerate(puzzle["tray"], start=1):
        tile["id"] = f"tile-{index}"
        tile["used"] = False
        tile["placedCellId"] = None


def write_counts(out_dir: Path, counts_out: Path) -> None:
    from export_counts import main as export_counts_main

    old_argv = sys.argv
    try:
        sys.argv = ["export_counts.py", "--puzzles", str(out_dir), "--out", str(counts_out)]
        export_counts_main()
    finally:
        sys.argv = old_argv


def generate(difficulty: str, count: int, out_dir: Path, seed: int, template_source: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, count + 1):
        item_seed = seed + index
        if template_source == "walk":
            item = generate_template_puzzle(difficulty, puzzle_id(difficulty, index), item_seed)
        else:
            item = build_puzzle(difficulty, puzzle_id(difficulty, index), item_seed)
        shuffled_tray(item, item_seed)
        validate_template_structure(item)
        validate_inventory(item)
        validate_solution(item)
        solution_count = count_solutions(item, limit=2)
        if solution_count != 1:
            raise ValueError(f"{item['id']}: expected 1 solution, found {solution_count}")
        item["solution_count"] = solution_count
        path = out_dir / f"{item['id']}.json"
        path.write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static CrossMath puzzle JSON files.")
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard", "all"), required=True)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("puzzles"))
    parser.add_argument("--seed", type=int, default=20260421)
    parser.add_argument("--counts-out", type=Path, default=Path("puzzle-counts.js"))
    parser.add_argument("--template-source", choices=("authored", "walk"), default="authored")
    args = parser.parse_args()

    difficulties = ("easy", "medium", "hard") if args.difficulty == "all" else (args.difficulty,)
    for offset, difficulty in enumerate(difficulties):
        generate(difficulty, args.count, args.out, args.seed + offset * 1000, args.template_source)
    write_counts(args.out, args.counts_out)


if __name__ == "__main__":
    main()
