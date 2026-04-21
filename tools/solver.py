from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def cell_value(cell: dict, assignments: dict[str, int]) -> int | None:
    if cell["type"] == "fixed-number":
        return int(cell["value"])
    if cell["type"] == "slot":
        return assignments.get(cell["id"])
    return None


def evaluate(left: int, operator: str, right: int) -> int | None:
    if operator == "+":
        return left + right
    if operator == "-":
        return left - right
    if operator in {"x", "*"}:
        return left * right
    if operator == "/":
        if right == 0 or left % right != 0:
            return None
        return left // right
    raise ValueError(f"Unsupported operator: {operator}")


def run_status(run: list[str], cells_by_id: dict[str, dict], assignments: dict[str, int]) -> bool | None:
    left_cell, op_cell, right_cell, eq_cell, result_cell = [cells_by_id[cell_id] for cell_id in run]
    if op_cell["type"] != "operator" or eq_cell["type"] != "equals":
        raise ValueError(f"Invalid run shape: {run}")

    left = cell_value(left_cell, assignments)
    right = cell_value(right_cell, assignments)
    result = cell_value(result_cell, assignments)

    if left is None or right is None or result is None:
        return None

    return evaluate(left, op_cell["value"], right) == result


def validate_run_contiguity(puzzle: dict) -> None:
    cells_by_id = {cell["id"]: cell for cell in puzzle["cells"]}
    for run in puzzle_runs(puzzle):
        if len(run) != 5:
            raise ValueError(f"{puzzle['id']}: run must have 5 cells: {run}")
        cells = [cells_by_id[cell_id] for cell_id in run]
        rows = [cell["row"] for cell in cells]
        cols = [cell["col"] for cell in cells]
        same_row = len(set(rows)) == 1 and cols == list(range(cols[0], cols[0] + 5))
        same_col = len(set(cols)) == 1 and rows == list(range(rows[0], rows[0] + 5))
        if not same_row and not same_col:
            raise ValueError(f"{puzzle['id']}: run is not contiguous: {run}")


def validate_no_orphans(puzzle: dict) -> None:
    used_cell_ids = {cell_id for run in puzzle_runs(puzzle) for cell_id in run}
    rendered_cell_ids = {cell["id"] for cell in puzzle["cells"]}
    orphan_ids = sorted(rendered_cell_ids - used_cell_ids)
    if orphan_ids:
        raise ValueError(f"{puzzle['id']}: cells are not part of any run: {orphan_ids}")


def validate_connected_board(puzzle: dict) -> None:
    cells_by_pos = {(cell["row"], cell["col"]): cell for cell in puzzle["cells"]}
    if not cells_by_pos:
        raise ValueError(f"{puzzle['id']}: puzzle has no rendered cells")

    start = next(iter(cells_by_pos))
    seen = {start}
    stack = [start]

    while stack:
        row, col = stack.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in cells_by_pos and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)

    if len(seen) != len(cells_by_pos):
        disconnected = sorted(cell["id"] for pos, cell in cells_by_pos.items() if pos not in seen)
        raise ValueError(f"{puzzle['id']}: board has disconnected cells: {disconnected}")


def validate_adjacency_edges(puzzle: dict) -> None:
    cells_by_pos = {(cell["row"], cell["col"]): cell for cell in puzzle["cells"]}
    allowed_edges = set()

    for run in puzzle_runs(puzzle):
        for left, right in zip(run, run[1:]):
            allowed_edges.add(frozenset((left, right)))

    for (row, col), cell in cells_by_pos.items():
        for neighbor_pos in ((row + 1, col), (row, col + 1)):
            neighbor = cells_by_pos.get(neighbor_pos)
            if not neighbor:
                continue
            edge = frozenset((cell["id"], neighbor["id"]))
            if edge not in allowed_edges:
                raise ValueError(
                    f"{puzzle['id']}: adjacent cells are not consecutive in a run: "
                    f"{cell['id']} and {neighbor['id']}"
                )


def validate_template_structure(puzzle: dict) -> None:
    validate_run_contiguity(puzzle)
    validate_no_orphans(puzzle)
    validate_connected_board(puzzle)
    validate_adjacency_edges(puzzle)


