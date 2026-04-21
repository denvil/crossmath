const STORAGE_KEYS = {
  currentPuzzleId: "crossmath.currentPuzzleId",
  currentPuzzle: "crossmath.currentPuzzle",
  currentProgress: "crossmath.currentProgress",
  settings: "crossmath.settings",
};
const RECENT_HISTORY_LIMIT = 10;
const DIFFICULTIES = ["easy", "medium", "hard"];

let puzzle = null;
let cellById = new Map();
let cellByPosition = new Map();

const state = {
  tiles: [],
  placements: {},
  selectedTileId: null,
  checked: false,
  difficulty: "medium",
  solved: false,
  revealed: false,
};

const boardEl = document.querySelector("#board");
const trayEl = document.querySelector("#tray");
const statusEl = document.querySelector("#status");
const trayHintEl = document.querySelector("#trayHint");
const puzzleMetaEl = document.querySelector("#puzzleMeta");
const resetButton = document.querySelector("#resetButton");
const revealButton = document.querySelector("#revealButton");
const checkButton = document.querySelector("#checkButton");
const difficultyButtons = Array.from(document.querySelectorAll(".difficulty-button"));

const dragState = {
  tileId: null,
  startX: 0,
  startY: 0,
  active: false,
  ghost: null,
  overCellId: null,
  suppressClick: false,
};

function puzzleCounts() {
  return window.PUZZLE_COUNTS || { easy: 1, medium: 1, hard: 1 };
}

function formatPuzzleNumber(index) {
  return String(index).padStart(4, "0");
}

function buildPuzzlePath(difficulty, index) {
  return `puzzles/${difficulty}-${formatPuzzleNumber(index)}.json`;
}

function defaultSettings() {
  return {
    difficulty: "medium",
    recentByDifficulty: Object.fromEntries(DIFFICULTIES.map((difficulty) => [difficulty, []])),
    solvedByDifficulty: Object.fromEntries(DIFFICULTIES.map((difficulty) => [difficulty, 0])),
  };
}

function mergeSettings(settings) {
  const fallback = defaultSettings();
  return {
    ...fallback,
    ...settings,
    recentByDifficulty: {
      ...fallback.recentByDifficulty,
      ...(settings.recentByDifficulty || {}),
    },
    solvedByDifficulty: {
      ...fallback.solvedByDifficulty,
      ...(settings.solvedByDifficulty || {}),
    },
  };
}

function normalizePuzzle(payload) {
  return {
    id: payload.id,
    version: payload.version,
    difficulty: payload.difficulty,
    rows: payload.rows,
    cols: payload.cols,
    templateId: payload.template_id || payload.templateId,
    solutionCount: payload.solution_count || payload.solutionCount,
    cells: payload.cells,
    tray: payload.tray,
    solution: payload.solution || {},
  };
}

function setPuzzle(nextPuzzle, restoredProgress = null) {
  puzzle = normalizePuzzle(nextPuzzle);
  cellById = new Map(puzzle.cells.map((cell) => [cell.id, cell]));
  cellByPosition = new Map(puzzle.cells.map((cell) => [`${cell.row}:${cell.col}`, cell]));

  state.difficulty = puzzle.difficulty;
  state.tiles = puzzle.tray.map((tile) => ({ ...tile }));
  state.placements = {};
  state.selectedTileId = null;
  state.checked = false;
  state.solved = false;
  state.revealed = false;

  if (restoredProgress && restoredProgress.puzzleId === puzzle.id) {
    state.tiles = restoredProgress.tiles.map((tile) => ({ ...tile }));
    state.placements = { ...restoredProgress.placements };
    state.difficulty = restoredProgress.difficulty || puzzle.difficulty;
    state.solved = Boolean(restoredProgress.solved);
    state.revealed = Boolean(restoredProgress.revealed);
  }

  saveProgress();
  render();
}

