# CrossMath

Static, mobile-first CrossMath-style puzzle website. The browser app is plain HTML, Tailwind via CDN, and vanilla JavaScript. Puzzle generation happens offline with Python, and exported puzzle JSON files are served as static assets.

## Current Status

Phase 3 has static puzzle loading, persistence, and offline puzzle tooling. The site loads JSON puzzles from `puzzles/`, uses `puzzle-counts.js`, keeps exact consumable tray tiles, and saves current progress in `localStorage`.

`SPECS.md` remains the source of truth, and `TODO.md` tracks the planned build order and play-testing checkpoints.

## Planned File Layout

```text
.
|-- SPECS.md
|-- TODO.md
|-- README.md
|-- index.html
|-- app.js
|-- puzzle-counts.js
|-- puzzles/
|   |-- easy-0001.json
|   |-- medium-0001.json
|   `-- hard-0001.json
`-- tools/
    |-- generate_puzzles.py
    |-- solver.py
    |-- templates.py
    `-- export_counts.py
```

## Requirements

- A browser with JavaScript enabled.
- Python 3.11+ for offline puzzle tooling.
- `uv` for running Python tools.
- Any static file server for local development.
- nginx or equivalent static hosting for deployment.

The website itself must not require a build step, backend, API route, or server-side rendering.

## Local Static Server

Run from the repo root:

```powershell
python -m http.server 8080
```

Then open:

```text
http://localhost:8080/
```

PowerShell alternative if Python is not on `PATH`:

```powershell
py -m http.server 8080
```

## Puzzle Tooling Commands

Run these commands from the repo root.

Generate a small development puzzle set:

```powershell
uv run tools/generate_puzzles.py --difficulty easy --count 10 --out puzzles
```

Generate one puzzle for each difficulty:

```powershell
uv run tools/generate_puzzles.py --difficulty all --count 1 --out puzzles --counts-out puzzle-counts.js
```

Generate three test puzzles for each difficulty:

```powershell
uv run tools/generate_puzzles.py --difficulty all --count 3 --out puzzles --counts-out puzzle-counts.js
```

Generate six diversified test puzzles for each difficulty:

```powershell
uv run tools/generate_puzzles.py --difficulty all --count 6 --out puzzles --counts-out puzzle-counts.js
```

Generate twelve diversified test puzzles for each difficulty, enough for the 10-round no-repeat window:

```powershell
uv run tools/generate_puzzles.py --difficulty all --count 12 --out puzzles --counts-out puzzle-counts.js
```

The generator chooses from multiple validated template variants per difficulty using deterministic seed-based selection.

The walking generator can also close loops by placing runs through two existing number cells. Generated metadata includes run count, intersection count, cycle count, slot count, footprint, retry count, base seed, and attempt number.

Generate an experimental set using the walking template generator:

```powershell
uv run tools/generate_puzzles.py --difficulty all --count 3 --out puzzles --counts-out puzzle-counts.js --template-source walk
```

Generate one walking-template puzzle directly:

```powershell
uv run tools/template_generator.py --difficulty hard --seed 303 --out puzzles/hard-walk.json
```

Generate all v1 puzzle sets:

```powershell
uv run tools/generate_puzzles.py --difficulty easy --count 120 --out puzzles
uv run tools/generate_puzzles.py --difficulty medium --count 90 --out puzzles
uv run tools/generate_puzzles.py --difficulty hard --count 60 --out puzzles
```

Export puzzle counts for the frontend:

```powershell
uv run tools/export_counts.py --puzzles puzzles --out puzzle-counts.js
```

Validate exported puzzles:

```powershell
uv run tools/solver.py --validate puzzles
```

Validation enforces:

- every equation run is a contiguous 5-cell row or column
- every rendered cell belongs to at least one run
- all rendered cells form one orthogonally connected board
- every adjacent rendered cell pair is consecutive inside an equation run
- division uses whole-number results only
- tray inventory exactly matches missing slot values
- each exported puzzle has exactly one solution

## Expected Browser Behavior

- Load static puzzle JSON files from `puzzles/`.
- Use exact consumable tray tiles.
- Treat duplicate numbers as separate tile objects with unique ids.
- Support tap-select and tap-place as the primary mobile interaction.
- Support pointer drag and drop as an enhancement.
- Reveal the current solution without incrementing solved counts.
- Save current puzzle progress in `localStorage`.
- Restore the exact board and tray state after reload.
- Avoid recently loaded puzzles per difficulty for up to 10 rounds when enough puzzle files exist.
- Persist solved counts per difficulty.

## Deployment

Deploy the repo contents as static files. Example nginx location:

```nginx
location / {
    root /var/www/crossmath;
    try_files $uri $uri/ =404;
}
```

Puzzle files must be reachable as plain static assets, for example:

```text
/puzzles/easy-0001.json
```
