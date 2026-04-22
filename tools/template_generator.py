from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

from solver import count_solutions, validate_inventory, validate_solution, validate_template_structure
from templates import eq, fixed, make_puzzle, op, slot


NUMBER_POSITIONS = {0, 2, 4}
TOKEN_TYPES = ("number", "operator", "number", "equals", "number")
RUN_LENGTH = 5


@dataclass(frozen=True)
class Profile:
    rows: int
    cols: int
    target_runs: int
    operators: tuple[str, ...]
    min_value: int
    max_value: int
    allow_two_digit: bool
    loop_probability: float
    extra_slot_probability: float
    min_slots: int
    max_slots: int
    min_two_digit_slots: int
    min_cycle_count: int
    min_single_step_stuck_slots: int


PROFILES = {
    "easy": Profile(
        rows=7,
        cols=9,
        target_runs=4,
        operators=("+", "-"),
        min_value=1,
        max_value=9,
        allow_two_digit=False,
        loop_probability=0.05,
        extra_slot_probability=0.0,
        min_slots=0,
        max_slots=0,
        min_two_digit_slots=0,
        min_cycle_count=0,
        min_single_step_stuck_slots=0,
    ),
    "medium": Profile(
        rows=11,
        cols=11,
        target_runs=9,
        operators=("+", "-", "x"),
        min_value=1,
        max_value=14,
        allow_two_digit=True,
        loop_probability=0.35,
        extra_slot_probability=0.35,
        min_slots=10,
        max_slots=14,
        min_two_digit_slots=1,
        min_cycle_count=1,
        min_single_step_stuck_slots=1,
    ),
    "hard": Profile(
        rows=13,
        cols=13,
        target_runs=12,
        operators=("+", "-", "x", "/"),
        min_value=1,
        max_value=24,
        allow_two_digit=True,
        loop_probability=0.5,
        extra_slot_probability=0.45,
        min_slots=14,
        max_slots=18,
        min_two_digit_slots=4,
        min_cycle_count=3,
        min_single_step_stuck_slots=3,
    ),
}


def pos_id(row: int, col: int) -> str:
    return f"r{row}c{col}"


def candidate_coords(anchor: tuple[int, int], orientation: str, anchor_index: int) -> list[tuple[int, int]]:
    row, col = anchor
    coords = []
    for index in range(RUN_LENGTH):
        offset = index - anchor_index
        if orientation == "h":
            coords.append((row, col + offset))
        else:
            coords.append((row + offset, col))
    return coords


def in_bounds(coords: list[tuple[int, int]], profile: Profile) -> bool:
    return all(0 <= row < profile.rows and 0 <= col < profile.cols for row, col in coords)


def token_type(index: int, operator_value: str | None = None) -> str:
    if index in NUMBER_POSITIONS:
        return "number"
    if index == 1:
        return f"operator:{operator_value or ''}"
    return "equals"


def adjacent_pairs(coords: list[tuple[int, int]]) -> set[frozenset[tuple[int, int]]]:
    return {frozenset((left, right)) for left, right in zip(coords, coords[1:])}


def can_place_run(
    *,
    coords: list[tuple[int, int]],
    operator_value: str,
    grid: dict[tuple[int, int], str],
    run_edges: set[frozenset[tuple[int, int]]],
    allowed_overlaps: set[tuple[int, int]],
) -> bool:
    candidate_edges = adjacent_pairs(coords)
    overlaps = [coord for coord in coords if coord in grid]
    if set(overlaps) != allowed_overlaps:
        return False

    for index, coord in enumerate(coords):
        expected = token_type(index, operator_value)
        existing = grid.get(coord)
        if existing and existing != expected and not (existing.startswith("operator:") and expected.startswith("operator:")):
            return False
        if existing and index not in NUMBER_POSITIONS:
            return False
        if existing and index in NUMBER_POSITIONS and existing != "number":
            return False

    for index, coord in enumerate(coords):
        row, col = coord
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor not in grid:
                continue
            if frozenset((coord, neighbor)) not in candidate_edges and frozenset((coord, neighbor)) not in run_edges:
                return False

    return True


