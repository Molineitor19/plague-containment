// ─────────────────────────────────────────────
//  engine.cpp
//  Plague Containment — C++ Game Engine
//
//  Reads action.json, updates game state,
//  spreads the plague, and writes state.json.
// ─────────────────────────────────────────────

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include "json.hpp"
#include "InfectionList.h"
#include "AVLTree.h"
#include <windows.h>
#include <cstdlib>
#include <ctime>

using json = nlohmann::json;

// ── Constants ─────────────────────────────────

const int GRID_SIZE = 8;

// District states as strings (match state.json schema)
const std::string HEALTHY     = "healthy";
const std::string INFECTED    = "infected";
const std::string VACCINATED  = "vaccinated";
const std::string QUARANTINED = "quarantined";

// ── Grid ──────────────────────────────────────

struct District {
    int row;
    int col;
    int risk;
    std::string state;
};

// 8x8 grid of districts
District grid[GRID_SIZE][GRID_SIZE];

// ── Data structures ───────────────────────────

InfectionList infectionChain;
AVLTree       riskTree;

// ── Neighbor helper ───────────────────────────

// Returns the 4 cardinal neighbors of (r,c) that are inside the grid
std::vector<std::pair<int,int>> neighbors(int r, int c) {
    std::vector<std::pair<int,int>> result;
    int dr[] = {-1, 1, 0, 0};
    int dc[] = { 0, 0,-1, 1};
    for (int i = 0; i < 4; i++) {
        int nr = r + dr[i];
        int nc = c + dc[i];
        if (nr >= 0 && nr < GRID_SIZE && nc >= 0 && nc < GRID_SIZE)
            result.push_back({nr, nc});
    }
    return result;
}

// ── Plague spread ─────────────────────────────

// Called at the end of each turn
// Every infected district tries to infect its healthy neighbors
void spreadPlague(int currentTurn) {
    // Collect newly infected districts (avoid modifying while iterating)
    std::vector<std::pair<int,int>> newlyInfected;

    InfectionNode* node = infectionChain.getHead();
    while (node != nullptr) {
        for (auto [nr, nc] : neighbors(node->row, node->col)) {
            if (grid[nr][nc].state == HEALTHY) {
                newlyInfected.push_back({nr, nc});
            }
        }
        node = node->next;
    }

    // Apply infection
    for (auto [r, c] : newlyInfected) {
        if (grid[r][c].state == HEALTHY) { // double-check (avoid double infection)
            grid[r][c].state = INFECTED;
            infectionChain.append(r, c, currentTurn);
            riskTree.remove(grid[r][c].risk, r, c);
        }
    }
}

// ── JSON I/O ──────────────────────────────────

// Write the full game state to state.json
void writeStateJSON(int turn) {
    json j;
    j["turn"]      = turn;
    j["grid_size"] = GRID_SIZE;

    // Districts array
    json districts = json::array();
    for (int r = 0; r < GRID_SIZE; r++) {
        for (int c = 0; c < GRID_SIZE; c++) {
            districts.push_back({
                {"row",   grid[r][c].row},
                {"col",   grid[r][c].col},
                {"risk",  grid[r][c].risk},
                {"state", grid[r][c].state}
            });
        }
    }
    j["districts"] = districts;

    // Infection chain (linked list → array)
    json chain = json::array();
    InfectionNode* node = infectionChain.getHead();
    while (node != nullptr) {
        chain.push_back({
            {"row",          node->row},
            {"col",          node->col},
            {"turn_infected",node->turn_infected}
        });
        node = node->next;
    }
    j["infection_chain"] = chain;

    // Stats
    int totalInfected = 0, totalVaccinated = 0,
        totalQuarantined = 0, totalHealthy = 0;
    for (int r = 0; r < GRID_SIZE; r++)
        for (int c = 0; c < GRID_SIZE; c++) {
            std::string s = grid[r][c].state;
            if      (s == INFECTED)    totalInfected++;
            else if (s == VACCINATED)  totalVaccinated++;
            else if (s == QUARANTINED) totalQuarantined++;
            else                       totalHealthy++;
        }
    j["stats"] = {
        {"total_infected",    totalInfected},
        {"total_vaccinated",  totalVaccinated},
        {"total_quarantined", totalQuarantined},
        {"total_healthy",     totalHealthy}
    };

    std::ofstream file("../interface/state.json");
    file << j.dump(2);
    file.close();
    std::cout << "[engine] state.json written (turn " << turn << ")\n";
}