def puzzle_runs(puzzle: dict) -> list[list[str]]:
    if puzzle.get("runs"):
        return puzzle["runs"]
    return infer_runs(puzzle)


def infer_runs(puzzle: dict) -> list[list[str]]:
    cells_by_pos = {(cell["row"], cell["col"]): cell for cell in puzzle["cells"]}
    runs = []
    for row in range(puzzle["rows"]):
        for col in range(puzzle["cols"] - 4):
            run = [cells_by_pos.get((row, col + offset)) for offset in range(5)]
            if is_run(run):
                runs.append([cell["id"] for cell in run])
    for row in range(puzzle["rows"] - 4):
        for col in range(puzzle["cols"]):
            run = [cells_by_pos.get((row + offset, col)) for offset in range(5)]
            if is_run(run):
                runs.append([cell["id"] for cell in run])
    return runs


def is_run(run: list[dict | None]) -> bool:
    if any(cell is None for cell in run):
        return False
    return (
        run[0]["type"] in {"slot", "fixed-number"}
        and run[1]["type"] == "operator"
        and run[2]["type"] in {"slot", "fixed-number"}
        and run[3]["type"] == "equals"
        and run[4]["type"] in {"slot", "fixed-number"}
    )


def validate_inventory(puzzle: dict) -> None:
    slot_values = sorted(int(cell["solution"]) for cell in puzzle["cells"] if cell["type"] == "slot")
    tray_values = sorted(int(tile["value"]) for tile in puzzle["tray"])
    if slot_values != tray_values:
        raise ValueError(f"{puzzle['id']}: tray inventory does not match slot solutions")


def validate_solution(puzzle: dict) -> None:
    cells_by_id = {cell["id"]: cell for cell in puzzle["cells"]}
    assignments = {cell["id"]: int(cell["solution"]) for cell in puzzle["cells"] if cell["type"] == "slot"}
    for run in puzzle_runs(puzzle):
        if run_status(run, cells_by_id, assignments) is not True:
            raise ValueError(f"{puzzle['id']}: solution fails run {run}")


def count_solutions(puzzle: dict, limit: int = 2) -> int:
    cells_by_id = {cell["id"]: cell for cell in puzzle["cells"]}
    slots = [cell for cell in puzzle["cells"] if cell["type"] == "slot"]
    runs = puzzle_runs(puzzle)
    runs_by_slot: dict[str, list[list[str]]] = {slot["id"]: [] for slot in slots}
    for run in runs:
        for cell_id in run:
            if cell_id in runs_by_slot:
                runs_by_slot[cell_id].append(run)

    ordered_slots = sorted(slots, key=lambda cell: len(runs_by_slot[cell["id"]]), reverse=True)
    remaining = Counter(int(tile["value"]) for tile in puzzle["tray"])
    assignments: dict[str, int] = {}
    count = 0

    def consistent(slot_id: str) -> bool:
        for run in runs_by_slot[slot_id]:
            status = run_status(run, cells_by_id, assignments)
            if status is False:
                return False
        return True

    def search(index: int) -> None:
        nonlocal count
        if count >= limit:
            return
        if index == len(ordered_slots):
            if all(run_status(run, cells_by_id, assignments) is True for run in runs):
                count += 1
            return

        slot_id = ordered_slots[index]["id"]
        for value in list(remaining):
            if remaining[value] < 1:
                continue
            remaining[value] -= 1
            assignments[slot_id] = value
            if consistent(slot_id):
                search(index + 1)
            del assignments[slot_id]
            remaining[value] += 1

    search(0)
    return count


def validate_puzzle(path: Path) -> str:
    puzzle = json.loads(path.read_text(encoding="utf-8"))
    validate_template_structure(puzzle)
    validate_inventory(puzzle)
    validate_solution(puzzle)
    count = count_solutions(puzzle, limit=2)
    if count != 1:
        raise ValueError(f"{puzzle['id']}: expected 1 solution, found {count}")
    return f"{path.name}: valid, unique solution"


def iter_json_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob("*.json"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate CrossMath puzzle JSON files.")
    parser.add_argument("--validate", type=Path, required=True, help="Puzzle JSON file or directory.")
    args = parser.parse_args()

    for path in iter_json_files(args.validate):
        print(validate_puzzle(path))


if __name__ == "__main__":
    main()
