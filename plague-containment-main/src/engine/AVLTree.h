#pragma once


// One district stored in the AVL tree
struct AVLNode {
    int risk;       // Key — risk level (1–10)
    int row;        // Grid row position
    int col;        // Grid column position
    int height;     // Height of this node (used for balancing)
    AVLNode* left;
    AVLNode* right;

    AVLNode(int risk, int row, int col)
        : risk(risk), row(row), col(col),
          height(1), left(nullptr), right(nullptr) {}
};

class AVLTree {
public:
    AVLTree();
    ~AVLTree();

    // Insert a district into the tree
    void insert(int risk, int row, int col);

    // Remove a district by its position (row, col)
    void remove(int risk, int row, int col);

    // Find and return the node with the highest risk level
    AVLNode* findMax() const;

    // Check if a district exists in the tree
    bool contains(int risk, int row, int col) const;

    // Print the tree in-order (ascending risk) — for debugging
    void printInOrder() const;

private:
    AVLNode* root;

    // Internal recursive helpers
    AVLNode* insert(AVLNode* node, int risk, int row, int col);
    AVLNode* remove(AVLNode* node, int risk, int row, int col);
    void     destroy(AVLNode* node);
    void     printInOrder(AVLNode* node) const;

    // AVL balancing utilities
    int      height(AVLNode* node) const;
    int      balanceFactor(AVLNode* node) const;
    void     updateHeight(AVLNode* node);
    AVLNode* balance(AVLNode* node);
    AVLNode* rotateRight(AVLNode* node);
    AVLNode* rotateLeft(AVLNode* node);
    AVLNode* findMin(AVLNode* node) const;
};
