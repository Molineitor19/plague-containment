#pragma once

// ─────────────────────────────────────────────
//  InfectionList.h
//  Plague Containment — C++ Engine
//
//  Singly linked list that tracks every infected
//  district in chronological order.
// ─────────────────────────────────────────────

// One infected district in the chain
struct InfectionNode {
    int row;              // Row position on the 8x8 grid
    int col;              // Column position on the 8x8 grid
    int turn_infected;    // Turn number when this district got infected
    InfectionNode* next;  // Pointer to the next infected district

    InfectionNode(int r, int c, int turn)
        : row(r), col(c), turn_infected(turn), next(nullptr) {}
};

// The linked list that holds all infected districts
class InfectionList {
public:
    InfectionList();
    ~InfectionList();

    // Add a newly infected district at the end of the list
    void append(int row, int col, int turn);

    // Remove a district from the list (e.g. if quarantined)
    void remove(int row, int col);

    // Check if a district is already in the list
    bool contains(int row, int col) const;

    // Return the number of infected districts
    int size() const;

    // Print the full chain (for debugging)
    void print() const;

    // Get the head of the list (used by the engine to traverse)
    InfectionNode* getHead() const;

private:
    InfectionNode* head;
    int count;
};