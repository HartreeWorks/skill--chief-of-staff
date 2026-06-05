---
name: chief-of-staff
description: Run Peter's daily briefings, schedule refreshes, and recaps.
---

# Chief of Staff

A lean daily briefing scannable in 30 seconds. Focuses on what matters: schedule, week priorities, and yesterday's agent work.

## Morning briefing workflow

### Step 1: Load context

**Dispatch these sources as parallel subagents**—one per source-group, and one per Google account for email—rather than loading them sequentially. They are almost entirely independent, so fanning out cuts the briefing's wall-clock time substantially. Delegate the pure lookups (calendar, day tracker, Todoist, Claude Code summaries, raw email/WhatsApp fetches) to Haiku subagents. Keep the judgement calls in the main loop: which emails genuinely need a reply, which WhatsApp messages clear the bar, and the final assembly. Attendee context is one chain per attendee (resolve person → read project files), but attendees are independent of each other, so they fan out too.

Gather information from these sources:

| Source | Location | What to extract |
|--------|----------|-----------------|
| Week plan | `/Users/ph/Documents/Projects/plans-and-reviews/work/week-plans/2026-WXX-plan.md` | Key results, day-by-day, **week mantra** |
| Calendar | Both calendars (see [Fetching calendar events](#fetching-calendar-events)) | Today's events |
| Calendar attendee context | `~/.agents/data/people.json` + per-attendee project `CLAUDE.md` / `AGENTS.md` | Who each attendee is, default project, recent context |
| Day tracker | `/Users/ph/Documents/day-tracker/data/daily/YYYY-MM-DD.json` | Yesterday's activity |
| Claude Code summaries | `data/claude-code-summaries/YYYY-MM-DD.json` | Yesterday's Claude Code + Codex work |
| Previous week review (Mondays only) | `/Users/ph/Documents/Projects/plans-and-reviews/work/week-reviews/2026-WXX-review.md` | How the previous week went—accomplishments, misses, ratings, reflections |
| Todoist overdue carryovers | `td` CLI | Tasks due in the previous 7 days that are still incomplete |
| Email triage | `gog gmail search` (3 accounts) | Important emails needing a timely reply |
| WhatsApp (last 24h) | `ssh mini` + sqlite3 against bridge DB | Notable personal messages: LTP, family, close friends, commitments |

**Monday context:** On Mondays, also look for the previous week's review at `work/week-reviews/2026-W{XX-1}-review.md`. If it exists, read it and use it to enrich the "Week priorities" section (mark items as done/missed based on the review) and the "What can I help with?" suggestions (e.g. carry forward unfinished work, flag patterns from the review). If no review exists, note that in the briefing and suggest running `/week-review` first.

**Calendar attendee context:** For each named attendee of today's events (excluding Peter), look them up in the people registry at `~/.agents/data/people.json`. The key convention is `<first>-<last>` lowercased and hyphenated (e.g. "Jane Smith" → `jane-smith`).

If the attendee's entry has a `default_project` value (e.g. `ai-wow`, `coaching-client`, `acme-corp`):

1. Resolve the project name to a folder path via `~/.agents/references/project-map.md`.
2. Read both `CLAUDE.md` and `AGENTS.md` from that project folder (either or both may exist).
3. If those files name a per-person notes file in the project's `context/` folder (e.g. `context/ph-js-weekly-calls.md`), read that too.

Use the loaded context to write the "Notes" column for that event — what the standing relationship is, what was last discussed, what's pending. This is what catches things like "Jane Smith = AI Wow peer mentor, weekly check-in" without guessing.

If the attendee is **not** in the registry, write "No project context — unregistered" in the Notes column rather than inferring. If it looks like a recurring relationship, suggest registering them via `/summarise-granola` (which has a "register unregistered people" step).

**Todoist overdue check:** Every morning briefing should check `td` for incomplete tasks due in the previous 7 days. Mention them explicitly somewhere in the briefing (usually in **Week priorities**, **Yesterday**, or a short **Overdue tasks** subsection if there are several).

Suggested approach:
```bash
# Get tasks due in the last 7 days that are still incomplete.
# Note: `td task list` only returns active (non-completed) tasks, so no !completed clause is needed
# — including it returns HTTP 400 because Todoist's filter syntax doesn't support it.
td task list --filter "due after: -8 days & due before: today" --json
```

If that returns nothing, there are no recent overdue tasks—omit the section. For each overdue task, include content, due date, and project (if available). If there are many, group by project.

**Email triage:** Search all three accounts for emails that likely need a timely reply. Run these searches:

```bash
# Personal account — unread inbox, last 3 days
gog --json gmail search 'label:inbox is:unread newer_than:3d' --account your-email@gmail.com --max 30

# T3A account — unread inbox, last 3 days
gog --json gmail search 'label:inbox is:unread newer_than:3d' --account your-email@example.com --max 20

# IWR account — unread inbox, last 3 days
gog --json gmail search 'label:inbox is:unread newer_than:3d' --account your-product@gmail.com --max 20
```

From the results, select emails that are **actually important and likely need a reply**. Use judgement, but always include:
- Any TYPE III AUDIO client (check sender against known clients)
- Emails from current advisory-client domains
- Emails from your accountant
- Personal emails from real humans that look time-sensitive

If `data/triage-allowlist.md` exists, read it for the specific high-priority senders to always include (client domains, accountant addresses, etc.). This file is local-only and never published.

Always **exclude**:
- Todoist task notification emails
- Newsletters, marketing, automated notifications
- Receipts, shipping updates, and other transactional noise

**Prefer false positives over false negatives.** Peter will give feedback to reduce noise over time.

If no important emails are found, omit the section entirely.

**No Slack mentions.** Peter checks those at lunchtime. Urgent items reach him via Signal/push.

**WhatsApp (last 24h):** Query the bridge DB on mini for messages in the last 24 hours. Full schema and query patterns: `/Users/ph/.agents/references/whatsapp-bridge.md`. Use the reference's standard queries with `FROM` = 24h ago, which already filter out noisy groups (>3 distinct senders) and empty-content rows.

Scan for anything that genuinely deserves Peter's attention today: questions awaiting a reply, plans being made for today/this week, emotional or LTP-related threads, commitments to follow up on. Be highly selective — most WhatsApp volume is chit-chat or logistics that doesn't need surfacing. Include at most a handful of bullets under a `## WhatsApp` section, or omit entirely if nothing rises to the bar. Err on the side of omission for the daily briefing (unlike email, where false positives are OK).

**Never send WhatsApp messages. Read-only.**

**Week number calculation:** Use ISO week format (2026-WXX).

**Day tracker summary generation:**

Before reading day-tracker data, ensure yesterday's summary exists:

1. Check if yesterday's JSON has a `summary` object: `cat /Users/ph/Documents/day-tracker/data/daily/YYYY-MM-DD.json | python3 -c "import json,sys; print('Has summary:', 'summary' in json.load(sys.stdin))"`
2. If missing, generate it:
   ```bash
   cd /Users/ph/.claude/skills/day-tracker && python3 cli.py summary YYYY-MM-DD
   ```
3. Then read the summary from the JSON file

**Claude Code + Codex digest:**

Read from the day-tracker completions sidecar file:
```bash
cat /Users/ph/Documents/day-tracker/data/daily/YYYY-MM-DD.completions.json
```

If the file doesn't exist, run the rollup first:
```bash
cd /Users/ph/.agents/skills/day-tracker && python3 scripts/daily-rollup.py YYYY-MM-DD
```

The `agent_sessions` key contains session counts grouped by project. Other keys (`git_commits`, `emails_sent`, `google_docs_edited`, `calendar_events`) provide additional context for the briefing.

### Step 2: Present briefing

Display the briefing in chat, save it to `data/briefings/YYYY-MM-DD.md`, update Day.md with today's schedule via `update-day-schedule.py` (see [Fetching calendar events](#fetching-calendar-events)), and open the saved briefing in Typora:
```bash
open -a Typora /Users/ph/.agents/skills/chief-of-staff/data/briefings/YYYY-MM-DD.md
```

Structure the briefing as follows:

```markdown
# Good morning

**[Day] [Date] [Month] [Year] · W[XX]**

> **Mantra:** [Week mantra from the week plan, if set]

## Today's schedule

| Time | Event | Notes |
|------|-------|-------|
| HH:MM | Event name | Contextual insight from week plan / project knowledge |

[If no events before afternoon: "No morning commitments—deep work day."]

## Needs reply

| Sender | Subject | Age | Account | Context |
|--------|---------|-----|---------|---------|
| [Name] | [Subject line] | [e.g. 2d] | [personal / t3a / iwr] | [One-line context: why this matters or what action is needed] |

[Omit this section entirely if no important emails were found.]

## Week priorities

| Priority | Status | Notes |
|----------|--------|-------|
| [Key result from week plan] | [Done / X/Y done / In progress / Not started] | [Concrete progress indicator, what's next] |

## Yesterday

| Project | Sessions | What happened |
|---------|----------|---------------|
| [project-name] | N | One-line summary of work done |

[Day tracker: Xh tracked—breakdown by category]
[Or: "No day tracker data for yesterday."]

## What can I help with?

1. **[Action]** — grounded in today's situation (calendar, week plan, yesterday's unfinished work)
2. **[Action]**
3. **[Action]**
4. **[Action]**
5. **[Action]**
```

**Key rules for content:**

- **Needs reply** is curated from the Gmail search results. Only include emails that genuinely look like they need a human reply. Err on the side of inclusion—Peter will give feedback to tighten the filter.
- **Schedule notes must be contextual and insightful**, drawing on week plan and project knowledge—not just restating calendar entries.
- **Week priorities** are extracted from the current week plan's key results, with concrete progress indicators (e.g. "2/5 done", "Drafted, needs review").
- **Yesterday** comes from the Claude Code + Codex digest. Concise: project, session count (noting source if mixed), one-line summary.
- **"What can I help with?"** must be grounded in today's actual situation. Each option should be something Claude can actually do right now. Not generic.

## Day note update (standalone)

Triggered by `/cos schedule`, `/gm schedule`, or "update day note".

**Use case:** Refresh today's schedule in Day.md mid-day.

**Steps:**

1. Fetch events from both calendars (see [Fetching calendar events](#fetching-calendar-events))
2. Update Day.md via `update-day-schedule.py`
3. Print today's schedule in the chat in `HHMM Event name` format
4. Confirm: `"Day.md updated — N events written"`

**No briefing file saved, no digest generated, no week priorities or yesterday section.**

## Day recap

Triggered by "day recap", "what done", "what have i done", "what did i do", or `/recap`.

**Use case:** Mid-day or end-of-day accountability check. Compare plan vs actual work, flag distractions. Output should be screenshot-friendly (Peter often screenshots it to his accountability partner).

### Step 1: Load context

**Fan these out as parallel subagents**—agent sessions, git commits, active directories, calendar, day tracker, and Mochi are all independent lookups. Delegate them to Haiku and assemble once they return; keep the plan-vs-actual judgement in the main loop.

Gather from these sources:

| Source | How to get it | What to extract |
|--------|--------------|-----------------|
| Week plan | Read current `week-plans/2026-WXX-plan.md` | Today's day-by-day plan, "What I'm NOT doing this week", "Commitments (meta)" |
| Agent sessions | `python3 /Users/ph/.agents/skills/chief-of-staff/generate_digest.py --json` | Sessions since midnight grouped by project |
| Git commits | `git-commits YYYY-MM-DD --json` | All commits today across all repos (replace YYYY-MM-DD with today's date) |
| Active directories | `bash /Users/ph/.agents/scripts/utils/active-directories.sh 16h --no-files` | Which projects had file changes today |
| Calendar (past events) | Both calendars (see [Fetching calendar events](#fetching-calendar-events)) | Meetings that already happened today |
| Day tracker | `/Users/ph/Documents/day-tracker/data/daily/YYYY-MM-DD.json` | Time tracked, category breakdown |
| Mochi reviews | `mochi reviewed --json` | Whether Mochi was done today, how many cards |

**Session discovery:** Use `generate_digest.py --json` for agent sessions only. For git commits, call the day-tracker collector directly (see table above). These are separate systems.

### Step 2: Present recap

Display in chat only—**no file saved**.

```markdown
# Day recap

**[Day] [Date] [Month] · [HH:MM]**

## What you did

| Project | Work | Source |
|---------|------|--------|
| [project] | One-line summary | N sessions, N commits |

[If meetings happened: list them briefly]
[Day tracker: Xh tracked — breakdown by category. Or: "No day tracker data yet."]

## Plan vs actual

**Today's plan:** [Copy the day-by-day line from week plan]

| Planned | Status |
|---------|--------|
| [planned item] | Done / In progress / Not started / Skipped |

## Off-plan check

**"NOT doing" list:**
| Item | Verdict |
|------|---------|
| [item from week plan "NOT doing" section] | Clean / Violated — [evidence] |

**Commitments to accountability partner:**
| Commitment | Verdict |
|------------|---------|
| [commitment from week plan] | Kept / Broken — [evidence] |

## Verdict

[One sentence: on track, drifting, or off-plan. Be direct.]

## Appendix: git commits

[List all git commits from today across all repos, grouped by repo. Use compact format:]

| Time | Repo | Message |
|------|------|---------|
| HH:MM | repo-name | Commit message (first line only) |
```

**Key rules:**

- **Be honest and direct.** The point is accountability, not encouragement. If Peter spent 3 hours on something not in the plan, say so plainly.
- **Evidence-based verdicts.** Every "Violated" or "Broken" must cite specific agent sessions, commits, or active directories as evidence.
- **Screenshot-friendly.** Keep it compact. No verbose descriptions. Tables over prose.
- **"NOT doing" is critical.** The week plan's "What I'm NOT doing this week" section lists specific distractions Peter has committed to avoiding. Check agent sessions and active directories against this list explicitly.
- **Commitments to accountability partner.** The "Commitments (meta)" section in the week plan contains promises like "No podcatcher Mon–Wed". Check these against the evidence.
- **Mochi commitment.** If the week plan includes a Mochi commitment, check `mochi reviewed --json` to verify. Do NOT rely on day-tracker screenshots—Mochi reviews happen on the phone app or via Telegram/Hermes.
- **Time of day matters.** At noon, "Not started" on an afternoon task is fine. At EOD, it's a miss. Calibrate accordingly.

## Data paths reference

```
/Users/ph/Documents/Projects/
├── plans-and-reviews/
│   └── work/
│       └── week-plans/2026-WXX-plan.md
└── [project folders]/CLAUDE.md  # plus AGENTS.md, context/

/Users/ph/.agents/data/
└── people.json  # calendar attendee → default project

/Users/ph/Documents/day-tracker/data/
└── daily/YYYY-MM-DD.json

/Users/ph/.agents/skills/chief-of-staff/
└── data/
    ├── briefings/YYYY-MM-DD.md
    ├── claude-code-summaries/YYYY-MM-DD.json
    └── overnight-results/
```

## Integration with existing skills

| Skill | When to use |
|-------|-------------|
| `week-plan` | Trigger weekly planning |
| `week-review` | Trigger weekly review |
| `call-prep` | Prep for upcoming calls |
| `schedule-task` | Schedule overnight automation |

## Weekly rhythm

| Day | Prompt |
|-----|--------|
| Friday–Sunday | "It's time for your weekly review. Run /week-review?" |
| Sunday–Monday | "Ready to plan next week? Run /week-plan?" |

## Fetching calendar events

Fetch from both calendars:
```bash
gog cal events primary --from today --to today --account your-email@gmail.com
gog cal events your-meetings-calendar-id@group.calendar.google.com --from today --to today --account your-email@gmail.com
```

The Meetings calendar returns times in UTC—add 1h for CET (or 2h for CEST). Merge both calendars, sort by time, format each event as `HHMM Event name`.

Update Day.md by passing each event as an argument:
```bash
python3 /Users/ph/.agents/skills/chief-of-staff/scripts/update-day-schedule.py "0800 Standup" "1400 Call with Alice"
```
No arguments → inserts "No events scheduled."
