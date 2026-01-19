---
name: generate-newsletter-digest
description: Generate a digest of newsletters since the last briefing, extracting high-value facts and ideas
allowed-tools: ["Read", "Write", "Bash", "Task", "Glob", "MCPSearch"]
---

# Generate newsletter digest

Analyse newsletters since the last briefing and generate a summary file extracting high-value facts and ideas based on interests and current priorities.

## Output file

`/Users/ph/.claude/skills/chief-of-staff/state/newsletter-digests/YYYY-MM-DD.json`

## Workflow

### Step 1: Get last briefing timestamp

Read `/Users/ph/.claude/skills/chief-of-staff/state/briefings.jsonl` and find the most recent entry's timestamp.

If no entries exist, use 7 days ago as the default (newsletters accumulate more slowly than code chats).

### Step 2: Build context

Load these files to understand current priorities:

1. **Interests**: `/Users/ph/.claude/skills/chief-of-staff/interests/interests.md`
2. **Week plan**: `/Users/ph/Documents/Projects/plans-and-reviews/work/week-plans/2026-WXX-plan.md` (current week)
3. **Quarterly goals**: `/Users/ph/Documents/Projects/plans-and-reviews/quarterly-goals.md` (if exists)

Extract:
- Topic interests
- Current week's theme and priorities
- Any active projects or initiatives

### Step 3: Fetch newsletters via Gmail MCP

Use the Google Workspace MCP tools to search for newsletters.

**Primary query:**
```
label:$good-newsletters after:{YYYY/MM/DD}
```

Where `{YYYY/MM/DD}` is the last briefing date. Note: Do NOT include `in:inbox` as newsletters are typically auto-archived after labelling.

**Fallback query** (if primary returns few results):
```
(from:substack.com OR from:buttondown.email OR from:beehiiv.com OR from:convertkit.com OR from:mailchimp.com) after:{YYYY/MM/DD}
```

Use `search_gmail_messages` to get message list, then `get_gmail_messages_content_batch` to fetch content.

### Step 4: Pass 1 - Triage with Haiku

Spawn a Haiku Task agent to score and filter newsletters.

**Input to Haiku (per newsletter):**
- Subject line
- From address
- First 1000 characters of content
- Interests summary (from step 2)

**Haiku prompt:**

```
Score this newsletter for relevance to the user's interests and priorities.

INTERESTS:
{interests summary}

CURRENT PRIORITIES:
{week plan priorities}

NEWSLETTER:
Subject: {subject}
From: {from}
Preview: {first 1000 chars}

Output JSON only:
{
  "relevance_score": 0-10,
  "reason": "one sentence explaining score",
  "topics_matched": ["list of matched interest topics"],
  "skip_reason": "reason if score < 5, else null"
}

Scoring guide:
- 8-10: Directly relevant to current work or core interests
- 5-7: Generally interesting, matches broader interests
- 3-4: Tangentially relevant
- 0-2: Not relevant or pure promotion
```

**Process in parallel** - spawn multiple Haiku agents simultaneously for efficiency.

**Filter:** Keep newsletters with `relevance_score >= 5`. Target ~15 newsletters maximum.

### Step 5: Pass 2 - Extract with Sonnet

For each shortlisted newsletter, spawn a Sonnet Task agent to extract high-value content.

**Truncate** each newsletter to first 10,000 characters before processing.

**Sonnet prompt:**

