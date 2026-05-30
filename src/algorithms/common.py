"""
common.py  —  Plague Containment  —  Team 16
════════════════════════════════════════════════════════════════════════════
Shared constants, data model, and grid utilities.
Imported by vaccination.py, quarantine.py, and algorithms.py.
════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────

GRID_SIZE = 8   # fixed 8×8 city grid

# District state labels — must match the JSON schema
HEALTHY     = "healthy"
INFECTED    = "infected"
VACCINATED  = "vaccinated"
QUARANTINED = "quarantined"

# 4-connectivity: up · down · left · right
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


# ─────────────────────────────────────────────────────────────
#  Data Model
# ─────────────────────────────────────────────────────────────

class District:
    """
    One cell of the 8x8 city grid.

    Attributes
    ----------
    row, col : int   Grid position (0-indexed, top-left is (0,0)).
    risk     : int   Infection vulnerability 1-10. Assigned once; never changes.
    state    : str   One of HEALTHY | INFECTED | VACCINATED | QUARANTINED.
    """

    def __init__(self, row: int, col: int, risk: int, state: str = HEALTHY):
        self.row   = row
        self.col   = col
        self.risk  = risk
        self.state = state

    def __repr__(self) -> str:
        return f"District({self.row},{self.col} risk={self.risk} [{self.state}])"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, District)
            and self.row == other.row
            and self.col == other.col
        )

    def __hash__(self) -> int:
        # Required so Districts can be stored in sets and used as dict keys
        return hash((self.row, self.col))


# ─────────────────────────────────────────────────────────────
#  Grid Utilities
# ─────────────────────────────────────────────────────────────

def build_grid(districts_data: list[dict]) -> list[list[District]]:
    """
    Build an 8x8 matrix of District objects from the JSON 'districts' array.

    Parameters
    ----------
    districts_data : list of dicts — each dict has keys row, col, risk, state.

    Returns
    -------
    grid : list[list[District]]   accessed as grid[row][col].
    """
    grid: list[list[District | None]] = [
        [None] * GRID_SIZE for _ in range(GRID_SIZE)
    ]
    for entry in districts_data:
        r, c = entry["row"], entry["col"]
        grid[r][c] = District(r, c, entry["risk"], entry["state"])
    return grid  # type: ignore[return-value]


def get_neighbors(grid: list[list[District]], row: int, col: int) -> list[District]:
    """
    Return the 4-connected neighbors (up/down/left/right) of cell (row, col).
    Cells outside the 8x8 boundary are ignored.
    """
    neighbors: list[District] = []
    for dr, dc in DIRECTIONS:
        nr, nc = row + dr, col + dc
        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
            neighbors.append(grid[nr][nc])
    return neighbors