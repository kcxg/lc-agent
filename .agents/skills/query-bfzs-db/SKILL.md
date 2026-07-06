---
name: query-bfzs-db
description: >-
  Use when debugging bfzs application data, verifying session messages,
  checking agent presets, or inspecting tool call history. Triggers: user asks
  about sessions, messages, tool usage, or agent preset configuration in bfzs.
---

# Query bfzs Database

## Overview

Query the bfzs SQLite databases directly to inspect sessions, messages, agent presets, and tool call history — without needing the server running.

## When to Use

- Debugging what tools/presets are actually being used in a session
- Verifying message content without manual browser testing
- Checking if the correct `preset_id` was applied to a session
- Inspecting tool call history for a specific conversation

## Quick Reference

| Command | Purpose |
|---------|---------|
| `--sessions [--limit N] [--search KEYWORD]` | List recent sessions, with optional keyword search |
| `--presets` | List agent presets (all fields: model, prompt, tools, mcp, skills) |
| `--users` | List users and their agent access permissions |
| `--last` | Use the most recent session (shortcut) |
| `--last --msgs` | UI messages for most recent session (fast, has usage) |
| `--last --tools` | Tool calls for most recent session |
| `--msgs <session-uuid>` | UI messages from chat_ui_messages table (fast, shows usage/traces) |
| `<session-uuid>` | Full messages from LangGraph checkpoint |
| `--tools <session-uuid>` | Tool calls only, from LangGraph checkpoint |
| `--state` | Runtime MCP servers and tool groups status (server must be running) |

## Implementation

```powershell
$Python = "D:\ProgramData\miniconda3\envs\py312\python.exe"
$Script = "D:\codes\lc-agent\.agents\skills\query-bfzs-db\scripts\query_session.py"

# Most common: see last session's UI messages
& $Python $Script --last --msgs

# List recent sessions
& $Python $Script --sessions --limit 20

# Search sessions by title
& $Python $Script --sessions --search "funboost"

# List agent presets (all fields)
& $Python $Script --presets

# List users and permissions
& $Python $Script --users

# Full checkpoint messages for a specific session
& $Python $Script "session-uuid-here"

# Tool calls for a specific session
& $Python $Script --tools "session-uuid-here"
```

## Database Locations

| DB | Path | Contents |
|----|------|---------|
| Data | `D:\codes\lc-agent-bfzs\bfzs_data.db` | sessions, agent_presets, users |
| Checkpoint | `D:\codes\lc-agent-bfzs\bfzs_checkpoints.db` | LangGraph state with messages |
