---
name: verify-bot-to-agent-migration-prerequisites
description: >
   Entry point for migrating an Einstein Bot to a Salesforce NGA (Next Generation AI) Agent
   using AgentScript format. Verifies prerequisites, explains the 6-step migration pipeline,
   and launches the first step. Start here when the user wants to migrate an Einstein Bot
   to NGA Agent.
metadata:
   author: salesforce-migration
   version: "2.0-bot"
   pipeline-order: "0"
compatibility: Requires Node.js, Python 3.11+, Salesforce CLI (sf), uv package manager, sf-git-merge-driver plugin, and network access to the Salesforce Nexus PyPI proxy.
---

# Start Bot-to-NGA Agent Migration

# Purpose

This verifies that all required tools are installed and prerequisites are met, provides authoritative reference materials, and hands off to the first migration step.

# Instructions

## 1. Verify Prerequisites

**IMPORTANT: You MUST wait for up to 5 minutes for ALL `sf` CLI commands to complete.** Do
not cancel, retry, or re-run the same `sf` command without first giving it adequate time to
finish. Salesforce CLI operations (especially org-related commands) can be slow depending on
network conditions and org size.

Run ALL of the following checks. Report the result of each.

### 1a: Python 3.11+

```bash
python3 --version
```

Check that the version is 3.11 or higher. If Python is not installed or the version is older than 3.11, check for `python3.11` as a fallback:

```bash
python3.11 --version 2>/dev/null || echo "not found"
```

If `python3.11` exists and is 3.11+, suggest creating an alias or updating the PATH. Otherwise:
> "Python 3.11+ is required for the AgentScript compiler but not installed or version is too old.
> Current version: [version or 'not found']"

### 1b: Node.js

```bash
node --version
```

If this fails:
> "Node.js is required (for the Salesforce CLI) but not installed.
> Install it from: https://nodejs.org/"


### 1c: Salesforce CLI

```bash
sf --version
```

If this fails:
> "The Salesforce CLI (`sf`) is required but not installed.
> Install it from: https://developer.salesforce.com/tools/salesforcecli"


### 1d: uv Package Manager

```bash
uv --version
```

If this fails:
> "The `uv` package manager is required but not installed.
> Install from: https://docs.astral.sh/uv/getting-started/installation/"


### 1e: Nexus Authentication Files

Check for the existence of required Nexus authentication configuration files:

```bash
test -f ~/.npmrc && echo "✓ ~/.npmrc exists" || echo "✗ ~/.npmrc missing"
```

```bash
test -f ~/.m2/settings.xml && echo "✓ ~/.m2/settings.xml exists" || echo "✗ ~/.m2/settings.xml missing"
```

```bash
(test -f ~/.config/nexus-npm/npm-sfdc-certs.pem || test -f ~/npm-sfdc-certs.pem) && echo "✓ npm-sfdc-certs.pem exists" || echo "✗ npm-sfdc-certs.pem missing"
```

If **any** of these files are missing:

1. Ask the user to open https://nexus-dev.data.sfdc.net/nexus/ and login with SSO
2. Instruct them to retrieve their user access token details (NEXUS_TOKEN_ID and NEXUS_TOKEN_HASH)
3. Ask for NEXUS_TOKEN_ID (wait for user response)
4. Ask for NEXUS_TOKEN_HASH (wait for user response)
5. Run the Nexus installer command (piped directly from source):

```bash
NEXUS_TOKEN_ID=<id> NEXUS_TOKEN_HASH=<hash> node npm-setup.js bash
```

Replace `<id>` and `<hash>` with the values provided by the user.

**Important:** Do not proceed until all three authentication files are present.

**Note:** The installer script URL requires SSO authentication and cannot be downloaded directly to disk. The curl-pipe-to-bash approach handles the authentication automatically.

### 1f: Salesforce Metadata Git Merge Driver

Check if the plugin is installed:

```bash
sf plugins 2>/dev/null | grep sf-git-merge-driver || echo "not installed"
```

Check if it is configured for this project:

```bash
git config --get merge.salesforce-source.driver 2>/dev/null && echo "configured" || echo "not configured"
```

If the plugin is **not installed**, install it:

```bash
sf plugins install sf-git-merge-driver
```

If the plugin is installed but the project is **not configured**, wire it up:

```bash
sf git merge driver install
```

If both pass, report `PASS`. This driver resolves Salesforce metadata XML merge conflicts (profiles, permission sets, picklists, workflows, etc.) automatically during `git merge`, `git pull`, and `git rebase`.

### 1g: Compiler Dependencies (Network Access)

```bash
python3 .claude/skills/00-verify-prerequisites/scripts/compile_agentscript_nexus_ts.py 2>&1 || true
```

If the output shows a network error reaching the Nexus PyPI proxy:
> "Cannot reach the Salesforce Nexus PyPI proxy at nexus-proxy.repo.local.sfdc.net.
> Ensure you are on a network with access (VPN may be required)."

If the output shows `Usage:` or a missing-argument error, the compiler is accessible — this
is a successful check.

## 2. Report Readiness

After all checks, display a summary:

```
Prerequisites Check
====================
  Python 3.11+:         [PASS version / FAIL]
  Node.js:              [PASS version / FAIL]
  Salesforce CLI:       [PASS version / FAIL]
  uv:                   [PASS version / FAIL]
  Nexus Auth Files:     [PASS / FAIL (list missing files)]
  SF Merge Driver:      [PASS / INSTALLED / CONFIGURED / FAIL]
  Compiler Access:      [PASS / FAIL]
```

**Note:** Org authentication will be verified in Step 1 (Retrieve Bot Metadata) when you need to connect to Salesforce.

If **all checks pass**:
> "Your environment is ready. Starting Step 1: Retrieve Bot Metadata."

Then invoke the **01-retrieve-bots-metadata** skill.

If **check 1e fails** (Nexus authentication files missing):
> "Nexus authentication is not configured. Please follow these steps:
>
> 1. Open https://nexus-dev.data.sfdc.net/nexus/ in your browser
> 2. Login with your SSO credentials
> 3. Retrieve your NEXUS_TOKEN_ID and NEXUS_TOKEN_HASH
> 4. Provide them when prompted below
>
> I will run the Nexus installer to configure your authentication."

Wait for user to provide NEXUS_TOKEN_ID and NEXUS_TOKEN_HASH, then run the installer command (curl piped to bash with the credentials).

If **check 1f fails** (SF merge driver not installed or not configured for the project), auto-install and configure it silently — no user action needed. Report the result in the summary.

If **any of checks 1a, 1b, 1c, or 1d fail** (Python 3.11+, Node.js, sf CLI, or uv missing), suggest the user
run the appropriate one-line installer command:

> "Some prerequisites are missing: [list missing tools].
> You can install them automatically using the provided installation scripts:
>
> **macOS/Linux:**
> ```bash
> bash scripts/install-prerequisites.sh
> ```
>
> **Windows (PowerShell):**
> ```powershell
> powershell -ExecutionPolicy Bypass -File scripts/install-prerequisites.ps1
> ```
>
> After installing, please restart your terminal and re-run this skill."

**Do NOT proceed to the next step until all prerequisites pass.**

## 3. Output

- Environment readiness report
- Pipeline overview for the user