async function loadRandomPuzzle(difficulty) {
  const count = puzzleCounts()[difficulty] || 0;

  if (count < 1) {
    setStatus(`No ${difficulty} puzzles available.`);
    return;
  }

  const index = choosePuzzleIndex(difficulty, count);
  const path = buildPuzzlePath(difficulty, index);

  setStatus(`Loading ${difficulty} puzzle.`);

  try {
    const response = await fetch(path, { cache: "no-store" });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    clearSavedProgress();
    rememberPuzzle(difficulty, payload.id);
    setPuzzle(payload);
    saveSettings();
    setStatus("Select a tile to begin.");
  } catch (error) {
    setStatus(`Could not load ${path}.`);
    console.error(error);
  }
}

function choosePuzzleIndex(difficulty, count) {
  const settings = savedSettings();
  const recentIds = settings.recentByDifficulty[difficulty] || [];
  const availableIndexes = [];

  for (let index = 1; index <= count; index += 1) {
    const puzzleId = `${difficulty}-${formatPuzzleNumber(index)}`;
    if (!recentIds.includes(puzzleId)) {
      availableIndexes.push(index);
    }
  }

  const choices = availableIndexes.length > 0 ? availableIndexes : Array.from({ length: count }, (_, index) => index + 1);
  return choices[Math.floor(Math.random() * choices.length)];
}

function rememberPuzzle(difficulty, puzzleId) {
  const settings = savedSettings();
  const recent = settings.recentByDifficulty[difficulty] || [];
  settings.recentByDifficulty[difficulty] = [puzzleId, ...recent.filter((id) => id !== puzzleId)].slice(0, RECENT_HISTORY_LIMIT);
  settings.difficulty = difficulty;
  saveSettings(settings);
}

function recordSolvedPuzzle() {
  if (!puzzle || state.solved || state.revealed) {
    return;
  }

  const settings = savedSettings();
  settings.solvedByDifficulty[state.difficulty] = (settings.solvedByDifficulty[state.difficulty] || 0) + 1;
  settings.difficulty = state.difficulty;
  state.solved = true;
  saveSettings(settings);
  saveProgress();
}

function saveSettings(settings = null) {
  const nextSettings = mergeSettings(settings || savedSettings());
  localStorage.setItem(
    STORAGE_KEYS.settings,
    JSON.stringify({
      ...nextSettings,
      difficulty: nextSettings.difficulty || state.difficulty,
      savedAt: Date.now(),
    }),
  );
}

function savedSettings() {
  try {
    return mergeSettings(JSON.parse(localStorage.getItem(STORAGE_KEYS.settings)) || {});
  } catch {
    return defaultSettings();
  }
}

function saveProgress() {
  if (!puzzle) {
    return;
  }

  localStorage.setItem(STORAGE_KEYS.currentPuzzleId, puzzle.id);
  localStorage.setItem(STORAGE_KEYS.currentPuzzle, JSON.stringify(puzzle));
  localStorage.setItem(
    STORAGE_KEYS.currentProgress,
    JSON.stringify({
      puzzleId: puzzle.id,
      placements: state.placements,
      tiles: state.tiles,
      difficulty: state.difficulty,
      solved: state.solved,
      revealed: state.revealed,
      savedAt: Date.now(),
    }),
  );
}

function clearSavedProgress() {
  localStorage.removeItem(STORAGE_KEYS.currentPuzzleId);
  localStorage.removeItem(STORAGE_KEYS.currentPuzzle);
  localStorage.removeItem(STORAGE_KEYS.currentProgress);
}

function restoreSavedPuzzle() {
  try {
    const savedPuzzle = JSON.parse(localStorage.getItem(STORAGE_KEYS.currentPuzzle));
    const savedProgress = JSON.parse(localStorage.getItem(STORAGE_KEYS.currentProgress));

    if (!savedPuzzle || !savedProgress || savedPuzzle.id !== savedProgress.puzzleId) {
      return false;
    }

    setPuzzle(savedPuzzle, savedProgress);
    setStatus("Restored saved puzzle.");
    return true;
  } catch {
    clearSavedProgress();
    return false;
  }
}

function isCompactBoard() {
  return puzzle && puzzle.cols > 9;
}

function tileById(tileId) {
  return state.tiles.find((tile) => tile.id === tileId);
}

function placedTileForCell(cellId) {
  const tileId = state.placements[cellId];
  return tileId ? tileById(tileId) : null;
}

