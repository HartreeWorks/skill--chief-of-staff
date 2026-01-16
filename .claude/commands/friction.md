---
name: friction
description: Log a friction point - something you struggled with that might benefit from automation
allowed-tools: ["Read", "Write", "Bash"]
---

# Log friction point

Log a friction point to help identify recurring struggles that could be automated.

## Usage

```
/friction "Description of what you struggled with"
```

## Instructions

1. Parse the user's description from the command arguments
2. Read the existing friction log from `/Users/ph/.claude/skills/chief-of-staff/state/friction-log.jsonl`
3. Check if a similar friction point already exists (fuzzy match on description)
4. If similar exists, note this is a recurring issue
5. Append the new entry to the friction log
6. Confirm to the user and note if this is a recurring pattern

## Friction log format

Each line in `friction-log.jsonl` is a JSON object:

```json
{"timestamp": "2026-01-11T14:32:00", "description": "Finding right Toggl project", "tags": [], "resolved": false}
```

## Output format

After logging:

```
✓ Logged friction point: "[description]"

[If recurring: "⚠️ This is the Nth time you've logged a similar issue. Consider creating automation."]
```

## State file path

`/Users/ph/.claude/skills/chief-of-staff/state/friction-log.jsonl`

## Tag inference

Automatically infer tags from common keywords:
- "toggl" → `["toggl", "time-tracking"]`
- "email" or "gmail" → `["email", "communication"]`
- "invoice" or "billing" → `["invoicing", "finance"]`
- "calendar" or "schedule" → `["calendar", "scheduling"]`
- "slack" → `["slack", "communication"]`
