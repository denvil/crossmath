from __future__ import annotations

from copy import deepcopy
import random


def tile(value: int, index: int) -> dict:
    return {
        "id": f"tile-{index}",
        "value": value,
        "used": False,
        "placedCellId": None,
    }


def slot(cell_id: str, row: int, col: int, solution: int) -> dict:
    return {"id": cell_id, "row": row, "col": col, "type": "slot", "solution": solution}


def fixed(cell_id: str, row: int, col: int, value: int) -> dict:
    return {"id": cell_id, "row": row, "col": col, "type": "fixed-number", "value": value}


def op(cell_id: str, row: int, col: int, value: str) -> dict:
    return {"id": cell_id, "row": row, "col": col, "type": "operator", "value": value}


def eq(cell_id: str, row: int, col: int) -> dict:
    return {"id": cell_id, "row": row, "col": col, "type": "equals", "value": "="}


def make_tray(values: list[int]) -> list[dict]:
    return [tile(value, index + 1) for index, value in enumerate(values)]


def solution_map(cells: list[dict]) -> dict:
    return {cell["id"]: cell["solution"] for cell in cells if cell["type"] == "slot"}


def make_puzzle(
    *,
    puzzle_id: str,
    difficulty: str,
    rows: int,
    cols: int,
    template_id: str,
    cells: list[dict],
    runs: list[list[str]],
    seed: int,
) -> dict:
    missing_values = [cell["solution"] for cell in cells if cell["type"] == "slot"]
    return {
        "id": puzzle_id,
        "version": 1,
        "difficulty": difficulty,
        "rows": rows,
        "cols": cols,
        "template_id": template_id,
        "solution_count": 1,
        "seed": seed,
        "operator_set": sorted({cell["value"] for cell in cells if cell["type"] == "operator"}),
        "single_digit_only": all(value < 10 for value in missing_values),
        "cells": cells,
        "runs": runs,
        "tray": make_tray(missing_values),
        "solution": solution_map(cells),
    }


def easy_template(puzzle_id: str, seed: int) -> dict:
    cells = [
        slot("r0c0", 0, 0, 5),
        op("r0c1", 0, 1, "+"),
        fixed("r0c2", 0, 2, 4),
        eq("r0c3", 0, 3),
        slot("r0c4", 0, 4, 9),
        op("r1c0", 1, 0, "-"),
        op("r1c2", 1, 2, "+"),
        slot("r2c0", 2, 0, 3),
        op("r2c1", 2, 1, "+"),
        slot("r2c2", 2, 2, 3),
        eq("r2c3", 2, 3),
        fixed("r2c4", 2, 4, 6),
        eq("r3c0", 3, 0),
        eq("r3c2", 3, 2),
        fixed("r4c0", 4, 0, 2),
        op("r4c1", 4, 1, "+"),
        slot("r4c2", 4, 2, 7),
        eq("r4c3", 4, 3),
        slot("r4c4", 4, 4, 9),
    ]
    runs = [
        ["r0c0", "r0c1", "r0c2", "r0c3", "r0c4"],
        ["r2c0", "r2c1", "r2c2", "r2c3", "r2c4"],
        ["r4c0", "r4c1", "r4c2", "r4c3", "r4c4"],
        ["r0c0", "r1c0", "r2c0", "r3c0", "r4c0"],
        ["r0c2", "r1c2", "r2c2", "r3c2", "r4c2"],
    ]
    return make_puzzle(
        puzzle_id=puzzle_id,
        difficulty="easy",
        rows=7,
        cols=7,
        template_id="cross_7x7_easy_01",
        cells=cells,
        runs=runs,
        seed=seed,
    )


def easy_template_branch(puzzle_id: str, seed: int) -> dict:
    cells = [
        slot("r0c0", 0, 0, 5),
        op("r0c1", 0, 1, "+"),
        fixed("r0c2", 0, 2, 4),
        eq("r0c3", 0, 3),
        slot("r0c4", 0, 4, 9),
        op("r1c0", 1, 0, "-"),
        op("r1c2", 1, 2, "+"),
        slot("r2c0", 2, 0, 3),
        op("r2c1", 2, 1, "+"),
        slot("r2c2", 2, 2, 3),
        eq("r2c3", 2, 3),
        fixed("r2c4", 2, 4, 6),
        op("r2c5", 2, 5, "+"),
        slot("r2c6", 2, 6, 2),
        eq("r2c7", 2, 7),
        slot("r2c8", 2, 8, 8),
        eq("r3c0", 3, 0),
        eq("r3c2", 3, 2),
        fixed("r4c0", 4, 0, 2),
        op("r4c1", 4, 1, "+"),
        slot("r4c2", 4, 2, 7),
        eq("r4c3", 4, 3),
        slot("r4c4", 4, 4, 9),
    ]
    runs = [
        ["r0c0", "r0c1", "r0c2", "r0c3", "r0c4"],
        ["r2c0", "r2c1", "r2c2", "r2c3", "r2c4"],
        ["r2c4", "r2c5", "r2c6", "r2c7", "r2c8"],
        ["r4c0", "r4c1", "r4c2", "r4c3", "r4c4"],
        ["r0c0", "r1c0", "r2c0", "r3c0", "r4c0"],
        ["r0c2", "r1c2", "r2c2", "r3c2", "r4c2"],
    ]
    return make_puzzle(
        puzzle_id=puzzle_id,
        difficulty="easy",
        rows=5,
        cols=9,
        template_id="cross_5x9_easy_branch_01",
        cells=cells,
        runs=runs,
        seed=seed,
    )


