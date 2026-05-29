# Plague Containment

> Turn-based epidemic strategy game built for the Computer Sciences I course at Universidad Distrital Francisco José de Caldas.

## Abstract

Plague Containment models a city as an 8×8 grid of districts, each assigned a fixed infection risk level (1–10). A plague spreads each turn to neighboring districts. The player uses two algorithmic tools to stop it: a **greedy vaccination advisor** that always targets the highest-risk uninfected border district, and a **backtracking quarantine planner** that finds a valid containment perimeter without isolating any healthy district. The system is implemented across three layers — a C++ game engine, a Python algorithm module, and a Pygame interface — communicating through JSON files.

## Methodology

| Layer | Language | Role |
|-------|----------|------|
| Engine | C++ | Infection linked list, district AVL tree, plague spread, state serialization |
| Algorithms | Python | Greedy vaccination advisor, backtracking quarantine planner |
| Interface | Python / Pygame | Grid rendering, player input, HUD, JSON I/O |

The three layers communicate exclusively through three JSON files: `state.json` (engine → all), `result.json` (algorithms → interface), and `action.json` (interface → engine).

## Repository Structure

plague-containment/
├── src/
│   ├── engine/          # C++ game engine (linked list, AVL tree, plague spread)
│   ├── algorithms/      # Python greedy and backtracking modules
│   └── interface/       # Pygame rendering and input handling
├── docs/
│   ├── diagrams/        # Data structure diagrams and architecture figures
│   └── paper/           # Technical paper (IEEE format)
├── data/
│   ├── schemas/         # JSON schema definitions (state, result, action)
│   └── samples/         # Example JSON files for testing
├── experiments/         # Test runs and algorithm benchmarks
├── results/             # Output data and performance measurements
├── references/          # Bibliography and cited resources
├── .gitignore
├── LICENSE
└── README.md

## Team

| Member | Role |
|--------|------|
| Nelson David Molina Ramos | Data Structures (C++) — infection linked list and district-risk AVL tree |
| Brayan Estiven Aguirre Aristizabal | Algorithms (Python) — greedy vaccination and backtracking quarantine |
| Juan Sneyder Méndez Gil | Interface & Integration — Pygame, JSON schema, system architecture |

## License

MIT License — see [LICENSE](LICENSE) for details.

