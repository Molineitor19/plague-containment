#include "InfectionList.h"
#include <iostream>


InfectionList::InfectionList() : head(nullptr), count(0) {}

InfectionList::~InfectionList() {
    // Free every node to avoid memory leaks
    InfectionNode* current = head;
    while (current != nullptr) {
        InfectionNode* next = current->next;
        delete current;
        current = next;
    }
}

// Append a new infected district at the end of the list
void InfectionList::append(int row, int col, int turn) {
    if (contains(row, col)) return; // Already in the list

    InfectionNode* newNode = new InfectionNode(row, col, turn);

    if (head == nullptr) {
        head = newNode;
    } else {
        // Walk to the last node
        InfectionNode* current = head;
        while (current->next != nullptr) {
            current = current->next;
        }
        current->next = newNode;
    }
    count++;
}

// Remove a district from the list by position
void InfectionList::remove(int row, int col) {
    if (head == nullptr) return;

    // Special case: removing the head
    if (head->row == row && head->col == col) {
        InfectionNode* toDelete = head;
        head = head->next;
        delete toDelete;
        count--;
        return;
    }

    // General case: find the node before the target
    InfectionNode* current = head;
    while (current->next != nullptr) {
        if (current->next->row == row && current->next->col == col) {
            InfectionNode* toDelete = current->next;
            current->next = toDelete->next;
            delete toDelete;
            count--;
            return;
        }
        current = current->next;
    }
}

// Check whether a district is already in the list
bool InfectionList::contains(int row, int col) const {
    InfectionNode* current = head;
    while (current != nullptr) {
        if (current->row == row && current->col == col) return true;
        current = current->next;
    }
    return false;
}

// Return total number of infected districts
int InfectionList::size() const {
    return count;
}

// Print the chain — useful during development
void InfectionList::print() const {
    InfectionNode* current = head;
    while (current != nullptr) {
        std::cout << "[(" << current->row << "," << current->col
                  << ") t=" << current->turn_infected << "]";
        if (current->next != nullptr) std::cout << " -> ";
        current = current->next;
    }
    std::cout << " -> NULL\n";
}

// Return the head pointer so the engine can traverse the list
InfectionNode* InfectionList::getHead() const {
    return head;
}