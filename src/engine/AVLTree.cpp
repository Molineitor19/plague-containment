#include "AVLTree.h"
#include <iostream>
#include <algorithm>

// ─────────────────────────────────────────────
//  AVLTree.cpp
//  Plague Containment — C++ Engine
// ─────────────────────────────────────────────

AVLTree::AVLTree() : root(nullptr) {}

AVLTree::~AVLTree() {
    destroy(root);
}

// Recursively free all nodes
void AVLTree::destroy(AVLNode* node) {
    if (node == nullptr) return;
    destroy(node->left);
    destroy(node->right);
    delete node;
}

// ── Height & Balance ──────────────────────────

int AVLTree::height(AVLNode* node) const {
    return (node == nullptr) ? 0 : node->height;
}

int AVLTree::balanceFactor(AVLNode* node) const {
    return (node == nullptr) ? 0 : height(node->left) - height(node->right);
}

void AVLTree::updateHeight(AVLNode* node) {
    if (node != nullptr)
        node->height = 1 + std::max(height(node->left), height(node->right));
}

// ── Rotations ────────────────────────────────

//        y                x
//       / \              / \
//      x   T3    →     T1   y
//     / \                  / \
//   T1  T2               T2  T3
AVLNode* AVLTree::rotateRight(AVLNode* y) {
    AVLNode* x  = y->left;
    AVLNode* T2 = x->right;

    x->right = y;
    y->left  = T2;

    updateHeight(y);
    updateHeight(x);
    return x;
}

//      x                  y
//     / \                / \
//   T1   y      →       x   T3
//       / \            / \
//      T2  T3        T1  T2
AVLNode* AVLTree::rotateLeft(AVLNode* x) {
    AVLNode* y  = x->right;
    AVLNode* T2 = y->left;

    y->left  = x;
    x->right = T2;

    updateHeight(x);
    updateHeight(y);
    return y;
}

// ── Balance ───────────────────────────────────

AVLNode* AVLTree::balance(AVLNode* node) {
    updateHeight(node);
    int bf = balanceFactor(node);

    // Left-heavy
    if (bf > 1) {
        if (balanceFactor(node->left) < 0)          // Left-Right case
            node->left = rotateLeft(node->left);
        return rotateRight(node);                    // Left-Left case
    }

    // Right-heavy
    if (bf < -1) {
        if (balanceFactor(node->right) > 0)          // Right-Left case
            node->right = rotateRight(node->right);
        return rotateLeft(node);                     // Right-Right case
    }

    return node; // Already balanced
}

// ── Insert ────────────────────────────────────

void AVLTree::insert(int risk, int row, int col) {
    root = insert(root, risk, row, col);
}

AVLNode* AVLTree::insert(AVLNode* node, int risk, int row, int col) {
    if (node == nullptr)
        return new AVLNode(risk, row, col);

    if (risk < node->risk)
        node->left  = insert(node->left,  risk, row, col);
    else if (risk > node->risk)
        node->right = insert(node->right, risk, row, col);
    else {
        // Same risk level: use (row, col) as tiebreaker
        if (row < node->row || (row == node->row && col < node->col))
            node->left  = insert(node->left,  risk, row, col);
        else
            node->right = insert(node->right, risk, row, col);
    }

    return balance(node);
}

// ── Remove ───────────────────────────────────

void AVLTree::remove(int risk, int row, int col) {
    root = remove(root, risk, row, col);
}

AVLNode* AVLTree::remove(AVLNode* node, int risk, int row, int col) {
    if (node == nullptr) return nullptr;

    if (risk < node->risk) {
        node->left  = remove(node->left,  risk, row, col);
    } else if (risk > node->risk) {
        node->right = remove(node->right, risk, row, col);
    } else {
        // Risk matches — verify it is the exact district
        if (node->row == row && node->col == col) {
            if (node->left == nullptr || node->right == nullptr) {
                // 0 or 1 child
                AVLNode* child = (node->left != nullptr) ? node->left : node->right;
                delete node;
                return child;
            }
            // 2 children: replace with in-order successor (min of right subtree)
            AVLNode* successor = findMin(node->right);
            node->risk = successor->risk;
            node->row  = successor->row;
            node->col  = successor->col;
            node->right = remove(node->right, successor->risk,
                                 successor->row, successor->col);
        } else {
            // Same risk, different district — search both subtrees
            node->left  = remove(node->left,  risk, row, col);
            node->right = remove(node->right, risk, row, col);
        }
    }

    return balance(node);
}

// ── Helpers ──────────────────────────────────

// Return the node with the smallest risk in a subtree
AVLNode* AVLTree::findMin(AVLNode* node) const {
    while (node->left != nullptr)
        node = node->left;
    return node;
}

// Return the node with the highest risk (rightmost node)
AVLNode* AVLTree::findMax() const {
    if (root == nullptr) return nullptr;
    AVLNode* current = root;
    while (current->right != nullptr)
        current = current->right;
    return current;
}

// Check if a specific district exists in the tree
bool AVLTree::contains(int risk, int row, int col) const {
    AVLNode* current = root;
    while (current != nullptr) {
        if (risk == current->risk && row == current->row && col == current->col)
            return true;
        if (risk < current->risk)
            current = current->left;
        else
            current = current->right;
    }
    return false;
}

// Print all districts in ascending order of risk
void AVLTree::printInOrder() const {
    printInOrder(root);
    std::cout << "\n";
}

void AVLTree::printInOrder(AVLNode* node) const {
    if (node == nullptr) return;
    printInOrder(node->left);
    std::cout << "[risk=" << node->risk
              << " (" << node->row << "," << node->col << ")] ";
    printInOrder(node->right);
}
