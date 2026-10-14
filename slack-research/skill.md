---
name: slack-research
description: Use Slackbot AI on salesforce-internal.slack.com to research any question. Leverages the saved session so no manual login is required. Use when the user asks to "research X on Slack", "ask Slackbot about X", "check Slack for X", or wants to use internal Salesforce Slack tools for research.
allowed-tools: Bash(npx agent-browser:*)
---

# Slack Research via Slackbot AI

Use this skill to send a research query to Slackbot AI on the Salesforce internal Slack instance and return the response. The session is pre-authenticated — no manual login needed.

## Auth state
Saved session: `.claude/skills/agent-browser/slack-auth.json`
Workspace: `https://salesforce-internal.slack.com/`

## Workflow

```bash
# 1. Open Slack with saved session
npx agent-browser --state .claude/skills/agent-browser/slack-auth.json open https://salesforce-internal.slack.com/

# 2. Wait for load
npx agent-browser wait --load networkidle

# 3. Open Slackbot AI
npx agent-browser snapshot -i
# Find the "Chat with Slackbot AI" button and click it
npx agent-browser click @eN   # ref for "Chat with Slackbot AI"

npx agent-browser wait 1000
npx agent-browser snapshot -i

# 4. Find the message textbox (ref for "Message to Slackbot") and fill + send
npx agent-browser fill @eN "<USER_QUERY>"
npx agent-browser click @eN   # ref for "Send message"

# 5. Wait for response and read it
npx agent-browser wait 5000
npx agent-browser snapshot -i
# Read the response from the latest Slackbot listitem
npx agent-browser get text @eN

# 6. Screenshot for confirmation
npx agent-browser screenshot /tmp/slackbot-response.png
```

## Notes
- Always re-snapshot after each action to get fresh refs
- Slackbot AI may take a few seconds to respond — wait at least 5s before reading
- If session has expired, user must re-login manually in headed mode:
  `npx agent-browser --headed open https://salesforce-internal.slack.com/`
  then save state again:
  `npx agent-browser state save .claude/skills/agent-browser/slack-auth.json`