// Read the player action from action.json
// Returns false if the file does not exist yet
bool readActionJSON(std::string& actionType, int& targetRow, int& targetCol, int& turn) {
    std::ifstream file("../interface/action.json");
    if (!file.is_open()) return false;

    json j;
    file >> j;
    file.close();

    actionType = j["action_type"];
    targetRow  = j["target"]["row"];
    targetCol  = j["target"]["col"];
    turn       = j["turn"];
    return true;
}

// ── Apply player action ───────────────────────

void applyAction(const std::string& actionType, int row, int col) {
    if (actionType == "vaccinate") {
        if (grid[row][col].state == HEALTHY) {
            grid[row][col].state = VACCINATED;
            riskTree.remove(grid[row][col].risk, row, col);
            std::cout << "[engine] District (" << row << "," << col
                      << ") vaccinated.\n";
        }
    } else if (actionType == "quarantine") {
        if (grid[row][col].state == HEALTHY) {
            grid[row][col].state = QUARANTINED;
            infectionChain.remove(row, col);
            riskTree.remove(grid[row][col].risk, row, col);
            std::cout << "[engine] District (" << row << "," << col
                      << ") quarantined.\n";
        }
    } else {
        std::cout << "[engine] Turn skipped.\n";
    }
}

// ── Win / Lose check ──────────────────────────

// Returns "ongoing", "win", or "lose"
std::string checkGameStatus() {
    int infected = 0, healthy = 0;
    for (int r = 0; r < GRID_SIZE; r++)
        for (int c = 0; c < GRID_SIZE; c++) {
            if (grid[r][c].state == INFECTED)  infected++;
            if (grid[r][c].state == HEALTHY)   healthy++;
        }
    if (infected == 0) return "win";
    if (healthy  == 0) return "lose";
    return "ongoing";
}

// ── Initialization ────────────────────────────

// Fixed risk map for a reproducible starting game
// Values between 1 and 10
const int RISK_MAP[GRID_SIZE][GRID_SIZE] = {
    {3, 5, 2, 7, 4, 6, 1, 3},
    {4, 6, 8, 5, 3, 7, 2, 5},
    {2, 4, 6, 8, 9, 7, 3, 4},
    {5, 3, 4, 7, 6, 5, 8, 2},
    {6, 7, 8, 9,10, 1, 2, 3},
    {4, 5, 6, 7, 8, 9,10, 1},
    {2, 3, 4, 5, 6, 7, 8, 9},
    {10,1, 2, 3, 4, 5, 6, 7}
};

void initGrid() {
    for (int r = 0; r < GRID_SIZE; r++) {
        for (int c = 0; c < GRID_SIZE; c++) {
            grid[r][c] = {r, c, RISK_MAP[r][c], HEALTHY};
            riskTree.insert(RISK_MAP[r][c], r, c);
        }
    }

   // Random seed infection
srand(static_cast<unsigned int>(time(nullptr)));
int startR = 2 + rand() % 5;  // between 2 and 6
int startC = 2 + rand() % 5;
grid[startR][startC].state = INFECTED;
infectionChain.append(startR, startC, 1);
riskTree.remove(RISK_MAP[startR][startC], startR, startC);

std::cout << "[engine] Grid initialized. Initial infection at ("
          << startR << "," << startC << ").\n";
}

// ── Main loop ─────────────────────────────────

int main() {
    std::cout << "╔══════════════════════════════════════╗\n";
    std::cout << "║   Plague Containment — C++ Engine    ║\n";
    std::cout << "╚══════════════════════════════════════╝\n\n";

    initGrid();

    int turn = 1;
    const int MAX_TURNS = 20;

    while (turn <= MAX_TURNS) {
        std::cout << "\n── Turn " << turn << " ──\n";

        // 1. Write current state for Python/Pygame to read
        writeStateJSON(turn);

        // 2. Wait for player action from Pygame
        std::cout << "[engine] Waiting for action.json...\n";
        while (!std::ifstream("../interface/action.json").good()) {
            Sleep(500);
        }
        Sleep(200);

        // 3. Read and apply player action
        std::string actionType;
        int targetRow, targetCol, actionTurn;
        if (readActionJSON(actionType, targetRow, targetCol, actionTurn)) {
            applyAction(actionType, targetRow, targetCol);
            std::remove("../interface/action.json");
        } else {
            std::cout << "[engine] No action found — skipping.\n";
        }

        // 4. Spread the plague
        spreadPlague(turn);

        // 5. Check win/lose
        std::string status = checkGameStatus();
        if (status == "win") {
            std::cout << "\n[engine] *** PLAYER WINS ***\n";
            writeStateJSON(turn);
            break;
        } else if (status == "lose") {
            std::cout << "\n[engine] *** GAME OVER ***\n";
            writeStateJSON(turn);
            break;
        }

        turn++;
    }

    return 0;
}

