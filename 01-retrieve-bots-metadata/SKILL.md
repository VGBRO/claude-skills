---
name: retrieve-bots-metadata
description: >
  Retrieve Bot Metadata. Interactive conversational interface for fetching Einstein Bot
metadata:
   author: salesforce-migration
   version: "3.0-ux-step1"
   pipeline-order: "1"
   ux-spec: "Einstein Bots → Agentscript Converter - Step 1"
compatibility: Requires Salesforce CLI (sf), Python 3.7+, authenticated org access

# Step 1 — Retrieve Bot Metadata from SF Org

## Purpose

This is **Step 1 of the 6-step Einstein Bots → Agentforce Converter pipeline**. It provides an interactive conversational interface for retrieving bot metadata from Salesforce orgs, including complete ML training data.

## Pipeline Context

```
┌──────────────────────────────────────────────────────────────┐
│  Einstein Bots → Agentforce Converter Pipeline               │
│                                                               │
│  Step 1: Retrieve Metadata        ◀── YOU ARE HERE           │
│  Step 2: Bot Inventory                                        │
│  Step 3: Mapping Plan                                         │
│  Step 4: Generate Script                                      │
│  Step 5: Compile & Validate                                   │
│  Step 6: Create Agent                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Activation

This skill activates when the user:
- Says "proceed" from the pipeline welcome screen (Step 0)
- Says "start bot migration" or similar
- Invokes `/01-retrieve-bots-metadata` directly
- Wants to fetch a bot from a Salesforce org

---

## Conversational Flow

**🚨 CRITICAL RULES - READ THIS FIRST 🚨**

1. **NEVER AUTO-SELECT ANYTHING**
   - ❌ Never auto-select org (always show list, ask user to choose)
   - ❌ Never auto-select bot (always show list, ask user to choose)
   - ❌ Never auto-select version (always show list, ask user to choose)
   - ❌ Never remember previous selections across sessions
   - ✅ Always show full list and wait for user input

2. **SINGLE CONTINUOUS SCRIPT EXECUTION**
   - ❌ Never restart the script multiple times
   - ❌ Never call non-interactive mode when user is selecting
   - ✅ Use ONE bash command with piped input: `printf "1\n1\ny\n" | bash fetch_bot_from_org.sh interactive <ORG>`
   - ✅ Feed all selections (bot, version, confirmation) in one continuous stdin stream

3. **RESPECT USER'S VERSION CHOICE**
   - ❌ Never query org for "latest version" - that ignores user's selection
   - ❌ Never bypass the Python selector's SELECTED_VERSION output
   - ✅ User selects version 1 → Script uses version 1 (not version 2)
   - ✅ Continuous script execution preserves SELECTED_VERSION variable

### Phase 1.1: Org Connection & Selection

**Never automatically select an org. Always show user the list of available orgs.**

When this skill activates, display the Step 1 header and check for authenticated orgs:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Einstein Bots → Agentscript Converter  |  Step 1 of 6
  Retrieve Bot Metadata
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verifying Salesforce CLI authentication...
```

**IMPORTANT: You MUST wait for up to 5 minutes for ALL `sf` CLI commands to complete.** Do
not cancel, retry, or re-run the same `sf` command without first giving it adequate time to
finish. Salesforce CLI operations (especially org-related commands) can be slow depending on
network conditions and org size.

**Check org authentication:**
```bash
sf org list --json
```

**If orgs are found, display list:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AUTHENTICATED ORGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  #   Org Alias           Username                              Status
  ─   ─────────────────   ───────────────────────────────────   ──────────
  1   orgfarm-epic        epic.out.b9fcfa00@orgfarm.sf.com     Connected
  2   my-sandbox          user@company.com.sandbox              Connected
  3   production          user@company.com                      Connected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Would you like to use one of these orgs or login to a different org?

  [1-N]   Select an org from the list
  [login] Login to a different org
  [quit]  Exit
```

**Natural Language Understanding:**

Accept:
- "1" / "select 1" / "use orgfarm-epic" / "orgfarm-epic"
- "login" / "new" / "different" / "authenticate to new org"
- "quit" / "exit"

**If user selects a number:**
```
✅  Selected: orgfarm-epic (epic.out.b9fcfa00@orgfarm.sf.com)