function placeTile(tileId, cellId) {
  const tile = tileById(tileId);
  const cell = cellById.get(cellId);

  if (!tile || !cell || cell.type !== "slot" || state.placements[cellId]) {
    return;
  }

  tile.used = true;
  tile.placedCellId = cellId;
  state.placements[cellId] = tile.id;
  state.selectedTileId = null;
  state.checked = false;
  saveProgress();
  setStatus("Placed tile.");
  render();
}

function removeTileFromCell(cellId) {
  const tile = placedTileForCell(cellId);

  if (!tile) {
    return;
  }

  tile.used = false;
  tile.placedCellId = null;
  delete state.placements[cellId];
  state.selectedTileId = null;
  state.checked = false;
  saveProgress();
  setStatus("Returned tile to tray.");
  render();
}

function handleSlotTap(cellId) {
  if (state.placements[cellId]) {
    removeTileFromCell(cellId);
    return;
  }

  if (!state.selectedTileId) {
    setStatus("Select a tray tile first.");
    return;
  }

  placeTile(state.selectedTileId, cellId);
}

function handleTileTap(tileId) {
  if (dragState.suppressClick) {
    dragState.suppressClick = false;
    return;
  }

  const tile = tileById(tileId);

  if (!tile || tile.used) {
    return;
  }

  state.selectedTileId = state.selectedTileId === tileId ? null : tileId;
  state.checked = false;
  setStatus(state.selectedTileId ? `Selected ${tile.value}.` : "Selection cleared.");
  render();
}

function revealSolution() {
  if (!puzzle) {
    return;
  }

  state.tiles = puzzle.tray.map((tile) => ({ ...tile }));
  state.placements = {};

  for (const cell of puzzle.cells.filter((item) => item.type === "slot")) {
    const tile = state.tiles.find((item) => !item.used && item.value === cell.solution);
    if (!tile) {
      setStatus("Could not reveal solution.");
      return;
    }
    tile.used = true;
    tile.placedCellId = cell.id;
    state.placements[cell.id] = tile.id;
  }

  state.selectedTileId = null;
  state.checked = true;
  state.solved = false;
  state.revealed = true;
  saveProgress();
  setStatus("Solution revealed.");
  render();
}

function resetPuzzle() {
  if (!puzzle) {
    return;
  }

  state.tiles = puzzle.tray.map((tile) => ({ ...tile }));
  state.placements = {};
  state.selectedTileId = null;
  state.checked = false;
  saveProgress();
  setStatus("Puzzle reset.");
  render();
}

function checkPuzzle() {
  if (!puzzle) {
    return;
  }

  const slots = puzzle.cells.filter((cell) => cell.type === "slot");
  const emptyCount = slots.filter((cell) => !state.placements[cell.id]).length;

  state.checked = true;

  if (emptyCount > 0) {
    setStatus(`${emptyCount} slot${emptyCount === 1 ? "" : "s"} still empty.`);
    render();
    return;
  }

  const mistakes = slots.filter((cell) => placedTileForCell(cell.id)?.value !== cell.solution);

  if (mistakes.length === 0) {
    recordSolvedPuzzle();
    setStatus("Solved.");
  } else {
    setStatus(`${mistakes.length} tile${mistakes.length === 1 ? "" : "s"} need another look.`);
  }

  render();
}

function setStatus(message) {
  statusEl.textContent = message;
}

