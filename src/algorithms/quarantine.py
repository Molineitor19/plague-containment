"""
quarantine.py  —  Plague Containment  —  Team 16
════════════════════════════════════════════════════════════════════════════
Algorithms 2 & 3 — Backtracking Quarantine

Finds a set of HEALTHY border districts to quarantine such that:
  1. Full enclosure  — every infected district has no free healthy neighbor.
  2. No isolation    — all remaining healthy districts stay connected.
════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from collections import deque
from typing import Optional
from algorithms.common import District, INFECTED, HEALTHY, QUARANTINED, GRID_SIZE, get_neighbors


# ─────────────────────────────────────────────────────────────
#  Constraint Checks
# ─────────────────────────────────────────────────────────────

def _is_fully_enclosed(grid: list[list[District]]) -> bool:
    """
    Condition 1 — Full enclosure.

    Returns True iff every INFECTED district has NO HEALTHY neighbor.
    A QUARANTINED or VACCINATED neighbor counts as blocking; a HEALTHY
    neighbor means the containment ring is still open somewhere.
    """
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if grid[row][col].state == INFECTED:
                for n in get_neighbors(grid, row, col):
                    if n.state == HEALTHY:
                        return False   # open exit found — not enclosed
    return True


def _is_healthy_connected(grid: list[list[District]]) -> bool:
    """
    Condition 2 — No isolation.

    Returns True iff all HEALTHY districts form a single connected component.
    Uses a BFS reachability check from the first healthy cell found.
    Returns True vacuously when there are no healthy districts.

    Complexity: O(n)  — at most one full BFS over the 8x8 grid.
    """
    healthy: list[tuple[int, int]] = [
        (r, c)
        for r in range(GRID_SIZE)
        for c in range(GRID_SIZE)
        if grid[r][c].state == HEALTHY
    ]

    if not healthy:
        return True   # no healthy districts — trivially satisfied

    # BFS from the first healthy cell
    start = healthy[0]
    visited: set[tuple[int, int]] = {start}
    queue: deque[tuple[int, int]] = deque([start])

    while queue:
        r, c = queue.popleft()
        for n in get_neighbors(grid, r, c):
            key = (n.row, n.col)
            if n.state == HEALTHY and key not in visited:
                visited.add(key)
                queue.append(key)

    # Every healthy cell must be reachable from the start
    return len(visited) == len(healthy)


# ─────────────────────────────────────────────────────────────
#  Algorithm 3 — Recursive Backtracking Step
# ─────────────────────────────────────────────────────────────

def _search(
    grid: list[list[District]],
    border: list[District],
    i: int,
    quarantine: set[District],
) -> bool:
    """
    Algorithm 3 — Search, recursive backtracking step.

    For each border district starting at index i, two choices are tried:
      Option A — quarantine the district, verify both constraints, recurse.
      Option B — skip the district (do not quarantine it), recurse.

    The grid is modified in-place but is always restored on backtrack.
    If this function returns True, the districts in *quarantine* are the
    solution and are left marked QUARANTINED in the grid.

    Parameters
    ----------
    grid       : city grid — modified temporarily, always restored on backtrack.
    border     : ordered list of candidate border districts.
    i          : index of the district currently being decided.
    quarantine : partial solution accumulated so far (modified in-place).

    Returns
    -------
    True  — a valid complete quarantine was found.
    False — no solution reachable from this branch; grid is fully restored.
    """

    # ── Base case A: infected zone is fully enclosed → solution found ────────
    if _is_fully_enclosed(grid):
        return True

    # ── Base case B: no more candidates without full enclosure → dead end ────
    if i >= len(border):
        return False

    d = border[i]

    # ────────────────────────────────────────────────────────────────────────
    #  Option A: quarantine district d
    # ────────────────────────────────────────────────────────────────────────
    quarantine.add(d)
    d.state = QUARANTINED                             # temporary grid change

    if _is_healthy_connected(grid):                   # condition 2 check
        if _search(grid, border, i + 1, quarantine):  # recurse
            return True                               # propagate success upward

    # ── Backtrack: undo the quarantine of d ─────
    quarantine.discard(d)
    d.state = HEALTHY                                 # restore grid cell

    # ────────────────────────────────────────────────────────────────────────
    #  Option B: skip district d
    # ────────────────────────────────────────────────────────────────────────
    if _search(grid, border, i + 1, quarantine):
        return True

    return False   # both options exhausted — dead end on this branch


# ═════════════════════════════════════════════════════════════
#  Algorithm 2 — Backtracking Quarantine Entry Point
# ═════════════════════════════════════════════════════════════

def backtracking_quarantine(
    grid: list[list[District]],
) -> Optional[set[District]]:
    """
    Backtracking Quarantine Algorithm — entry point.

    Finds the minimal set of HEALTHY border districts to quarantine such that:
      1. Full enclosure  — no infected cell has a free healthy neighbor.
      2. No isolation    — every remaining healthy district stays reachable.

    Parameters
    ----------
    grid : 8x8 matrix of District objects.
           Modified temporarily during the search; fully restored if no
           solution exists.  On success, quarantined districts are left
           marked QUARANTINED in the grid.

    Returns
    -------
    set of District objects forming the valid quarantine perimeter, or None
    if no valid quarantine exists.

    Complexity
    ----------
    Worst case O(2^b · n)  where b = |border|, n = 64.
    The connectivity check (condition 2) prunes most branches early, keeping
    the search fast for typical infection patterns on an 8x8 board.
    """

    # ── Step 1: collect border = healthy neighbors of all infected cells ─────
    # (Algorithm 2, line 1)
    border: list[District] = []
    seen: set[tuple[int, int]] = set()

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            d = grid[row][col]
            if d.state == INFECTED:
                for n in get_neighbors(grid, row, col):
                    if n.state == HEALTHY and (n.row, n.col) not in seen:
                        border.append(n)
                        seen.add((n.row, n.col))

    # ── Step 2: run the recursive search  (Algorithm 2, lines 2–3) ──────────
    quarantine: set[District] = set()
    success = _search(grid, border, 0, quarantine)

    # ── Step 3: return result  (Algorithm 2, lines 4–8) ─────────────────────
    if success:
        return quarantine   # districts already marked QUARANTINED in grid
    else:
        return None         # grid fully restored by backtracking