def evaluate(left: int, operator_value: str, right: int) -> int | None:
    if operator_value == "+":
        return left + right
    if operator_value == "-":
        return left - right
    if operator_value == "x":
        return left * right
    if operator_value == "/":
        if right == 0 or left % right != 0:
            return None
        return left // right
    raise ValueError(f"Unsupported operator: {operator_value}")


def solve_run_values(
    *,
    rng: random.Random,
    operator_value: str,
    fixed_values: dict[int, int],
    profile: Profile,
) -> tuple[int, int, int] | None:
    candidates = []
    for left in range(profile.min_value, profile.max_value + 1):
        for right in range(profile.min_value, profile.max_value + 1):
            result = evaluate(left, operator_value, right)
            if result is None or result < profile.min_value or result > profile.max_value:
                continue
            values = (left, right, result)
            if fixed_values:
                if any(values[(0, 2, 4).index(index)] != value for index, value in fixed_values.items()):
                    continue
            candidates.append(values)
    if not candidates:
        return None
    return rng.choice(candidates)


def normalize(
    grid: dict[tuple[int, int], str],
    runs: list[list[tuple[int, int]]],
    values: dict[tuple[int, int], int],
    slot_positions: set[tuple[int, int]],
) -> tuple[dict[tuple[int, int], str], list[list[tuple[int, int]]], dict[tuple[int, int], int], set[tuple[int, int]], int, int]:
    min_row = min(row for row, _ in grid)
    min_col = min(col for _, col in grid)

    def shift(coord: tuple[int, int]) -> tuple[int, int]:
        row, col = coord
        return row - min_row, col - min_col

    next_grid = {shift(coord): value for coord, value in grid.items()}
    next_runs = [[shift(coord) for coord in run] for run in runs]
    next_values = {shift(coord): value for coord, value in values.items()}
    next_slots = {shift(coord) for coord in slot_positions}
    rows = max(row for row, _ in next_grid) + 1
    cols = max(col for _, col in next_grid) + 1
    return next_grid, next_runs, next_values, next_slots, rows, cols


def build_cells(
    grid: dict[tuple[int, int], str],
    values: dict[tuple[int, int], int],
    slot_positions: set[tuple[int, int]],
) -> list[dict]:
    cells = []
    for row, col in sorted(grid):
        cell_id = pos_id(row, col)
        kind = grid[(row, col)]
        if kind == "number":
            value = values[(row, col)]
            cells.append(slot(cell_id, row, col, value) if (row, col) in slot_positions else fixed(cell_id, row, col, value))
        elif kind.startswith("operator:"):
            cells.append(op(cell_id, row, col, kind.split(":", 1)[1]))
        elif kind == "equals":
            cells.append(eq(cell_id, row, col))
        else:
            raise ValueError(f"Unknown cell kind: {kind}")
    return cells


def build_run_ids(runs: list[list[tuple[int, int]]]) -> list[list[str]]:
    return [[pos_id(row, col) for row, col in run] for run in runs]


def intersection_count(runs: list[list[tuple[int, int]]]) -> int:
    counts: dict[tuple[int, int], int] = {}
    for run in runs:
        for coord in (run[0], run[2], run[4]):
            counts[coord] = counts.get(coord, 0) + 1
    return sum(1 for count in counts.values() if count > 1)


def cycle_count(runs: list[list[tuple[int, int]]]) -> int:
    if not runs:
        return 0
    vertices = set()
    edges = set()
    for run in runs:
        vertices.update(run)
        edges.update(adjacent_pairs(run))
    return max(0, len(edges) - len(vertices) + 1)


def choose_slot_positions(
    rng: random.Random,
    profile: Profile,
    new_number_positions: list[tuple[int, int]],
) -> set[tuple[int, int]]:
    if not new_number_positions:
        return set()

    shuffled = list(new_number_positions)
    rng.shuffle(shuffled)
    chosen = {shuffled[0]}
    for coord in shuffled[1:]:
        if rng.random() < profile.extra_slot_probability:
            chosen.add(coord)
    return chosen