function cellClasses(cell) {
  const compact = isCompactBoard();
  const isSymbol = cell.type === "operator" || cell.type === "equals";
  const base = [
    "board-cell",
    "flex",
    "aspect-square",
    "items-center",
    "justify-center",
    "rounded-md",
    compact && isSymbol ? "text-base" : compact ? "text-[0.8rem]" : "text-lg",
    "font-black",
    compact && isSymbol ? "sm:text-lg" : compact ? "sm:text-sm" : "sm:text-xl",
  ];

  if (cell.type === "slot") {
    const tile = placedTileForCell(cell.id);
    const isCorrect = state.checked && tile && tile.value === cell.solution;
    const isWrong = state.checked && tile && tile.value !== cell.solution;
    const isDragOver = dragState.overCellId === cell.id && !tile;

    base.push(
      compact ? "border" : "border-2",
      "shadow-sm",
      "transition",
      "active:translate-y-px",
      tile ? "bg-white" : "slot-empty bg-amber-50 text-amber-800",
      state.selectedTileId && !tile ? "border-emerald-600" : "border-slate-300",
    );

    if (isDragOver) {
      base.push("border-emerald-700", "bg-emerald-100", "ring-2", "ring-emerald-500");
    }

    if (isCorrect) {
      base.push("border-emerald-600", "bg-emerald-50", "text-emerald-900");
    }

    if (isWrong) {
      base.push("border-rose-600", "bg-rose-50", "text-rose-900");
    }
  } else {
    base.push("border", "border-slate-300", "bg-amber-50", "text-slate-950", "shadow-sm");
  }

  return base.join(" ");
}

function renderBoard() {
  boardEl.replaceChildren();

  if (!puzzle) {
    return;
  }

  boardEl.style.setProperty("--board-cols", puzzle.cols);
  boardEl.style.setProperty("--board-gap", isCompactBoard() ? "2px" : "6px");
  boardEl.style.setProperty("--board-gap-wide", isCompactBoard() ? "4px" : "8px");

  for (let row = 0; row < puzzle.rows; row += 1) {
    for (let col = 0; col < puzzle.cols; col += 1) {
      const cell = cellByPosition.get(`${row}:${col}`);
      const el = document.createElement(cell?.type === "slot" ? "button" : "div");

      if (!cell) {
        el.className = "aspect-square";
        boardEl.appendChild(el);
        continue;
      }

      el.className = cellClasses(cell);

      if (cell.type === "slot") {
        const tile = placedTileForCell(cell.id);
        el.type = "button";
        el.dataset.cellId = cell.id;
        el.setAttribute("aria-label", tile ? `Slot filled with ${tile.value}. Tap to remove.` : "Empty slot");
        el.addEventListener("click", () => handleSlotTap(cell.id));
        el.textContent = tile ? tile.value : "";
      } else {
        el.textContent = cell.value;
      }

      boardEl.appendChild(el);
    }
  }
}

function renderTray() {
  trayEl.replaceChildren();

  state.tiles.forEach((tile) => {
    const button = document.createElement("button");
    const isSelected = state.selectedTileId === tile.id;
    const classes = [
      "tray-tile",
      "flex",
      "min-h-12",
      "items-center",
      "justify-center",
      "rounded-md",
      "border-2",
      "text-lg",
      "font-black",
      "shadow-sm",
      "transition",
      "active:translate-y-px",
    ];

    if (tile.used) {
      classes.push("border-slate-200", "bg-slate-100", "text-slate-300");
      button.disabled = true;
    } else if (isSelected) {
      classes.push("border-emerald-700", "bg-emerald-700", "text-white");
    } else {
      classes.push("border-slate-300", "bg-white", "text-slate-950");
    }

    button.type = "button";
    button.className = classes.join(" ");
    button.textContent = tile.value;
    button.dataset.tileId = tile.id;
    button.setAttribute("aria-pressed", String(isSelected));
    button.setAttribute("aria-label", `Tile ${tile.value}`);
    button.addEventListener("pointerdown", (event) => handleTilePointerDown(event, tile.id));
    button.addEventListener("click", () => handleTileTap(tile.id));
    trayEl.appendChild(button);
  });
}

function handleTilePointerDown(event, tileId) {
  const tile = tileById(tileId);

  if (!tile || tile.used || event.button !== 0) {
    return;
  }

  dragState.tileId = tileId;
  dragState.startX = event.clientX;
  dragState.startY = event.clientY;
  dragState.active = false;
  dragState.overCellId = null;
  dragState.suppressClick = false;

  window.addEventListener("pointermove", handleTilePointerMove);
  window.addEventListener("pointerup", handleTilePointerUp, { once: true });
  window.addEventListener("pointercancel", cancelDrag, { once: true });
}

