---
name: generate-chat-digest
description: Generate a digest of Claude Code chats since the last briefing
allowed-tools: ["Read", "Write", "Bash", "Task", "Glob"]
---

# Generate Claude Code chat digest

Analyze Claude Code chats since the last briefing and generate a summary file.

## Output file

`/Users/ph/.claude/skills/chief-of-staff/state/claude-code-summaries/YYYY-MM-DD.json`

## Workflow

### Step 1: Get last briefing timestamp

Read `/Users/ph/.claude/skills/chief-of-staff/state/briefings.jsonl` and find the most recent entry's timestamp.

If no entries exist, use 24 hours ago as the default.

### Step 2: Filter history.jsonl

Read `~/.claude/history.jsonl` and parse each line as JSON. Each entry looks like:

```json
{"sessionId": "abc123", "timestamp": "2026-01-16T14:30:00Z", "cwd": "/Users/ph/Documents/Projects/2025-09-forethought-ai-uplift", "projectId": "...", "totalToolUseCalls": 42}
```

Filter to entries where:
- `timestamp` is after the last briefing timestamp

Extract unique `sessionId` values along with their `cwd` (working directory).

### Step 3: Load projects index

Read `/Users/ph/Documents/Projects/projects.yaml` to build a mapping of folder name → project info.

### Step 4: Analyze each chat with Haiku

For each unique sessionId:

1. Check if debug log exists at `~/.claude/debug/{sessionId}.txt`
2. If exists, spawn a Haiku Task agent to analyze it

**Spawn agents in parallel** for efficiency. Use `model: "haiku"` in the Task tool.

Haiku prompt for each chat:

```
Analyze this Claude Code chat log and output JSON only.

WORKING DIRECTORY: {cwd}
PROJECT CONTEXT: {project_name if matched, else "Unknown"}

CHAT LOG:
{first 50000 characters of debug log}

Output this exact JSON structure:
{
  "summary": "2-4 sentence description of what was actually built, changed, or worked on. Be specific about features, components, or functionality - not vague descriptions.",
  "tasks_completed": ["list of specific completed deliverables - e.g. 'Added JWT authentication to login endpoint' not 'worked on auth'"],
  "tasks_in_progress": ["list of specific tasks that seem unfinished or were left mid-way"],
  "blockers": ["any issues, errors, or problems that weren't resolved by end of chat"],
  "key_files": ["important files modified, max 5"],
  "notable": "One sentence highlight if something significant was completed (leave empty string if nothing notable)"
}

Rules:
- Be SPECIFIC - summaries should mention actual features, files, or functionality
- Extract actual task names from todo lists if visible in the log
- Look for Write/Edit tool calls to identify what files were actually changed
- Look for error messages or failed commands to identify blockers
- Only include blockers that weren't resolved by end of chat
- key_files should be relative paths where possible
- Output valid JSON only, no explanation text
```

### Step 5: Match projects

For each chat, determine the project:

1. Extract folder name from cwd: `/Users/ph/Documents/Projects/{folder}/...` → folder
2. If folder matches a project in projects.yaml, use that project's name and type
3. Special cases:
   - If cwd contains `~/.claude/skills`, group as "Claude Code skills" (type: tools)
   - If cwd contains `~/.claude`, group as "Claude Code config" (type: tools)
4. Otherwise, set `managed_project` to null and let the summary's context speak for itself

### Step 6: Aggregate results

Combine all Haiku outputs into a single JSON structure:

```json
{
  "generated": "ISO timestamp",
  "period": {
    "from": "last briefing timestamp",
    "to": "now"
  },
  "chat_count": 5,
  "chats": [
    {
      "chat_id": "sessionId",
      "working_dir": "/full/path",
      "managed_project": {
        "folder": "2025-09-forethought-ai-uplift",
        "name": "Forethought Research AI Uplift",
        "type": "client"
      },
      "summary": "2-4 sentence specific description...",
      "tasks_completed": [],
      "tasks_in_progress": [],
      "blockers": [],
      "key_files": [],
      "notable": ""
    }
  ],
  "by_project": {
    "Forethought Research AI Uplift": {
      "type": "client",
      "chat_count": 2,
      "combined_summary": "2-4 sentence summary combining all sessions - be specific about what was actually built",
      "all_tasks_completed": ["specific deliverables..."],
      "all_tasks_in_progress": ["specific unfinished work..."],
      "all_blockers": ["any unresolved issues..."]
    },
    "Claude Code skills": {
      "type": "tools",
      "chat_count": 1,
      "combined_summary": "...",
      "all_tasks_completed": ["..."],
      "all_tasks_in_progress": [],
      "all_blockers": []
    }
  },
  "key_completions": ["Top 3-5 most notable completions across all projects"],
  "still_in_progress": ["Significant unfinished work that may need attention"],
  "all_blockers": ["Any unresolved issues across all chats"]
}
```

### Step 7: Write output

1. Create directory if needed: `/Users/ph/.claude/skills/chief-of-staff/state/claude-code-summaries/`
2. Write to `/Users/ph/.claude/skills/chief-of-staff/state/claude-code-summaries/YYYY-MM-DD.json`
3. Report summary: "Generated digest for N chats across M projects"

## Edge cases

- **No chats since last briefing**: Write a JSON file with `chat_count: 0` and empty arrays
- **Missing debug log**: Skip that chat but note it in output as `"debug_log_missing": true`
- **Very large debug log**: Truncate to first 50,000 characters before sending to Haiku
- **Haiku parse failure**: If Haiku returns invalid JSON, include raw response in `"parse_error"` field

## State file paths

- Briefings log: `/Users/ph/.claude/skills/chief-of-staff/state/briefings.jsonl`
- History file: `~/.claude/history.jsonl`
- Debug logs: `~/.claude/debug/{sessionId}.txt`
- Projects index: `/Users/ph/Documents/Projects/projects.yaml`
- Output directory: `/Users/ph/.claude/skills/chief-of-staff/state/claude-code-summaries/`