def medium_template(puzzle_id: str, seed: int) -> dict:
    cells = [
        slot("r0c0", 0, 0, 5),
        op("r0c1", 0, 1, "-"),
        fixed("r0c2", 0, 2, 1),
        eq("r0c3", 0, 3),
        slot("r0c4", 0, 4, 4),
        slot("r0c6", 0, 6, 4),
        op("r0c7", 0, 7, "+"),
        fixed("r0c8", 0, 8, 4),
        eq("r0c9", 0, 9),
        slot("r0c10", 0, 10, 8),
        op("r1c0", 1, 0, "+"),
        op("r1c2", 1, 2, "+"),
        op("r1c4", 1, 4, "+"),
        op("r1c6", 1, 6, "+"),
        op("r1c10", 1, 10, "-"),
        fixed("r2c0", 2, 0, 3),
        slot("r2c2", 2, 2, 7),
        op("r2c3", 2, 3, "-"),
        slot("r2c4", 2, 4, 3),
        eq("r2c5", 2, 5),
        slot("r2c6", 2, 6, 4),
        slot("r2c10", 2, 10, 2),
        eq("r3c0", 3, 0),
        eq("r3c2", 3, 2),
        eq("r3c4", 3, 4),
        eq("r3c6", 3, 6),
        eq("r3c10", 3, 10),
        slot("r4c0", 4, 0, 8),
        slot("r4c2", 4, 2, 8),
        fixed("r4c4", 4, 4, 7),
        slot("r4c6", 4, 6, 8),
        op("r4c7", 4, 7, "-"),
        slot("r4c8", 4, 8, 2),
        eq("r4c9", 4, 9),
        fixed("r4c10", 4, 10, 6),
        op("r5c8", 5, 8, "+"),
        fixed("r6c0", 6, 0, 9),
        op("r6c1", 6, 1, "+"),
        slot("r6c2", 6, 2, 9),
        eq("r6c3", 6, 3),
        fixed("r6c4", 6, 4, 18),
        slot("r6c6", 6, 6, 8),
        op("r6c7", 6, 7, "-"),
        slot("r6c8", 6, 8, 3),
        eq("r6c9", 6, 9),
        slot("r6c10", 6, 10, 5),
        op("r7c0", 7, 0, "-"),
        op("r7c2", 7, 2, "+"),
        op("r7c6", 7, 6, "+"),
        eq("r7c8", 7, 8),
        op("r7c10", 7, 10, "+"),
        fixed("r8c0", 8, 0, 6),
        slot("r8c2", 8, 2, 2),
        op("r8c3", 8, 3, "x"),
        fixed("r8c4", 8, 4, 2),
        eq("r8c5", 8, 5),
        slot("r8c6", 8, 6, 4),
        fixed("r8c8", 8, 8, 5),
        fixed("r8c10", 8, 10, 8),
        eq("r9c0", 9, 0),
        eq("r9c2", 9, 2),
        eq("r9c6", 9, 6),
        eq("r9c10", 9, 10),
        slot("r10c0", 10, 0, 3),
        op("r10c1", 10, 1, "+"),
        slot("r10c2", 10, 2, 11),
        eq("r10c3", 10, 3),
        fixed("r10c4", 10, 4, 14),
        fixed("r10c6", 10, 6, 12),
        op("r10c7", 10, 7, "+"),
        slot("r10c8", 10, 8, 1),
        eq("r10c9", 10, 9),
        slot("r10c10", 10, 10, 13),
    ]
    runs = [
        ["r0c0", "r0c1", "r0c2", "r0c3", "r0c4"],
        ["r0c6", "r0c7", "r0c8", "r0c9", "r0c10"],
        ["r2c2", "r2c3", "r2c4", "r2c5", "r2c6"],
        ["r4c6", "r4c7", "r4c8", "r4c9", "r4c10"],
        ["r6c0", "r6c1", "r6c2", "r6c3", "r6c4"],
        ["r6c6", "r6c7", "r6c8", "r6c9", "r6c10"],
        ["r8c2", "r8c3", "r8c4", "r8c5", "r8c6"],
        ["r10c0", "r10c1", "r10c2", "r10c3", "r10c4"],
        ["r10c6", "r10c7", "r10c8", "r10c9", "r10c10"],
        ["r0c0", "r1c0", "r2c0", "r3c0", "r4c0"],
        ["r0c2", "r1c2", "r2c2", "r3c2", "r4c2"],
        ["r0c4", "r1c4", "r2c4", "r3c4", "r4c4"],
        ["r0c6", "r1c6", "r2c6", "r3c6", "r4c6"],
        ["r0c10", "r1c10", "r2c10", "r3c10", "r4c10"],
        ["r6c0", "r7c0", "r8c0", "r9c0", "r10c0"],
        ["r6c2", "r7c2", "r8c2", "r9c2", "r10c2"],
        ["r6c6", "r7c6", "r8c6", "r9c6", "r10c6"],
        ["r4c8", "r5c8", "r6c8", "r7c8", "r8c8"],
        ["r6c10", "r7c10", "r8c10", "r9c10", "r10c10"],
    ]
    return make_puzzle(
        puzzle_id=puzzle_id,
        difficulty="medium",
        rows=11,
        cols=11,
        template_id="cross_11x11_medium_01",
        cells=cells,
        runs=runs,
        seed=seed,
    )


