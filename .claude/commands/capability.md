---
name: capability
description: Add or manage AI capability ideas in the pipeline
allowed-tools: ["Read", "Write", "Bash", "AskUserQuestion"]
---

# Manage capability pipeline

Add, view, or update AI capability ideas in the pipeline.

## Usage

```
/capability                           # List current pipeline
/capability add "Name of capability"  # Add new idea
/capability done [id]                 # Mark as built
/capability remove [id]               # Remove from pipeline
```

## Instructions

### List pipeline (no args)

1. Read `/Users/ph/.claude/skills/chief-of-staff/state/capability-pipeline.jsonl`
2. Display as a formatted table:
   ```
   | ID | Name | Value | Effort | Status | Notes |
   |...
   ```
3. Highlight quick wins (high value + low effort)

### Add new capability

1. Parse the capability name from arguments
2. Ask user for:
   - Value rating (high/medium/low)
   - Effort estimate (high/medium/low)
   - Brief notes (optional)
3. Generate a kebab-case ID from the name
4. Append to pipeline file

### Mark as done

1. Find entry by ID
2. Update status to "built"
3. Add completion timestamp

### Remove

1. Find entry by ID
2. Remove from pipeline (rewrite file without that entry)

## Pipeline file format

Each line in `capability-pipeline.jsonl` is a JSON object:

```json
{"id": "meeting-prep", "name": "Meeting prep automation", "value": "high", "effort": "low", "status": "idea", "notes": "Pull Granola context, summarise person's recent work", "created": "2026-01-11T10:00:00"}
```

## Status values

- `idea` - Just an idea, not yet scoped
- `scoped` - Has a detailed plan
- `in_progress` - Currently being built
- `built` - Completed and available
- `deferred` - Postponed for later

## State file path

`/Users/ph/.claude/skills/chief-of-staff/state/capability-pipeline.jsonl`

## Quick win detection

A capability is a "quick win" if:
- Value is "high" or "medium"
- Effort is "low"
- Status is "idea" or "scoped"

Surface these prominently in listings and morning briefings.