Fetching available bots...
```

Proceed to Phase 1.2.

**If user types "login" or wants to authenticate to different org:**
```
To authenticate to a new Salesforce org, run this command:

  sf org login web --instance-url <ORG_LOGIN_URL> --alias <CUSTOM_NAME>

Example:
  sf org login web --instance-url https://orgfarm-7532d67587.test1.my.pc-rnd.salesforce.com/ --alias my-new-org

After authenticating, re-run: /01-retrieve-bots-metadata
```

**User can change their mind:**
If user says "wait, use existing org" or "show me the orgs again" or "back":
- Re-display the org list from Phase 1.1
- Let them select from existing orgs
- Continue to Phase 1.2 with selected org

**After user authenticates:**
When user re-invokes the skill after running `sf org login web`:
- Check `sf org list --json` again
- Display updated org list (including the newly authenticated org)
- Ask them to select an org
- Continue to Phase 1.2 with selected org

**If no orgs found:**
```
❌  No authenticated Salesforce orgs found.

To authenticate to a Salesforce org, run:

  sf org login web --instance-url <ORG_LOGIN_URL> --alias <CUSTOM_NAME>

Example:
  sf org login web --instance-url https://orgfarm-7532d67587.test1.my.pc-rnd.salesforce.com/ --alias orgfarm-epic

After authenticating, re-run: /01-retrieve-bots-metadata
```

Exit the skill and wait for user to authenticate and re-invoke.

---

### Phase 1.2: Bot List Display

**Run interactive bot query:**

Execute:
```bash
bash .claude/skills/01-retrieve-bots-metadata/scripts/fetch_bot_from_org.sh interactive <ORG_ALIAS>
```

This invokes the existing `list_bots_interactive.py` script which queries and displays bots.

**IMPORTANT: Read the script output and display the bot list to the user.**

The script will output a formatted table. **You MUST read the Bash tool output and extract the bot list to show the user.** Look for the section that starts with "AVAILABLE BOTS".

**DO NOT say any of these phrases:**
- ❌ "The script is waiting for your selection"
- ❌ "The script is waiting for your input"  
- ❌ "Please select a bot"
- ❌ Any mention of "waiting" or "script"

**INSTEAD, immediately show the bot list from the script output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AVAILABLE BOTS  (Org: <OrgName>)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  #   Bot Name                            Description
  ─   ──────────────────────────────────  ────────────────────────────────────────────────────────────────
  1   Customer Service Bot                Customer service bot for airline services and bookings
  2   Fitness Assistant                   Fitness assistant for class bookings and memberships
  3   Support Bot                         General support bot with intent routing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [1–3]   Select a bot
  [quit]  Exit

Which bot would you like to convert?
```

**Note**: Bot names shown are **MasterLabels** (user-friendly display names), not DeveloperNames. The script internally uses DeveloperNames for all Salesforce operations. Only Bot Name and Description are shown; version information appears after bot selection.

**The bot list table IS the prompt for user input.** Don't add any extra text before it.

**Handle edge cases:**

- **No bots found:**
  ```
  ❌ No Einstein Bots found in this org.
  ```
  
- **More than 20 bots:**
  List first 20 and add pagination:
  ```
  [more]  Show next 20 bots
  ```

**Natural Language Understanding:**

Accept these variations:
- "select bot 1" / "1" / "bot 1" / "first one"
- "select CustomerServiceBot" / "Emirates Bot"
- "show me the Emirates bot"
- "quit" / "exit" / "cancel"

Map these to the appropriate bot selection or exit.

**Conversation Examples:**

```
User: select 2
Claude: ✅  Selected: FitnessAssistantBot
        Fetching versions...
        [Proceeds to Phase 1.3]

User: I want the Emirates bot
Claude: ✅  Selected: CustomerServiceBot
        Fetching versions...
        [Proceeds to Phase 1.3]

User: quit
Claude: Exiting bot selection. You can restart with /01-retrieve-bots-metadata
```

---

### Phase 1.3: Version List Display

**Once bot is selected, ALWAYS show versions - even if only one version exists:**

