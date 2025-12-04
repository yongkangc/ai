---
description: Walk through code logic step-by-step with ASCII diagrams
argument-hint: <file path or directory>
allowed-tools: Read, Glob, Grep, Task
---

Walk me through the code at: $ARGUMENTS

## Instructions

1. **Read the specified code location** - This could be:
   - A file path (e.g., `src/main.rs`)
   - A file with line range (e.g., `src/main.rs:50-100`)
   - A directory to explore key files (e.g., `crates/consensus/`)
   - A function/struct name to locate and explain

2. **Analyze the code structure** and identify:
   - Entry points and main logic flow
   - Key data structures and their relationships
   - Important function calls and their purposes
   - Error handling paths
   - Any concurrency or async patterns

3. **Create ASCII diagrams** to visualize:
   - Control flow (decision trees, loops)
   - Data flow (how data transforms through the code)
   - Component relationships (modules, structs, traits)
   - State machines (if applicable)
   - Call graphs for complex functions

4. **Walk through the logic step-by-step**:
   - Explain what each section does in plain language
   - Highlight non-obvious behavior or edge cases
   - Point out any important invariants or assumptions
   - Reference specific line numbers when explaining

## Diagram Format Examples

Use Unicode box-drawing characters for clean, professional diagrams:

### Code Block with Explanation Box
```
  // Lines 919-923
  debug_assert!(
      self.branch_path.len() < cached_path.len() || self.branch_path == cached_path,
      "branch_path {:?} is different-or-longer-than cached_path {cached_path:?}",
      self.branch_path
  );

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  WHAT THIS CHECKS                                                           │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │                                                                             │
  │  Valid states:                                                              │
  │                                                                             │
  │    branch_path = 0x      cached_path = 0x2A    ✓ (shorter)                  │
  │    branch_path = 0x2     cached_path = 0x2A    ✓ (shorter, is prefix)       │
  │    branch_path = 0x2A    cached_path = 0x2A    ✓ (equal)                    │
  │                                                                             │
  │  Invalid states (would panic):                                              │
  │                                                                             │
  │    branch_path = 0x2AB   cached_path = 0x2A    ✗ (longer!)                  │
  │    branch_path = 0x3     cached_path = 0x2A    ✗ (different path!)          │
  │                                                                             │
  │  Why? Because Phase 1 already popped all branches not on cached_path's      │
  │  path. So branch_path must be a prefix of (or equal to) cached_path.        │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### Bitmask/Binary Visualization
```
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  UNDERSTANDING THE MASKS                                                    │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │                                                                             │
  │  TrieMask is a u16 bitmask where each bit represents a nibble (0-15):       │
  │                                                                             │
  │     Bit:  15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0                   │
  │           ├──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┤                 │
  │  Nibble:   F  E  D  C  B  A  9  8  7  6  5  4  3  2  1  0                   │
  │                                                                             │
  │  Example:                                                                   │
  │                                                                             │
  │  cached_state_mask = 0b0000_1010_0000_0110 = 0x0A06                         │
  │                            A       5    21                                  │
  │                            ↓       ↓    ↓↓                                  │
  │                      Children at nibbles: 1, 2, 5, A exist                  │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### State Grid Visualization
```
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                    BRANCH @ 0x2A                                            │
  ├─────────────────────────────────────────────────────────────────────────────┤
  │                                                                             │
  │  Children:    0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F │
  │             ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
  │  cached:    │   │ ✓ │ ✓ │   │   │ ✓ │   │   │   │   │ ✓ │   │   │   │   │   │
  │  (exists)   └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  │                  1   2           5                   A                       │
  │             ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
  │  curr:      │   │ ✓ │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
  │  (done)     └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  │                  1   ←── already processed                                   │
  │             ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
  │  next:      │   │   │ ✓ │   │   │ ✓ │   │   │   │   │ ✓ │   │   │   │   │   │
  │  (XOR)      └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
  │                      2           5                   A                       │
  │                      ↑           ↑                   ↑                       │
  │                      └───────────┴───────────────────┘                       │
  │                              Still need to process                           │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow
```
  Input ──▶ [Parse] ──▶ [Validate] ──▶ [Transform] ──▶ Output
                │            │
                ▼            ▼
             Errors       Errors
```

### Component Relationships
```
  ┌────────────────┐      ┌────────────────┐
  │  Component A   │─────▶│  Component B   │
  └────────────────┘      └────────────────┘
         │                       │
         ▼                       ▼
  ┌────────────────┐      ┌────────────────┐
  │  Component C   │◀─────│  Component D   │
  └────────────────┘      └────────────────┘
```

## Output Format

Structure your walkthrough as:

1. **Overview** - Brief summary of what this code does
2. **Architecture Diagram** - High-level view of components
3. **Detailed Walkthrough** - Step-by-step explanation with diagrams
4. **Key Insights** - Important patterns, potential gotchas, or notable design decisions

Keep explanations clear and concise. Focus on helping understand the "why" behind the code, not just the "what".