function handleTilePointerMove(event) {
  if (!dragState.tileId) {
    return;
  }

  const distance = Math.hypot(event.clientX - dragState.startX, event.clientY - dragState.startY);
  if (!dragState.active && distance < 8) {
    return;
  }

  event.preventDefault();

  if (!dragState.active) {
    startDragGhost(event);
  }

  moveDragGhost(event.clientX, event.clientY);
  updateDragTarget(event.clientX, event.clientY);
}

function handleTilePointerUp(event) {
  window.removeEventListener("pointermove", handleTilePointerMove);

  if (!dragState.tileId) {
    clearDragState();
    return;
  }

  if (dragState.active) {
    dragState.suppressClick = true;
    updateDragTarget(event.clientX, event.clientY);
    if (dragState.overCellId) {
      placeTile(dragState.tileId, dragState.overCellId);
    } else {
      setStatus("Drop on an empty slot.");
    }
  }

  clearDragState();
  render();
}

function startDragGhost(event) {
  const tile = tileById(dragState.tileId);
  const ghost = document.createElement("div");
  ghost.className = "drag-ghost flex h-12 w-12 items-center justify-center rounded-md border-2 border-emerald-700 bg-emerald-700 text-lg font-black text-white shadow-xl";
  ghost.textContent = tile.value;
  document.body.appendChild(ghost);
  dragState.active = true;
  dragState.ghost = ghost;
  moveDragGhost(event.clientX, event.clientY);
}

function moveDragGhost(x, y) {
  if (!dragState.ghost) {
    return;
  }
  dragState.ghost.style.left = `${x}px`;
  dragState.ghost.style.top = `${y}px`;
}

function updateDragTarget(x, y) {
  if (dragState.ghost) {
    dragState.ghost.hidden = true;
  }
  const target = document.elementFromPoint(x, y)?.closest("[data-cell-id]");
  if (dragState.ghost) {
    dragState.ghost.hidden = false;
  }
  const cellId = target?.dataset.cellId || null;
  dragState.overCellId = cellId && !state.placements[cellId] ? cellId : null;
  render();
}

function cancelDrag() {
  window.removeEventListener("pointermove", handleTilePointerMove);
  clearDragState();
  render();
}

function clearDragState() {
  dragState.tileId = null;
  dragState.startX = 0;
  dragState.startY = 0;
  dragState.active = false;
  dragState.overCellId = null;

  if (dragState.ghost) {
    dragState.ghost.remove();
    dragState.ghost = null;
  }
}

function renderHint() {
  const remaining = state.tiles.filter((tile) => !tile.used).length;

  if (state.selectedTileId) {
    const tile = tileById(state.selectedTileId);
    trayHintEl.textContent = `Place ${tile.value}`;
    return;
  }

  trayHintEl.textContent = remaining === 0 ? "Tray empty" : "Tap a tile, then a slot";
}

function renderMeta() {
  if (!puzzle) {
    puzzleMetaEl.textContent = "";
    return;
  }

  const slots = puzzle.cells.filter((cell) => cell.type === "slot").length;
  const solvedCount = savedSettings().solvedByDifficulty[state.difficulty] || 0;
  puzzleMetaEl.textContent = `${puzzle.id} - ${slots} slots - solved ${solvedCount}`;
}

function renderDifficultyButtons() {
  difficultyButtons.forEach((button) => {
    const isActive = button.dataset.difficulty === state.difficulty;
    button.classList.toggle("bg-slate-900", isActive);
    button.classList.toggle("text-white", isActive);
    button.classList.toggle("bg-white", !isActive);
    button.classList.toggle("text-slate-800", !isActive);
  });
}

function render() {
  renderMeta();
  renderBoard();
  renderTray();
  renderHint();
  renderDifficultyButtons();
}

difficultyButtons.forEach((button) => {
  button.addEventListener("click", () => {
    loadRandomPuzzle(button.dataset.difficulty);
  });
});

resetButton.addEventListener("click", resetPuzzle);
revealButton.addEventListener("click", revealSolution);
checkButton.addEventListener("click", checkPuzzle);

if (!restoreSavedPuzzle()) {
  loadRandomPuzzle(savedSettings().difficulty || "medium");
}
