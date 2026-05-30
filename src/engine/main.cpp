──────────────────────────────────────────

#include <iostream>
#include "InfectionList.h"
#include "AVLTree.h"



void printSeparator(const std::string& title) {
    std::cout << "\n══════════════════════════════════════\n";
    std::cout << "  " << title << "\n";
    std::cout << "══════════════════════════════════════\n";
}


void testInfectionList() {
    printSeparator("INFECTION LINKED LIST TESTS");
    InfectionList list;

    // Test 1: append districts
    std::cout << "\n[1] Appending infected districts...\n";
    list.append(3, 4, 1);
    list.append(3, 5, 1);
    list.append(2, 4, 2);
    list.append(4, 4, 3);
    std::cout << "    Chain: ";
    list.print();
    std::cout << "    Size: " << list.size() << " (expected: 4)\n";

    // Test 2: no duplicates
    std::cout << "\n[2] Appending duplicate (3,4) — should be ignored...\n";
    list.append(3, 4, 1);
    std::cout << "    Size: " << list.size() << " (expected: 4)\n";

    // Test 3: contains
    std::cout << "\n[3] Contains checks...\n";
    std::cout << "    (3,4) -> " << (list.contains(3,4) ? "YES" : "NO") << " (expected: YES)\n";
    std::cout << "    (0,0) -> " << (list.contains(0,0) ? "YES" : "NO") << " (expected: NO)\n";

    // Test 4: remove
    std::cout << "\n[4] Removing district (3,5) — quarantined...\n";
    list.remove(3, 5);
    std::cout << "    Chain: ";
    list.print();
    std::cout << "    Size: " << list.size() << " (expected: 3)\n";

    // Test 5: remove head
    std::cout << "\n[5] Removing head (3,4)...\n";
    list.remove(3, 4);
    std::cout << "    Chain: ";
    list.print();
    std::cout << "    Size: " << list.size() << " (expected: 2)\n";

    // Test 6: remove all
    std::cout << "\n[6] Removing all remaining districts...\n";
    list.remove(2, 4);
    list.remove(4, 4);
    std::cout << "    Chain: ";
    list.print();
    std::cout << "    Size: " << list.size() << " (expected: 0)\n";
}

// ── AVL Tree Tests ────────────────────────────

void testAVLTree() {
    printSeparator("AVL TREE TESTS");
    AVLTree tree;

    // Test 1: insert districts
    std::cout << "\n[1] Inserting districts with varying risk levels...\n";
    tree.insert(5, 2, 5);
    tree.insert(4, 5, 1);
    tree.insert(9, 0, 7);
    tree.insert(2, 7, 3);
    tree.insert(6, 1, 2);
    tree.insert(8, 4, 6);
    tree.insert(10, 3, 0);
    tree.insert(3, 6, 7);
    tree.insert(7, 2, 4);
    std::cout << "    In-order (ascending risk): ";
    tree.printInOrder();

    // Test 2: findMax — used by greedy advisor
    std::cout << "\n[2] Finding highest-risk district (greedy target)...\n";
    AVLNode* maxNode = tree.findMax();
    if (maxNode) {
        std::cout << "    Max risk: " << maxNode->risk
                  << " at (" << maxNode->row << "," << maxNode->col << ")"
                  << " (expected: risk=10 at (3,0))\n";
    }

    // Test 3: contains
    std::cout << "\n[3] Contains checks...\n";
    std::cout << "    risk=9 at (0,7) -> "
              << (tree.contains(9,0,7) ? "YES" : "NO") << " (expected: YES)\n";
    std::cout << "    risk=1 at (0,0) -> "
              << (tree.contains(1,0,0) ? "YES" : "NO") << " (expected: NO)\n";

    // Test 4: remove a district (it became infected)
    std::cout << "\n[4] Removing district risk=10 (now infected, no longer candidate)...\n";
    tree.remove(10, 3, 0);
    std::cout << "    In-order after removal: ";
    tree.printInOrder();

    // Test 5: new max after removal
    std::cout << "\n[5] New greedy target after removal...\n";
    maxNode = tree.findMax();
    if (maxNode) {
        std::cout << "    Max risk: " << maxNode->risk
                  << " at (" << maxNode->row << "," << maxNode->col << ")"
                  << " (expected: risk=9 at (0,7))\n";
    }

    // Test 6: remove several and check balance holds
    std::cout << "\n[6] Removing risk=9 and risk=8, checking new max...\n";
    tree.remove(9, 0, 7);
    tree.remove(8, 4, 6);
    std::cout << "    In-order: ";
    tree.printInOrder();
    maxNode = tree.findMax();
    if (maxNode) {
        std::cout << "    Max risk: " << maxNode->risk
                  << " at (" << maxNode->row << "," << maxNode->col << ")"
                  << " (expected: risk=7 at (2,4))\n";
    }
}



int main() {
    std::cout << "╔════════════════════════════════════════╗\n";
    std::cout << "║   Plague Containment — Engine Tests    ║\n";
    std::cout << "╚════════════════════════════════════════╝\n";

    testInfectionList();
    testAVLTree();

    printSeparator("ALL TESTS COMPLETE");
    return 0;
}