def single_step_solve_stats(puzzle: dict) -> dict:
    cells_by_id = {cell["id"]: cell for cell in puzzle["cells"]}
    unresolved_slots = {cell["id"] for cell in puzzle["cells"] if cell["type"] == "slot"}
    steps = 0

    while unresolved_slots:
        step_slots = set()
        for run in puzzle["runs"]:
            missing = [cell_id for cell_id in run if cell_id in unresolved_slots]
            if len(missing) == 1:
                step_slots.add(missing[0])
        if not step_slots:
            break
        unresolved_slots -= step_slots
        steps += 1

    slot_count = sum(1 for cell in cells_by_id.values() if cell["type"] == "slot")
    return {
        "solved_slots": slot_count - len(unresolved_slots),
        "stuck_slots": len(unresolved_slots),
        "steps": steps,
    }


def validate_difficulty_profile(puzzle: dict, profile: Profile) -> dict:
    slots = [cell for cell in puzzle["cells"] if cell["type"] == "slot"]
    two_digit_slots = sum(int(cell["solution"]) >= 10 for cell in slots)
    puzzle_cycle_count = puzzle["template_metadata"]["cycle_count"]
    single_step_stats = single_step_solve_stats(puzzle)

    if len(slots) < profile.min_slots:
        raise RuntimeError(f"{puzzle['id']}: expected at least {profile.min_slots} slots, found {len(slots)}")
    if profile.max_slots and len(slots) > profile.max_slots:
        raise RuntimeError(f"{puzzle['id']}: expected at most {profile.max_slots} slots, found {len(slots)}")
    if two_digit_slots < profile.min_two_digit_slots:
        raise RuntimeError(
            f"{puzzle['id']}: expected at least {profile.min_two_digit_slots} two-digit slots, found {two_digit_slots}"
        )
    if puzzle_cycle_count < profile.min_cycle_count:
        raise RuntimeError(
            f"{puzzle['id']}: expected at least {profile.min_cycle_count} cycles, found {puzzle_cycle_count}"
        )
    if single_step_stats["stuck_slots"] < profile.min_single_step_stuck_slots:
        raise RuntimeError(
            f"{puzzle['id']}: expected at least {profile.min_single_step_stuck_slots} non-single-step slots, "
            f"found {single_step_stats['stuck_slots']}"
        )

    return {
        "two_digit_slot_count": two_digit_slots,
        "single_step_solved_slots": single_step_stats["solved_slots"],
        "single_step_stuck_slots": single_step_stats["stuck_slots"],
        "single_step_steps": single_step_stats["steps"],
    }


