# User Memory System

A comprehensive memory management system for Claude Code that maintains user preferences, project context, and solution patterns across sessions.

## Overview

The memory system provides persistent storage and intelligent retrieval of:
- User preferences and coding standards
- Project-specific context and decisions
- Solution patterns and error fixes
- Session history and learning points

## Components

### 1. Memory Agent (`agents/memory.md`)
A specialized agent that manages all memory operations with intelligent features:
- Auto-detection of memorable information
- Context-aware memory application
- Integration with other agents (reviewer, optimizer, debugger, etc.)
- Privacy-focused with no sensitive data storage

### 2. Memory Command (`commands/memory`)
A bash command interface for direct memory management:

```bash
# Store operations
memory store preference <category> <value>
memory store project <aspect> <details>
memory store pattern <problem> <solution>

# Recall operations
memory recall preferences [category]
memory recall project [aspect]
memory recall patterns [type]

# Management operations
memory update <category> <key> <value>
memory list
memory clear [scope]
```

## File Structure

Memory data is organized in `~/.claude/memory/`:

```
.claude/memory/
├── user/                 # User preferences
│   ├── preferences.json
│   ├── coding_standards.md
│   └── workflow_patterns.json
├── projects/            # Project-specific context
│   └── [project-name]/
│       ├── context.json
│       ├── architecture.md
│       ├── conventions.md
│       └── decisions.md
├── sessions/            # Session history
│   ├── history.json
│   ├── todos.json
│   └── learning_log.md
└── patterns/            # Reusable solutions
    ├── solutions.json
    ├── errors.json
    └── optimizations.json
```

## Usage Examples

### Storing Preferences
```bash
# Store coding style preference
memory store preference "indent" "2 spaces"

# Store tool preference
memory store preference "test_framework" "jest"

# Store workflow preference
memory store preference "commit_style" "conventional"
```

### Managing Project Context
```bash
# Store architectural decision
memory store project "architecture" "Using microservices with REST APIs"

# Store naming convention
memory store project "conventions" "Components use PascalCase, utilities use camelCase"

# Recall all project context
memory recall project
```

### Pattern Management
```bash
# Store a solution pattern
memory store pattern "null_pointer_exception" "Always check for null before dereferencing"

# Recall patterns for specific problem type
memory recall patterns "exception"
```

### Memory Overview
```bash
# List all stored memories
memory list

# Clear project-specific memory
memory clear project

# Clear all memory (with confirmation)
memory clear all
```

## Integration with Agents

The memory system integrates seamlessly with other specialized agents:

- **Reviewer**: Applies stored coding standards and preferences
- **Optimizer**: Uses known performance patterns
- **Debugger**: References previous error solutions
- **Writer**: Follows documentation preferences
- **Refactorer**: Applies established patterns
- **Test Generator**: Uses preferred testing approaches

## Privacy & Security

The memory system is designed with privacy in mind:
- Never stores passwords, API keys, or secrets
- Respects user privacy preferences
- Allows selective memory deletion
- Maintains clear audit trail
- All data stored locally in user's home directory

## Benefits

1. **Continuity**: Maintains context across sessions
2. **Personalization**: Adapts to user preferences
3. **Efficiency**: Recalls relevant solutions quickly
4. **Learning**: Builds knowledge base over time
5. **Consistency**: Ensures adherence to established patterns

## Quick Start

1. Use the memory agent for intelligent memory management:
   ```
   @memory store my preference for using TypeScript with strict mode
   ```

2. Use the command line for direct operations:
   ```bash
   memory store preference "language" "TypeScript"
   memory recall preferences
   ```

3. Check stored memories:
   ```bash
   memory list
   ```

## Advanced Features

### Auto-Detection
The memory agent automatically identifies and stores:
- Repeated coding patterns
- Frequently used solutions
- Project conventions from existing code
- User preferences from interactions

### Context Awareness
Memories are automatically applied based on:
- Current project directory
- Active file types
- Recent interactions
- Task context

### Memory Optimization
The system automatically:
- Prunes outdated information
- Consolidates duplicate entries
- Prioritizes frequently accessed memories
- Maintains optimal storage efficiency

## Troubleshooting

If memories aren't being recalled:
1. Check if memory directory exists: `ls ~/.claude/memory`
2. Verify current project name: `basename $(pwd)`
3. List available memories: `memory list`
4. Ensure proper permissions on memory files

## Future Enhancements

Planned improvements:
- Memory export/import for backup
- Team memory sharing capabilities
- Smart memory suggestions
- Memory versioning and rollback
- Integration with git for project-specific memories