def medium_template_branch(puzzle_id: str, seed: int) -> dict:
    puzzle = easy_template_branch(puzzle_id, seed)
    puzzle["difficulty"] = "medium"
    puzzle["template_id"] = "cross_5x9_medium_branch_01"
    puzzle["cells"].extend(
        [
            op("r4c5", 4, 5, "x"),
            slot("r4c6", 4, 6, 2),
            eq("r4c7", 4, 7),
            fixed("r4c8", 4, 8, 18),
        ]
    )
    puzzle["runs"].append(["r4c4", "r4c5", "r4c6", "r4c7", "r4c8"])
    puzzle["tray"] = make_tray([cell["solution"] for cell in puzzle["cells"] if cell["type"] == "slot"])
    puzzle["solution"] = solution_map(puzzle["cells"])
    puzzle["operator_set"] = sorted({cell["value"] for cell in puzzle["cells"] if cell["type"] == "operator"})
    puzzle["single_digit_only"] = all(tile["value"] < 10 for tile in puzzle["tray"])
    return puzzle


def hard_template(puzzle_id: str, seed: int) -> dict:
    puzzle = medium_template(puzzle_id, seed)
    puzzle["difficulty"] = "hard"
    puzzle["template_id"] = "cross_11x11_hard_01"
    replacements = {
        "r0c6": {"solution": 8},
        "r0c10": {"solution": 12},
        "r2c10": {"solution": 6},
        "r4c6": {"solution": 12},
        "r4c7": {"value": "/"},
    }

    for cell in puzzle["cells"]:
        if cell["id"] in replacements:
            cell.update(replacements[cell["id"]])

    puzzle["tray"] = make_tray([cell["solution"] for cell in puzzle["cells"] if cell["type"] == "slot"])
    puzzle["solution"] = solution_map(puzzle["cells"])
    puzzle["operator_set"] = sorted({cell["value"] for cell in puzzle["cells"] if cell["type"] == "operator"})
    puzzle["single_digit_only"] = False
    return puzzle


def hard_template_branch(puzzle_id: str, seed: int) -> dict:
    puzzle = easy_template_branch(puzzle_id, seed)
    puzzle["difficulty"] = "hard"
    puzzle["template_id"] = "cross_5x9_hard_branch_01"

    replacements = {
        "r2c5": {"value": "x"},
        "r2c8": {"solution": 12},
    }
    for cell in puzzle["cells"]:
        if cell["id"] in replacements:
            cell.update(replacements[cell["id"]])

    puzzle["cells"].extend(
        [
            op("r4c5", 4, 5, "/"),
            slot("r4c6", 4, 6, 3),
            eq("r4c7", 4, 7),
            fixed("r4c8", 4, 8, 3),
        ]
    )
    puzzle["runs"].append(["r4c4", "r4c5", "r4c6", "r4c7", "r4c8"])
    puzzle["tray"] = make_tray([cell["solution"] for cell in puzzle["cells"] if cell["type"] == "slot"])
    puzzle["solution"] = solution_map(puzzle["cells"])
    puzzle["operator_set"] = sorted({cell["value"] for cell in puzzle["cells"] if cell["type"] == "operator"})
    puzzle["single_digit_only"] = False
    return puzzle


TEMPLATES = {
    "easy": [easy_template, easy_template_branch],
    "medium": [medium_template, medium_template_branch],
    "hard": [hard_template, hard_template_branch],
}


def build_puzzle(difficulty: str, puzzle_id: str, seed: int) -> dict:
    if difficulty not in TEMPLATES:
        raise ValueError(f"Unknown difficulty: {difficulty}")
    templates = TEMPLATES[difficulty]
    template = random.Random(seed).choice(templates)
    return deepcopy(template(puzzle_id, seed))
