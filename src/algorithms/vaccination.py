"""
vaccination.py  —  Plague Containment  —  Team 16
════════════════════════════════════════════════════════════════════════════
Algorithm 1 — Greedy Vaccination

Strategy: scan the infection border and recommend the HEALTHY district
with the highest risk level for immediate vaccination.
════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from typing import Optional
from common import District, INFECTED, HEALTHY, VACCINATED, GRID_SIZE, get_neighbors


# ═════════════════════════════════════════════════════════════
#  Algorithm 1 — Greedy Vaccination
# ═════════════════════════════════════════════════════════════

def greedy_vaccination(grid: list[list[District]]) -> Optional[District]:
    """
    Greedy Vaccination Algorithm.

    Strategy
    --------
    1. Collect every HEALTHY district that shares at least one side with an
       INFECTED district — the "infection border".
    2. Return the border district with the highest risk level.
       Ties are broken by scan order (top-to-bottom, left-to-right).

    Parameters
    ----------
    grid : 8x8 matrix of District objects (not modified).

    Returns
    -------
    The highest-risk HEALTHY border District, or None if no candidates exist
    (infection is fully blocked or there are no infected districts).

    Complexity
    ----------
    O(n)  where n = GRID_SIZE^2 = 64.  Single pass over the entire grid.
    """

    candidates: list[District] = []
    seen: set[tuple[int, int]] = set()

    # ── Step 1: scan every INFECTED cell and collect HEALTHY neighbors ──────
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            d = grid[row][col]
            if d.state == INFECTED:
                for n in get_neighbors(grid, row, col):
                    if n.state == HEALTHY and (n.row, n.col) not in seen:
                        candidates.append(n)
                        seen.add((n.row, n.col))

    # ── Step 2: no candidates → nothing to recommend ─────────────────────
    if not candidates:
        return None

    # ── Step 3: linear scan for the highest-risk candidate ───────────────
    best = candidates[0]
    for c in candidates:
        if c.risk > best.risk:
            best = c

    # ── Step 4: return the recommendation ────────────────────────────────
    return best