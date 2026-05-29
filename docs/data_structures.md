# Data Structures — Plague Containment Engine

**Author:** Nelson David Molina Ramos  
**Component:** C++ Game Engine  
**Course:** Computer Sciences I — Universidad Distrital Francisco José de Caldas

---

## 1. Infection Linked List

### What it is

A singly linked list where each node represents one infected district.
Nodes are appended in the order the plague spreads, so the list is always
sorted chronologically by turn.

### Node structure

| Field          | Type          | Description                              |
|----------------|---------------|------------------------------------------|
| `row`          | `int`         | Row position on the 8×8 grid            |
| `col`          | `int`         | Column position on the 8×8 grid         |
| `turn_infected`| `int`         | Turn number when the district got infected |
| `next`         | `InfectionNode*` | Pointer to the next infected district |

### How it supports the engine

- **Plague spread:** Every turn the engine traverses the list from `head`
  to `NULL`. For each node it checks the four neighbors of that district
  and marks healthy ones as newly infected, appending them to the list.
  This traversal is O(n) where n is the number of currently infected districts.

- **Chronological order:** Because nodes are always appended at the tail,
  the list preserves the exact sequence of infection. This order is written
  directly into `state.json` as the `infection_chain` array, so Python and
  Pygame can reconstruct how the plague spread over time.

- **Quarantine removal:** When the backtracking algorithm places a district
  under quarantine, the engine calls `remove(row, col)` to take it out of
  the active infection chain, stopping further spread from that node.

### Complexity

| Operation  | Time     |
|------------|----------|
| `append`   | O(n)     |
| `remove`   | O(n)     |
| `contains` | O(n)     |
| Traversal  | O(n)     |

---

## 2. District-Risk AVL Tree

### What it is

A self-balancing binary search tree (AVL) that indexes every district
on the grid by its risk level. The risk level is the key used for ordering.
Because the tree stays balanced after every insertion and deletion, the
node with the highest risk is always found in O(log n) time by walking
to the rightmost node.

### Node structure

| Field    | Type       | Description                                      |
|----------|------------|--------------------------------------------------|
| `risk`   | `int`      | Risk level (1–10), used as the ordering key      |
| `row`    | `int`      | Row position on the 8×8 grid                     |
| `col`    | `int`      | Column position on the 8×8 grid                  |
| `height` | `int`      | Height of this node, used to compute balance     |
| `left`   | `AVLNode*` | Pointer to the left subtree (lower risk)         |
| `right`  | `AVLNode*` | Pointer to the right subtree (higher risk)       |

### How it supports the engine

- **Greedy advisor:** The greedy vaccination algorithm needs the healthy
  border district with the highest risk. The engine calls `findMax()`,
  which walks right from the root until there is no right child. This
  is always O(log n), never a full scan of the grid.

- **State updates:** When a district changes state (becomes infected,
  vaccinated, or quarantined) the engine removes it from the AVL tree
  with `remove(risk, row, col)` so it is no longer considered a candidate
  for vaccination. The tree rebalances automatically after each removal.

- **Insertion at game start:** At the beginning of the game all 64
  districts are inserted into the tree. Each insertion triggers at most
  O(log n) rotations to maintain the AVL balance property.

### AVL balance property

After every insertion or deletion the tree checks the balance factor
of each affected node. The balance factor is defined as:

```
bf = height(left subtree) − height(right subtree)
```

If `|bf| > 1` the tree applies one of four rotations:

| Case         | Condition                        | Fix                          |
|--------------|----------------------------------|------------------------------|
| Left-Left    | bf > 1, bf(left) >= 0           | Single right rotation        |
| Left-Right   | bf > 1, bf(left) < 0            | Left rotation then right     |
| Right-Right  | bf < -1, bf(right) <= 0         | Single left rotation         |
| Right-Left   | bf < -1, bf(right) > 0          | Right rotation then left     |

### Complexity

| Operation  | Time      |
|------------|-----------|
| `insert`   | O(log n)  |
| `remove`   | O(log n)  |
| `findMax`  | O(log n)  |
| `contains` | O(log n)  |

---

## 3. How the two structures work together

```
Each game turn:

  AVL Tree                          Infection List
  ─────────────────                 ──────────────────────────────
  findMax()                         traverse head → NULL
      │                                 │
      ▼                                 ▼
  highest-risk                      for each infected district
  healthy border                        check 4 neighbors
  district                              append newly infected
      │                                 nodes to the list
      ▼
  greedy recommendation
  written to result.json
```

- The **AVL tree** answers the question: *which healthy district is most
  at risk right now?*
- The **linked list** answers the question: *which districts are currently
  spreading the plague?*

Together they give the engine fast access to both the threat index and
the active infection chain without scanning the full 8×8 grid on every turn.