```
Extract high-value facts and ideas from this newsletter.

CONTEXT:
User interests: {interests}
Current week theme: {theme}
Current priorities: {priorities}

NEWSLETTER:
Subject: {subject}
From: {from}
Content:
{content, truncated to 10000 chars}

Output this exact JSON structure:
{
  "source": "{from name or publication}",
  "subject": "{subject}",
  "relevance_to_current_work": "one sentence on how this relates to current priorities, or null if not directly relevant",
  "facts": [
    {
      "type": "product|organisation|funding|research|event",
      "content": "specific fact",
      "significance": "why this matters"
    }
  ],
  "ideas": [
    {
      "type": "framework|approach|contrarian|prediction|lesson",
      "content": "the idea",
      "source_quote": "relevant quote if present, else null"
    }
  ],
  "quotes": [
    {
      "text": "the quote",
      "attribution": "who said it"
    }
  ],
  "action_items": [
    {
      "type": "tool_to_try|person_to_follow|event_to_attend|idea_to_apply",
      "content": "specific action",
      "urgency": "high|medium|low"
    }
  ]
}

Rules:
- Only extract genuinely valuable content, not filler
- Be specific - "AI tool" is bad, "Claude Code by Anthropic" is good
- Prioritise facts and ideas over quotes
- Action items should be concrete and actionable
- Empty arrays are fine if nothing valuable
- Output valid JSON only
```

**Process in parallel** - spawn multiple Sonnet agents simultaneously.

### Step 6: Aggregate results

Combine all extractions into a single digest:

```json
{
  "generated": "ISO timestamp",
  "period": {
    "from": "last briefing timestamp",
    "to": "now"
  },
  "context_snapshot": {
    "week_theme": "from week plan",
    "priorities": ["list of current priorities"]
  },
  "newsletter_count": 12,
  "newsletters_processed": [
    {
      "source": "Publication name",
      "subject": "Subject line",
      "relevance_score": 8,
      "relevance_to_current_work": "...",
      "facts": [...],
      "ideas": [...],
      "quotes": [...],
      "action_items": [...]
    }
  ],
  "aggregated": {
    "top_facts": [
      {
        "content": "...",
        "type": "...",
        "significance": "...",
        "source": "which newsletter"
      }
    ],
    "top_ideas": [
      {
        "content": "...",
        "type": "...",
        "source_quote": "...",
        "source": "which newsletter"
      }
    ],
    "action_items": [
      {
        "content": "...",
        "type": "...",
        "urgency": "...",
        "source": "which newsletter"
      }
    ],
    "mentions_of_current_projects": [
      {
        "project": "which priority/project",
        "mention": "what was mentioned",
        "source": "which newsletter"
      }
    ]
  }
}
```

**Aggregation rules:**
- `top_facts`: Select 5-7 most significant facts across all newsletters
- `top_ideas`: Select 3-5 most interesting ideas
- `action_items`: All high/medium urgency items
- `mentions_of_current_projects`: Any content directly relevant to week plan priorities

### Step 7: Write output

1. Create directory if needed: `/Users/ph/.claude/skills/chief-of-staff/state/newsletter-digests/`
2. Write to `/Users/ph/.claude/skills/chief-of-staff/state/newsletter-digests/YYYY-MM-DD.json`
3. Report summary: "Generated digest for N newsletters. Top facts: X, Top ideas: Y, Action items: Z"

## Edge cases

- **No newsletters since last briefing**: Write a JSON file with `newsletter_count: 0` and empty arrays
- **Gmail label doesn't exist**: Fall back to domain-based query
- **Very long newsletter**: Truncate to 10,000 characters before Sonnet processing
- **Sonnet parse failure**: Include raw response in `"parse_error"` field
- **No week plan found**: Use interests only for context, note in output

## MCP tools required

- `search_gmail_messages`: Find newsletters
- `get_gmail_messages_content_batch`: Fetch newsletter content
- `get_gmail_message_content`: Fetch individual newsletter (fallback)

## State file paths

- Briefings log: `/Users/ph/.claude/skills/chief-of-staff/state/briefings.jsonl`
- Interests: `/Users/ph/.claude/skills/chief-of-staff/interests/interests.md`
- Week plans: `/Users/ph/Documents/Projects/plans-and-reviews/work/week-plans/`
- Output directory: `/Users/ph/.claude/skills/chief-of-staff/state/newsletter-digests/`

## Token efficiency

- Pass 1 (triage) uses only subject + preview (fast, cheap with Haiku)
- Only fetch full content for ~15 shortlisted newsletters
- Truncate each to 10,000 characters before Sonnet extraction
- Parallel processing minimises wall-clock time
- Estimated cost per run: ~$0.40
