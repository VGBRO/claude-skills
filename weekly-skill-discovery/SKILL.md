---
name: weekly-skill-discovery
description: Weekly scan of Claude Code sessions, Slack, and Drive to identify repeatable processes that should become skills. Run every Friday at 9 AM to proactively surface automation candidates.
allowed-tools: Bash, Read, Glob, Grep, mcp__slack__slack_search_public_and_private, mcp__slack__slack_read_thread, mcp__slack__slack_send_message
---

# Weekly Skill Discovery

Scan all available signal sources — Claude Code session transcripts, Slack conversations, and local files — to find repeatable workflows that should become Claude Code skills.

## What to Look For

A good skill candidate is a workflow that:
1. Has been done **more than once** (appears across multiple sessions or messages)
2. Involves **3+ sequential steps** (not trivially short)
3. Is **triggered by a recognizable phrase** ("analyze X", "deploy Y", "generate Z report")
4. Currently requires **manual orchestration** — Claude rediscovering the same steps each time

## Step 1 — Scan Claude Code Session Transcripts

Session files live at:
```
/Users/vguruvugari/.claude/projects/-Users-vguruvugari-claude-bot-to-agent-migration-dev/*.jsonl
```

For each `.jsonl` file modified in the last 7 days:

```bash
# Find recent sessions (last 7 days)
find /Users/vguruvugari/.claude/projects/-Users-vguruvugari-claude-bot-to-agent-migration-dev/ \
  -name "*.jsonl" -newer $(date -v-7d +%Y-%m-%d 2>/dev/null || date -d "7 days ago" +%Y-%m-%d) \
  -type f
```

For each recent session, extract human turns to understand what the user asked Claude to do:
```bash
cat <session>.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        msg = json.loads(line.strip())
        if msg.get('type') == 'user':
            content = msg.get('message', {}).get('content', '')
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        print(block['text'][:300])
            elif isinstance(content, str):
                print(content[:300])
    except: pass
"
```

Look for patterns across sessions:
- Tasks that follow similar **multi-step flows** (e.g., always: retrieve → analyze → generate → deploy)
- Repeated **invocation phrases** across multiple sessions
- Long conversations where Claude rediscovered the same process each time

## Step 2 — Scan Slack for Repeated Requests

Use the Slack MCP to search for messages from `vguruvugari` in the past 7 days that contain process-oriented language:

```
Search queries to run:
- "can you help me with" from:vguruvugari
- "how do I" from:vguruvugari  
- "run the" OR "execute" OR "generate" from:vguruvugari
- "every time" OR "each time" OR "whenever" from:vguruvugari
```

For each match, read the thread to understand the full workflow.

Identify recurring themes — same type of request appearing across multiple threads.

## Step 3 — Scan Local Files for Repeated Patterns

Look for signs of manual repetition in the working directory:

```bash
# Find files modified multiple times recently (bash history patterns)
ls -lt /Users/vguruvugari/claude/bot-to-agent-migration-dev/data/ 2>/dev/null | head -20

# Look for scripts/notebooks that run similar operations
find /Users/vguruvugari/claude/bot-to-agent-migration-dev -name "*.py" -newer $(python3 -c "import time; print(time.strftime('%Y-%m-%d', time.gmtime(time.time()-604800)))") -not -path "*/.git/*" 2>/dev/null

# Check bash history for repeated command sequences
history 2>/dev/null | grep -E "(python|sf|uv|bash)" | sort | uniq -c | sort -rn | head -20
```

## Step 4 — Synthesize Candidates

After scanning all sources, build a ranked list of skill candidates.

For each candidate, fill out this template:

```
## Candidate: <Short Name>

**Pattern observed:** <What you saw repeated — quote specific examples>
**Sources:** Sessions: [list session IDs or dates] | Slack: [thread URLs if any]
**Trigger phrase:** "<The phrase the user typically uses to kick this off>"
**Steps involved:**
  1. <Step 1>
  2. <Step 2>
  3. <Step 3>
**Why a skill:** <Why this is better as a skill vs. rediscovered each time>
**Effort to build:** Low / Medium / High
**Impact:** Low / Medium / High
```

Rank by **Impact × (1/Effort)** — highest value, lowest effort first.

## Step 5 — Deliver Report via Slack

Send a DM to user `U01GXQK9UE4` (vguruvugari) with the findings:

**Message format:**
```
🔍 *Weekly Skill Discovery — [Date]*

Scanned [N] sessions, [N] Slack threads, [N] local files.

*Top skill candidates this week:*

1. *[Name]* — [one-line description]
   Trigger: "[phrase]"
   Seen: [N] times across [sources]
   Effort: [Low/Med/High] | Impact: [Low/Med/High]

2. *[Name]* — [one-line description]
   ...

[If nothing significant found:]
No high-signal candidates this week. Patterns are diverse — no single workflow dominated.

---
To build any of these: reply or open Claude Code and say `/weekly-skill-discovery build <name>`
```

If there are **zero** candidates worth building: send a brief "no strong candidates this week" message rather than padding with weak ones.

## Step 6 — Auto-Build (Optional Extension)

If triggered with argument `build <name>`:
1. Re-read the candidate's observed pattern from transcript/Slack evidence
2. Draft a SKILL.md following the format of existing skills in `.claude/skills/`
3. Place it at `.claude/skills/<kebab-case-name>/SKILL.md`
4. Report what was built and how to invoke it

## Notes

- **Do not fabricate patterns.** Only report what you actually observed in the transcripts/Slack. If sessions are sparse, say so.
- **Existing skills to exclude** (already built): `00-verify-prerequisites`, `01-retrieve-bots-metadata`, `02-process-einstein-bot`, `03-generate-topic-dialog-action-mappings`, `04-generate-agentscript`, `05-compile-agentscript`, `06-deploy-agent-to-org`, `07-generate-agent-tests`, `08-execute-agent-tests`, `09-generate-roi-report`, `slack-research`, `weekly-skill-discovery`
- **Session privacy:** Transcripts may contain sensitive data. Only extract task/workflow patterns, never quote credentials, org IDs, or personal data in the Slack report.