**Important**: Never auto-select a version, even if the bot has only one version. Always display the version list and let user confirm.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  VERSIONS  —  Customer Service Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  #   Version     Status      Last Modified
  ─   ─────────   ─────────   ──────────────────
  1   v2          Inactive    10 Jan 2026
  2   v3          Inactive    01 Mar 2026
  3   v4          Active      12 Apr 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Versions sorted alphabetically (v1 → v2 → v3...).
  The Active version is recommended for production migrations.

  [1–N]   Select a version
  [back]  Go back to the bot list
  [quit]  Exit
```

**Note**: Header shows **MasterLabel** (e.g., "Customer Service Bot"), while the script internally uses DeveloperName for operations.

**Natural Language Understanding:**

The script prompts: `Enter version number (0 to go back):`

Accept these variations:
- "select version 1" / "1" / "first" / "first one"
- "select the active version" / "active" (find which number is Active)
- "3" / "version 3" / "v3"
- "0" / "back" / "go back"

**Important**: The script expects a **number** (1, 2, 3, etc.), not the version label (v1, v2).

**Conversation Examples:**

```
User: select the active version
Claude: [Reads script output to find Active version is #3]
        3
        [Script shows confirmation prompt]

User: 1
Claude: [Feeds "1" to script stdin]
        [Script shows confirmation prompt for v1]

User: back
Claude: 0
        [Returns to Phase 1.2]

User: what does active mean?
Claude: The "Active" version is the currently deployed version in your org.
        For production migrations, you should use the Active version to ensure
        you're migrating the live bot configuration.
        
        In the list above, look for the row with "Active" status.
        Which version number would you like to select?
```

**Off-topic handling:**

```
User: how do I create a new bot?
Claude: We are currently in the version selection phase (Step 1). I can help you:
        - Select a version number (1, 2, 3, etc.)
        - Go back to the bot list (enter 0)
        
        To create a new bot, you would do that in Salesforce Setup after
        completing the migration. Which version would you like to select?
```

---

### Phase 1.4: Confirm Selection

**The script prompts: `Fetch <BotName> v<X>? [y/n]:`**

This confirmation happens **after** the user selects a version number.

**Script handles overwrite checks internally** — Claude does not need to check for existing files.

If the file already exists, the script will prompt the user directly:
```
⚠️  bot.json already exists for <BotName> version <X>

Do you want to overwrite the existing data?

  [yes]  Overwrite and re-retrieve metadata
  [no]   Skip retrieval (use existing data)

Your choice:
```

**Natural Language Understanding:**

The script expects `y` or `n`:

Accept:
- "yes" / "y" → Feed `y` to script
- "no" / "n" → Feed `n` to script

**Conversation Examples:**

```
User: yes
Claude: y
        [Script proceeds to download or shows overwrite prompt]

User: no
Claude: n
        [Script goes back to version selection]
```

**If script shows overwrite prompt:**

```
⚠️  bot.json already exists for B2A_Intent_Enabled version 1

Do you want to overwrite the existing data?

  [yes]  Overwrite and re-retrieve metadata
  [no]   Skip retrieval (use existing data)

Your choice:
```

Accept:
- "yes" / "y" / "overwrite" → Feed `yes` to script
- "no" / "n" / "skip" / "use existing" → Feed `no` to script

---

### Phase 1.5: Download & Save

**🚨 CRITICAL: Single Script Execution - Never Restart the Script 🚨**

The `interactive` mode script runs **continuously as ONE PROCESS** from Phase 1.2 through completion.

**❌ WRONG - Never Do This:**
```bash
# Starting script multiple times breaks the flow
bash fetch_bot_from_org.sh interactive orgfarm-cult          # Shows bot list
echo "1" | bash fetch_bot_from_org.sh interactive orgfarm-cult  # ❌ WRONG - restarts script
echo "1" | bash fetch_bot_from_org.sh interactive orgfarm-cult  # ❌ WRONG - restarts again
bash fetch_bot_from_org.sh B2A_Intent_Enabled orgfarm-cult    # ❌ WRONG - bypasses user selection
```

**✅ CORRECT - Do This:**
```bash
# Single continuous script execution with piped input (4 inputs if file exists)
printf "1\n1\ny\nyes\n" | bash fetch_bot_from_org.sh interactive orgfarm-cult
# Input 1: Bot selection (1)
# Input 2: Version selection (1)
# Input 3: Confirmation (y)
# Input 4: Overwrite choice (yes) - only if file already exists
```

**If file doesn't exist:**
```bash
printf "1\n1\ny\n" | bash fetch_bot_from_org.sh interactive orgfarm-cult
# Only 3 inputs needed
```

**Script execution flow (ONE continuous process):**
1. Script shows bot list (Phase 1.2)
2. Script **waits for stdin** ← Reads first line (bot selection)
3. Script shows version list (Phase 1.3)  
4. Script **waits for stdin** ← Reads second line (version selection)
5. Script **exits Python selector** with SELECTED_BOT and SELECTED_VERSION
6. Script shows confirmation prompt (Phase 1.4)
7. Script **waits for stdin** ← Reads third line (y/n confirmation)
8. Script checks if `${BOT_NAME}.json` exists (e.g., `B2A_Intent_Enabled.json`)
9. **If file exists**: Script shows overwrite prompt
10. Script **waits for stdin** ← Reads fourth line (yes/no for overwrite)
11. If yes, script deletes old directory and downloads fresh
12. If no, script exits with "Using existing" message
13. Script outputs success/failure
14. Script exits

**IMPORTANT**: Always provide 4 inputs via printf if you don't know whether file exists:
```bash
printf "1\n2\ny\nyes\n" | bash fetch_bot_from_org.sh interactive orgfarm-cult
```
The 4th input (yes) will only be consumed if file exists. Otherwise it's ignored.

**🚨 CRITICAL RULES FOR CLAUDE:**

1. **NEVER auto-select org, bot, or version** - Always ask user to choose
2. **NEVER restart the script multiple times** - Run it ONCE with all inputs
3. **NEVER "preview" or "fetch" lists separately** - The single script run will show everything
4. **ALWAYS use printf, NEVER use { echo } syntax** - Use: `printf "1\n2\ny\nyes\n"`
5. **ASK user for numbers BEFORE running script** - Don't run script to show lists first
6. **The script WILL show lists during execution** - User sees them in the final output
7. **NEVER say "fetching versions" or "fetching bots"** - Just run the single command

**User experience should be:**
- User sees org list → selects org (e.g., "1")
- Claude asks: "Which bot number?" → User says: "1"  
- Claude asks: "Which version number?" → User says: "2"
- Claude runs: `printf "1\n2\ny\nyes\n" | bash ... interactive orgfarm-cult`
- User sees the script output showing bot list, version list, and download progress
- Done! No intermediate prompts or selections

**Claude's role - Complete Flow:**

**🚨 CRITICAL: ONE SCRIPT EXECUTION ONLY 🚨**

1. **Show org list**: Run `sf org list --json` and display formatted table
2. **User selects org number**: Capture user's choice (e.g., "1" for orgfarm-cult)
3. **Get user's bot selection**: Ask "Which bot number?" (user will say "1" or "2" etc.)
4. **Get user's version selection**: Ask "Which version number?" (user will say "1" or "2" etc.)
5. **Run script ONCE with all inputs**:
   ```bash
   printf "1\n2\ny\nyes\n" | bash .claude/skills/01-retrieve-bots-metadata/scripts/fetch_bot_from_org.sh interactive orgfarm-cult
   ```
   Replace 1, 2 with actual user selections and orgfarm-cult with actual org alias
   
   **The 4 inputs:**
   - Line 1: Bot number (e.g., 1)
   - Line 2: Version number (e.g., 2)
   - Line 3: Confirmation (always "y")
   - Line 4: Overwrite (always "yes") - consumed only if file exists

6. **NEVER use**: `{ echo "1"; echo "2"; }` - Use `printf` with `\n` instead
7. **NEVER restart the script** - The user already told you the bot and version numbers
8. Parse final output for success/failure

**Why this works:**
- Script shows bot list → reads bot# from stdin
- Script shows version list → reads version# from stdin  
- Script shows confirmation → reads "y" from stdin
- Script checks file exists → reads "yes" from stdin (if needed)
- Script downloads and completes

**The script output will show the lists to the user naturally as it runs**

**Why this matters:**
- ❌ Restarting the script queries org again and picks latest version (ignores user selection)
- ❌ Non-interactive mode bypasses user's version choice
- ✅ Continuous process preserves SELECTED_VERSION from Python script
- ✅ Single execution respects all user choices

If user chooses "no":
```
✅ Skipping retrieval. Using existing CustomerServiceBot.json

File location:
  data/bots/00dvw0000075wif2ai/customerservicebot/v4/CustomerServiceBot.json

Next Step:
  /02-process-and-build-inventory
```

**Show simplified progress (hide intermediate steps unless errors occur):**
```
Downloading metadata for CustomerServiceBot v4...

✅  Metadata saved successfully!
```

**Internal steps (Steps 1.1-1.7) run silently unless DEBUG=1:**
- 1.1: Checking Salesforce DX project setup
- 1.2: Getting org details and bot version  
- 1.3: Retrieving bot metadata from org
- 1.4: Auto-discovering ML domains
- 1.5: Retrieving ML training data (if available)
- 1.5.1: Copying files to step1 folder
- 1.6: Converting bot XML to JSON
- 1.6.1: Converting ML domain XML to JSON (if retrieved)
- 1.6.2: Extracting bot metadata to JSON
- 1.7: Fetching real Apex class signatures from org (two-phase: extract params → parse signatures → merge)

**Only show SF CLI output and errors. Hide internal logging unless DEBUG=1.**

**Example error output:**
```
Downloading metadata for CustomerServiceBot v4...
❌ Error: Failed to extract bot metadata
```

**Success outcome:**
```
════════════════════════════════════════════════════════════
✅  STEP 1 COMPLETE
════════════════════════════════════════════════════════════

Bot metadata successfully retrieved and saved.

Final JSON location:
  data/bots/00dvw0000075wif2ai/customerservicebot/v4/CustomerServiceBot.json

════════════════════════════════════════════════════════════
```

**After successful completion, ask user what they want to do next:**
```
We just completed fetching metadata for <BotName> <VersionNumber>.

Would you like to:

  [1] Continue to Step 2 with <BotName> (recommended)
  [2] Fetch a different bot from the same org (<OrgAlias>)
  [3] Fetch a bot from a different org
  [4] Re-fetch the same bot (<BotName> <VersionNumber>)

Which option would you prefer?
```

**Handle user responses:**
- **Option 1**: Proceed to `/02-process-and-build-inventory`
- **Option 2**: Return to Phase 1.2 (bot list) with same org - **Start fresh interactive flow, no auto-selection**
- **Option 3**: Return to Phase 1.1 (org selection) - **Start fresh, show org list, no auto-selection**
- **Option 4**: Check if bot JSON file exists, then:
  - If file exists: Show confirmation with overwrite warning
  - If file doesn't exist: Proceed directly to fetch (no warning needed)

**🚨 CRITICAL for Options 2 & 3:**
- **NEVER remember** the previous org, bot, or version
- **ALWAYS show** the full list again
- **ALWAYS ask** the user to select from the list
- Use the same continuous script execution pattern: `printf "...\n...\n...\n" | bash fetch_bot_from_org.sh interactive <ORG>`

**Option 4 detailed flow:**

First, check if the bot JSON file exists at the expected path:
```
data/bots/<org-id-lowercase>/<bot-name-lowercase>/v<version>/<BotName>.json
```

**If file exists:**
```
⚠️  You've chosen to re-fetch <BotName> <VersionNumber>.

This will overwrite the existing metadata that was just downloaded.

Are you sure you want to proceed?

  [yes] Re-fetch and overwrite existing data
  [no]  Cancel and keep existing data

Your choice:
```

**If file does NOT exist:**
```
✅ Confirmed. Fetching metadata for <BotName> <VersionNumber>...
```

Then proceed directly to run the fetch script (no confirmation needed since there's nothing to overwrite).

**Important**: Replace `<BotName>`, `<VersionNumber>`, and `<OrgAlias>` with actual values from the completed fetch.

**Failure outcome:**
```
❌  Metadata download failed.

    Bot     : CustomerServiceBot  v4
    Reason  : <error detail from script>

  [retry]  Try downloading again
  [back]   Go back to the version list
  [quit]   Exit
```

**Natural Language Understanding:**

Accept:
- "yes" / "proceed" / "continue" / "next"
- "retry" / "try again"
- "back" / "go back"
- "quit" / "exit"

---

## Conversation Patterns

### Free-Form Questions During Selection

The user can ask questions at any point. Handle contextually:

**During bot selection (Phase 1.2):**
```
User: what does this bot do?
Claude: I can see that CustomerServiceBot is described as: "Customer service bot 
        for airline services. Handles reservations, baggage, rewards."
        
        Would you like to select this bot?

User: show me more details about bot 2
Claude: Bot 2 is FitnessAssistantBot:
        - Description: Fitness assistant
        - Available versions: v1, v2, v3
        - Latest modified: [date]
        
        Would you like to select this bot?
```

**Off-topic redirects:**
```
User: how does AgentScript work?
Claude: That's a great question! I'll explain how AgentScript works when we 
        get to Step 4 (Generate Script). Right now, we're in Step 1 where we 
        need to select and download a bot's metadata.
        
        Which bot would you like to convert?

User: can I change the org?
Claude: We are currently connected to: <OrgName>
        
        To switch orgs, you'll need to:
        1. Say "quit" to exit
        2. Authenticate to a different org: sf org login web --alias <new-alias>
        3. Re-run: /01-retrieve-bots-metadata
        
        Would you like to continue with the current org, or quit and switch?
```

### Conversation Memory

Maintain context throughout the flow:
- Remember which bot was selected when asking about versions
- Remember version when asking for confirmation
- Refer back to previous choices naturally

**Example:**
```
[User selected CustomerServiceBot in Phase 1.2]

Claude (in Phase 1.3): Here are the versions for CustomerServiceBot...

[User selected v4 in Phase 1.3]

Claude (in Phase 1.4): Confirm: CustomerServiceBot v4 from <OrgName>
```

---

## Technical Implementation

### Script Invocations

**Phase 1.1 - Check org:**
```bash
sf org list --json
```

**Phase 1.2 - Interactive bot selection:**
```bash
bash .claude/skills/01-retrieve-bots-metadata/scripts/fetch_bot_from_org.sh interactive <ORG_ALIAS>
```

This script internally calls `list_bots_interactive.py` which:
1. Queries all bots and versions
2. Displays formatted table
3. Captures user selection
4. Returns `SELECTED_BOT=<name>` for shell to parse

**Phase 1.5 - Download metadata:**
```bash
bash .claude/skills/01-retrieve-bots-metadata/scripts/fetch_bot_from_org.sh <BOT_NAME> <ORG_ALIAS>
```

This executes the full retrieval pipeline (Steps 1.3-1.10 in the script).

### Output Files

After successful completion:

| File | Location | Purpose |
|------|----------|---------|
| **Final bot JSON** | `data/bots/<org-id>/<bot-name>/v<version>/<BotName>.json` | **Main output for Step 2** |
| Step 1 intermediates | `data/bots/<org-id>/<bot-name>/v<version>/step1/` | All intermediate files (XML, JSON, Apex) |
| Bot XML | `step1/xml/bots/` | Raw bot metadata |
| ML Domain XML | `step1/xml/mlDomains/` | Raw ML metadata |
| JSON conversions | `step1/json/` | Converted metadata |
| Apex parsing | `step1/apex-invocations/` | Apex classes and parsing artifacts |

### Error Handling

**Org authentication failure:**
- Show exact error from `sf org list`
- Provide fix command
- Do not proceed

**Bot query failure:**
- Show error from query
- Suggest fixes (check permissions, network)
- Allow retry or quit

**Download failure:**
- Show which step failed (1.3-1.10)
- Show error detail from script
- Offer retry, go back, or quit

---

## Hand-off to Step 2

Once Step 1 completes successfully, hand off to Step 2:

**File to pass:**
```
data/bots/<org-id-lowercase>/<bot-name-lowercase>/v<version>/<BotName>.json
```

Example:
```
data/bots/00dvw0000075wif2ai/b2a_intent_enabled/v1/B2A_Intent_Enabled.json
```

**Transition message:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 1 complete.
  CustomerServiceBot v4  —  metadata downloaded

  Moving to Step 2: Bot Inventory.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then invoke:
```
/02-process-and-build-inventory
```

Or wait for user to say "yes" / "proceed".

---

## Design Principles

### Visual Consistency

Use these formatting patterns consistently:

**Headers:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Title
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Status indicators:**
- ✅ Success
- ❌ Error
- ⚠️  Warning
- ℹ️  Info
- ↩ Going back
- ✓ Checkmark for completed items

**Options:**
```
[option]  Description
```

**Table borders:**
```
─   Separator
```

### Conversational Tone

- Be concise and direct
- Use active voice: "I will download..." not "The system will..."
- Acknowledge user input: "✅ Selected: CustomerServiceBot"
- Provide context: "The Active version is recommended for production migrations"
- Guide next steps: "Would you like to select a version?"

### Natural Language Processing

- Accept multiple phrasings for same intent
- Handle typos gracefully
- Understand context from previous messages
- Redirect off-topic questions contextually
- Never say "I don't understand" - always suggest valid options

---

## Testing Scenarios

### Happy Path
1. User invokes skill
2. Org connects successfully
3. User selects bot by number
4. User selects active version
5. User confirms
6. Download succeeds
7. User proceeds to Step 2

### Edge Cases

**No bots in org:**
- Show clear message
- Don't proceed

**Authentication expired mid-flow:**
- Catch error
- Show re-auth command
- Allow retry

**User changes mind:**
- Allow "back" at every stage
- Maintain context when going back

**Download interrupted:**
- Show which step failed
- Offer retry with same selections

**Off-topic questions:**
- Answer briefly
- Redirect to current phase
- Maintain flow context

---

## Quick Reference

### Commands Available

| Phase | User Can Say | Action |
|-------|-------------|--------|
| 1.2 | "select 1" / "bot 1" | Select bot |
| 1.2 | "quit" / "exit" | Exit skill |
| 1.3 | "select v4" / "active" | Select version |
| 1.3 | "back" | Return to bot list |
| 1.4 | "yes" / "confirm" | Start download |
| 1.4 | "back" | Return to versions |
| 1.5 | "retry" | Retry download |
| 1.5 | "yes" / "proceed" | Go to Step 2 |

### File Paths

```
.claude/skills/01-retrieve-bots-metadata/
├── SKILL.md                                  # This file
├── APEX_INVOCATION_PARSING.md                # Technical doc for two-phase Apex parsing
├── assets/
│   ├── SF_CLI_COMMANDS.md                    # SF CLI reference
│   └── BOT_FETCHING_GUIDE.md                 # Comprehensive fetching guide
└── scripts/
    ├── fetch_bot_from_org.sh                 # Main orchestrator (Steps 1.1-1.7)
    ├── list_bots_interactive.py              # Bot selector
    ├── convert_bot_xml_to_json.py            # Bot XML converter
    ├── extract_bot_metadata.py               # Extraction engine (handles ML intents, normalizes retryMessages)
    ├── convert_ml_domain.py                  # ML domain XML converter
    ├── fetch_and_parse_invocations.sh        # Apex parsing orchestrator (two-phase approach)
    ├── extract_invocations_from_bot.py       # Phase 1: Extract parameter names from bot metadata
    ├── parse_apex_invocable_methods.py       # Phase 2a: Parse Apex @InvocableMethod signatures
    ├── merge_invocation_types.py             # Phase 2b: Merge bot params with Apex types
    └── compare_bot_jsons.py                  # Validation tool

Output:
data/bots/<org-id-lowercase>/<bot-name-lowercase>/v<version>/
├── <BotName>.json                           # ⭐ FINAL OUTPUT - Pass this to Step 2
└── step1/                                   # All Step 1 intermediate files
    ├── xml/
    │   ├── bots/                            # Raw bot XML
    │   └── mlDomains/                       # Raw ML XML
    ├── json/                                # Converted JSON files
    │   ├── <BotName>.bot-meta.json
    │   ├── v<N>.botVersion-meta.json
    │   └── <MLDomain>.json
    └── apex-invocations/                    # Apex parsing artifacts
        ├── classes/                         # Retrieved Apex .cls files
        ├── bot-invocations.json             # Phase 1: parameter names
        ├── parsed-apex-types.json           # Phase 2a: types from Apex
        └── merged-invocations.json          # Phase 2b: complete data
```

---

## Technical Implementation Details

### Two-Phase Apex Parsing (Step 1.7)

**Problem Solved:**
The original implementation inferred Apex invocable method parameter types from bot conversation variable labels, leading to incorrect type information. For example, a variable labeled "Response User" was incorrectly inferred as `ResponseUser__c` when the actual type was `CultUser__c`.

**Solution:**
Replaced inference with real Apex class parsing from Salesforce org using a two-phase approach:

**Phase 1: Extract Parameter Names from Bot Metadata**
- Script: `extract_invocations_from_bot.py`
- Parses `invocationMappings` from botVersion metadata
- Returns parameter names (without types yet)
- Output: `bot-invocations.json`

**Phase 2: Fetch and Parse Apex Classes**
- **Phase 2a: Parse Apex Source** (`parse_apex_invocable_methods.py`)
  - Retrieves .cls files from org using SF CLI
  - Parses `@InvocableMethod` signatures
  - Handles Request/Response inner classes
  - Handles simple method signatures (List<String> input, List<Response> output)
  - Handles mixed patterns (simple input + Response class output)
  - Maps Apex types to API types (`String` → `STRING`, `CustomObject__c` → `SOBJECT`)
  - Uses `sobjectType` field name (lowercase 's')
  - Output: `parsed-apex-types.json`
  
- **Phase 2b: Merge** (`merge_invocation_types.py`)
  - Merges bot metadata parameters with Apex type information
  - Uses Apex as authoritative source (includes all defined parameters)
  - Sorts all data alphabetically
  - Output: `merged-invocations.json`

**Phase 3: Update Bot JSON**
- Replaces `botInvocationsDescribeInfo.apex` with complete, accurate data
- Output: `<BOTNAME>_with_parsed_invocations.json` → `<BOTNAME>.json`

**Batching Strategy:**
- ≤ 50 Apex classes: Single `sf project retrieve start` call with `package.xml`
- \> 50 Apex classes: Batches of 50 (efficient parallel retrieval)

**Key Features:**
- ✅ No inference - all data from real Apex source code
- ✅ Accurate SObject types (e.g., `CultUser__c` not fabricated `ResponseUser__c`)
- ✅ Proper field name: `sobjectType` (lowercase 's')
- ✅ Includes `required` flags from `@InvocableVariable(required=true)`
- ✅ Handles complex method patterns (Request/Response, simple, mixed)
- ✅ Alphabetically sorted (classes, input params, output params)
- ✅ Generic - works with any Einstein Bot

**See Also:**
- `.claude/skills/01-retrieve-bots-metadata/APEX_INVOCATION_PARSING.md` for complete technical documentation
- `.claude/skills/01-retrieve-bots-metadata/assets/BOT_FETCHING_GUIDE.md` for usage guide

### retryMessages Normalization (Step 2.5 in extract_bot_metadata.py)

**Problem Solved:**
Einstein Bot metadata has inconsistent `retryMessages` structure:
- Sometimes: `{"message": "...", "messageIdentifier": "..."}` (single object)
- Sometimes: `[{"message": "...", "messageIdentifier": "..."}, ...]` (array)

**Solution:**
Added `normalize_retry_messages()` function that ensures all `retryMessages` fields are arrays of objects for consistency.

---

## Next Steps

1. After successful completion:
- **File ready:** `data/bots/<org-id>/<bot-name>/v<version>/<BotName>.json`
- **Contains:** Complete bot structure + ML training data + accurate Apex invocation types
- **Pipeline state saved:** `.claude/pipeline-state.json` (for session resumption)
- **Next skill:** `/02-process-and-build-inventory`
- **User prompt:** "Would you like to proceed to Step 2: Bot Inventory?"
2. **Important Instruction** - For the scope of this session, update the data directory to the new folder `data/bots/<org-id>/<bot-name>/v<version>`.
   - All new intermediate files or outputs should be written/read from this folder.
   - Wherever data directory is referenced, it should be resolved to this path.
   - Example: `data/bots/<ORGID>/<BOT_NAME>/<BOT_VERSION_NAME>` ---> `data/bots/00DSB00000cASgsgAG/Service_Bot/v1`.
3. Ensure that `<BOT_NAME>.json` file is present in the new data directory.
4. Finally, provide a message to the user like 'Proceeding to the next step..'.
