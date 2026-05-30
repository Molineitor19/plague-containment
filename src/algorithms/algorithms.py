"""
algorithms.py  —  Plague Containment  —  Team 16
════════════════════════════════════════════════════════════════════════════
Main entry point for the Python algorithm module.

JSON Bridge role:
  Reads  → state.json   (written by the C++ engine at the start of each turn)
  Writes → result.json  (read by the Pygame interface for rendering)

Imports the two algorithm modules:
  vaccination.py       — Algorithm 1: Greedy Vaccination
  quarantine.py — Algorithms 2-3: Backtracking Quarantine
════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import json
from typing import Optional

from common import District, build_grid
from vaccination import greedy_vaccination
from quarantine import backtracking_quarantine


# ─────────────────────────────────────────────────────────────
#  JSON Bridge  —  I / O
# ─────────────────────────────────────────────────────────────

def load_state(path: str = "state.json") -> tuple[list[list[District]], dict]:
    """
    Read state.json (written by the C++ engine) and build the game grid.

    Returns
    -------
    (grid, raw_data)
      grid     : 8x8 District matrix ready for the algorithms.
      raw_data : full parsed JSON dict (used for stats logging).
    """
    with open(path, "r", encoding="utf-8") as f:
        data: dict = json.load(f)
    grid = build_grid(data["districts"])
    return grid, data


def write_results(
    greedy_result: Optional[District],
    quarantine_result: Optional[set[District]],
    path: str = "result.json",
) -> None:
    """
    Write both algorithm recommendations to result.json.

    The Pygame interface reads this file to highlight the greedy suggestion
    and to render the proposed quarantine districts on the grid.

    Schema
    ------
    {
      "greedy_recommendation": { "row", "col", "risk", "reason" } | null,
      "quarantine_plan": {
        "found": bool,
        "districts": [{ "row", "col" }, ...],
        "cost": int
      }
    }
    """
    # ── Greedy section ────────────────────────────────────────────────────────
    if greedy_result is not None:
        greedy_json: Optional[dict] = {
            "row":    greedy_result.row,
            "col":    greedy_result.col,
            "risk":   greedy_result.risk,
            "reason": "highest-risk healthy neighbor",
        }
    else:
        greedy_json = None

    # ── Quarantine section ────────────────────────────────────────────────────
    if quarantine_result is not None:
        quarantine_json: dict = {
            "found":     True,
            "districts": [
                {"row": d.row, "col": d.col} for d in quarantine_result
            ],
            "cost": len(quarantine_result),
        }
    else:
        quarantine_json = {
            "found":     False,
            "districts": [],
            "cost":      0,
        }

    output = {
        "greedy_recommendation": greedy_json,
        "quarantine_plan":       quarantine_json,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"[algorithms] Wrote → {path}")


# ─────────────────────────────────────────────────────────────
#  Main Entry Point
# ─────────────────────────────────────────────────────────────

def run(
    state_path:  str = "state.json",
    result_path: str = "result.json",
) -> None:
    """
    Full turn cycle for the algorithm module  (§VI-C, Figure 3, steps 2-3):
      1. Load game state from state.json.
      2. Run Greedy Vaccination  → get recommendation.
      3. Run Backtracking Quarantine → get perimeter plan.
      4. Write both results to result.json.
    """
    print("[algorithms] ── Loading state ─────────────────────────────")
    grid, raw = load_state(state_path)
    stats = raw.get("stats", {})
    print(
        f"  Turn {raw.get('turn', '?')} | "
        f"infected={stats.get('total_infected', '?')}  "
        f"healthy={stats.get('total_healthy', '?')}"
    )

    print("[algorithms] ── Greedy Vaccination ─────────────────────────")
    greedy_result = greedy_vaccination(grid)
    if greedy_result:
        print(
            f"  Recommend: ({greedy_result.row},{greedy_result.col})"
            f"  risk={greedy_result.risk}"
        )
    else:
        print("  No vaccination candidates found.")

    print("[algorithms] ── Backtracking Quarantine ────────────────────")
    quarantine_result = backtracking_quarantine(grid)
    if quarantine_result is not None:
        coords = sorted((d.row, d.col) for d in quarantine_result)
        print(f"  Plan found: {len(quarantine_result)} district(s) → {coords}")
    else:
        print("  No valid quarantine plan exists.")

    print("[algorithms] ── Writing results ────────────────────────────")
    write_results(greedy_result, quarantine_result, result_path)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run()