def add_run(
    *,
    rng: random.Random,
    profile: Profile,
    grid: dict[tuple[int, int], str],
    runs: list[list[tuple[int, int]]],
    run_edges: set[frozenset[tuple[int, int]]],
    values: dict[tuple[int, int], int],
    slot_positions: set[tuple[int, int]],
    anchor: tuple[int, int] | None,
    prefer_loop: bool = False,
) -> bool:
    attempts = 180 if prefer_loop else 80
    for _ in range(attempts):
        operator_value = rng.choice(profile.operators)
        anchor_index = rng.choice(tuple(NUMBER_POSITIONS)) if anchor else None
        orientation = rng.choice(("h", "v"))
        coords = candidate_coords(anchor, orientation, anchor_index) if anchor else candidate_coords((profile.rows // 2, profile.cols // 2), "h", 2)
        if not in_bounds(coords, profile):
            continue
        if anchor and coords[anchor_index] != anchor:
            continue

        overlaps = {coord for coord in coords if coord in grid}
        if anchor and anchor not in overlaps:
            continue
        if not anchor and overlaps:
            continue
        if prefer_loop and len(overlaps) != 2:
            continue
        if not prefer_loop and len(overlaps) != (1 if anchor else 0):
            continue
        if any(coords.index(coord) not in NUMBER_POSITIONS for coord in overlaps):
            continue

        if not can_place_run(coords=coords, operator_value=operator_value, grid=grid, run_edges=run_edges, allowed_overlaps=overlaps):
            continue

        fixed_values = {coords.index(coord): values[coord] for coord in overlaps}
        run_values = solve_run_values(
            rng=rng,
            operator_value=operator_value,
            fixed_values=fixed_values,
            profile=profile,
        )
        if not run_values:
            continue

        for index, coord in enumerate(coords):
            grid[coord] = token_type(index, operator_value)
        for index, coord in zip((0, 2, 4), (coords[0], coords[2], coords[4])):
            values[coord] = run_values[(0, 2, 4).index(index)]

        new_number_positions = [coord for coord in (coords[0], coords[2], coords[4]) if coord not in overlaps]
        slot_positions.update(choose_slot_positions(rng, profile, new_number_positions))
        runs.append(coords)
        run_edges.update(adjacent_pairs(coords))
        return True
    return False


def generate_template_puzzle(difficulty: str, puzzle_id: str, seed: int, attempts: int = 50) -> dict:
    last_error: Exception | None = None
    for attempt in range(attempts):
        attempt_seed = seed + attempt * 10000
        try:
            puzzle = generate_template_puzzle_once(difficulty, puzzle_id, attempt_seed)
            puzzle["template_metadata"]["base_seed"] = seed
            puzzle["template_metadata"]["attempt"] = attempt + 1
            return puzzle
        except (RuntimeError, ValueError) as error:
            last_error = error
    raise RuntimeError(f"Could not generate {difficulty} template from seed {seed}: {last_error}")


def generate_template_puzzle_once(difficulty: str, puzzle_id: str, seed: int) -> dict:
    profile = PROFILES[difficulty]
    rng = random.Random(seed)
    grid: dict[tuple[int, int], str] = {}
    runs: list[list[tuple[int, int]]] = []
    run_edges: set[frozenset[tuple[int, int]]] = set()
    values: dict[tuple[int, int], int] = {}
    slot_positions: set[tuple[int, int]] = set()

    if not add_run(
        rng=rng,
        profile=profile,
        grid=grid,
        runs=runs,
        run_edges=run_edges,
        values=values,
        slot_positions=slot_positions,
        anchor=None,
    ):
        raise RuntimeError("Could not place seed run")

    retries = 0
    loop_attempts = 0
    while len(runs) < profile.target_runs and retries < 1000:
        anchors = [coord for coord, kind in grid.items() if kind == "number"]
        anchor = rng.choice(anchors)
        prefer_loop = len(runs) >= 3 and rng.random() < profile.loop_probability
        if not add_run(
            rng=rng,
            profile=profile,
            grid=grid,
            runs=runs,
            run_edges=run_edges,
            values=values,
            slot_positions=slot_positions,
            anchor=anchor,
            prefer_loop=prefer_loop,
        ):
            retries += 1
            if prefer_loop:
                loop_attempts += 1

    if len(runs) < profile.target_runs:
        raise RuntimeError(f"Could only place {len(runs)} of {profile.target_runs} runs")

    grid, runs, values, slot_positions, rows, cols = normalize(grid, runs, values, slot_positions)
    cells = build_cells(grid, values, slot_positions)
    puzzle = make_puzzle(
        puzzle_id=puzzle_id,
        difficulty=difficulty,
        rows=rows,
        cols=cols,
        template_id=f"walk_{difficulty}_{seed}",
        cells=cells,
        runs=build_run_ids(runs),
        seed=seed,
    )
    puzzle["template_metadata"] = {
        "algorithm": "walk",
        "run_count": len(runs),
        "intersection_count": intersection_count(runs),
        "cycle_count": cycle_count(runs),
        "slot_count": len(slot_positions),
        "footprint": {"rows": rows, "cols": cols},
        "retry_count": retries,
        "loop_retry_count": loop_attempts,
    }
    difficulty_metadata = validate_difficulty_profile(puzzle, profile)
    puzzle["template_metadata"].update(difficulty_metadata)
    validate_template_structure(puzzle)
    validate_inventory(puzzle)
    validate_solution(puzzle)
    puzzle["solution_count"] = count_solutions(puzzle, limit=2)
    if puzzle["solution_count"] != 1:
        raise RuntimeError(f"{puzzle_id}: expected 1 solution, found {puzzle['solution_count']}")
    return puzzle


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one algorithmic CrossMath template puzzle.")
    parser.add_argument("--difficulty", choices=tuple(PROFILES), required=True)
    parser.add_argument("--seed", type=int, default=20260421)
    parser.add_argument("--id", default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    puzzle_id = args.id or f"walk-{args.difficulty}-{args.seed}"
    puzzle = generate_template_puzzle(args.difficulty, puzzle_id, args.seed)
    content = json.dumps(puzzle, indent=2) + "\n"
    if args.out:
        args.out.write_text(content, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
