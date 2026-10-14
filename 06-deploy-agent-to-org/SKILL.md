---
name: deploy-agentscript
description: >
  Deploys the compiled AgentScript (aiAuthoringBundle) to a Salesforce org with mandatory
  human-in-the-loop confirmation and a self-healing publish loop. Shows org details before
  deployment and retries on publish errors. Pipeline step 6 of 6.
metadata:
  author: salesforce-migration
  version: "1.0"
  pipeline-order: "6"
compatibility: Requires Salesforce CLI (sf) installed, authenticated org connection, a successfully compiled .agent file from the 05-compile-agentscript skill, and 00-start-migration/assets/AGENT_SCRIPT_RULES.md for error fixing reference.
---

# Deploy AgentScript

## Purpose

Deploy the compiled AgentScript (`aiAuthoringBundle`) to the target Salesforce org. This skill
enforces mandatory human-in-the-loop confirmation before any deployment and includes a
self-healing loop to fix publish errors.

## Prerequisites

- The `.agent` file compiled successfully (from `05-compile-agentscript`).
- Salesforce CLI (`sf`) is installed and authenticated.
- `migration-architecture.md` is readable for agent name and org details.

## Safety Rules

1. **NEVER deploy without explicit user confirmation.** This skill modifies a live Salesforce
   org. The user MUST see the org details and explicitly approve before ANY deployment command.

2. **NEVER skip the confirmation step.** Even if the user said "deploy" earlier, re-confirm
   with full org details displayed.

3. **NEVER force-deploy over existing bundles.** If a bundle with the same name already
   exists, warn the user and ask how to proceed.

4. **You MUST wait for up to 5 minutes for ALL `sf` CLI commands to complete.** Do not cancel,
   retry, or re-run the same `sf` command without first giving it adequate time to finish.
   Salesforce CLI operations (deploy, publish, org display) can be slow. Be patient and let
   each command run to completion before analyzing the result or retrying.

## Instructions

### Step 0: Setup AgentforceDX Project

Before proceeding with deployment, ensure the `agentforcedx` project exists:

**Check if agentforcedx project exists:**
```bash
ls -la bot-to-agent-migration-dev/agentforcedx
```

**If it doesn't exist, create it:**
```bash
cd bot-to-agent-migration-dev
sf template generate project --name agentforcedx --template agent
cd agentforcedx
```

**Verify the project structure:**
The project should have this directory structure:
```
agentforcedx/
├── force-app/
│   └── main/
│       └── default/
│           └── aiAuthoringBundles/
```

**If agentforcedx project exists, proceed to Step 1.**

### Step 1: Load Deployment Context

Read `migration-architecture.md` and extract:
- `AGENT_NAME` — the agent API name
- `TARGET_ORG` — the org alias or username used during retrieval

Always ask for TARGET_ORG from user.

Verify the compiled `.agent` file exists at:
`force-app/main/default/aiAuthoringBundles/AGENT_NAME/AGENT_NAME.agent`

#### 1a: Copy Agent Bundle to AgentforceDX Project

Copy the compiled agent bundle to the agentforcedx project for deployment:

```bash
cp -r force-app/main/default/aiAuthoringBundles/AGENT_NAME bot-to-agent-migration-dev/agentforcedx/force-app/main/default/aiAuthoringBundles/
```

Verify the copy was successful:
```bash
ls -la bot-to-agent-migration-dev/agentforcedx/force-app/main/default/aiAuthoringBundles/AGENT_NAME/
```

The agent bundle should now exist in both locations:
- Source: `force-app/main/default/aiAuthoringBundles/AGENT_NAME/`
- Deployment: `bot-to-agent-migration-dev/agentforcedx/force-app/main/default/aiAuthoringBundles/AGENT_NAME/`

#### 1c: Verify No Linter Errors

Before proceeding with deployment, you MUST verify that all linter errors in the `.agent`
file and related project files have been resolved. Open the files in the IDE and check for
any remaining warnings or errors. **Do NOT proceed with deployment until ALL linter errors
are fixed.** Deploying code with linter errors can cause deployment failures or unexpected
behavior in the org.

### Step 2: Display Org Details

Run:

```bash
sf org display --target-org TARGET_ORG --json
```

Parse the JSON output and present the following to the user clearly:

```
============================================
   DEPLOYMENT TARGET ORG DETAILS
============================================

   Org ID:        [orgId]
   Username:      [username]
   Instance URL:  [instanceUrl]
   Org Type:      [orgType — Production/Sandbox/Scratch/etc]
   API Version:   [apiVersion]
   Status:        [status]
   Alias:         [alias]

   Agent to Deploy: AGENT_NAME
   Source Path:     force-app/main/default/aiAuthoringBundles/AGENT_NAME/
============================================
```

### Step 3: Request Explicit User Confirmation

Display this message:

```
DEPLOYMENT CONFIRMATION REQUIRED
=================================

I am about to deploy the new AgentScript agent to the org shown above.

This will:
  1. Publish the agent bundle (which both deploys source files and publishes in one step)

Do you confirm this deployment? Please respond YES or NO.
```

**WAIT for the user to explicitly respond.**

- If the user responds **YES** (or equivalent affirmative) → proceed to Step 4.
- If the user responds **NO** (or equivalent negative) → STOP immediately. Ask what
  they would like to do instead. Do not proceed.
- If the user's response is ambiguous → ask again for a clear YES or NO.

### Step 4: Deploy Source Files

#### 4a: Verify `.bundle-meta.xml` Exists

Before deploying, verify that the bundle metadata file exists at:
`bot-to-agent-migration-dev/agentforcedx/force-app/main/default/aiAuthoringBundles/AGENT_NAME/AGENT_NAME.bundle-meta.xml`

If it does NOT exist, create it with this exact content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AiAuthoringBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <bundleType>AGENT</bundleType>
</AiAuthoringBundle>
```

**Do NOT proceed with deployment until this file exists.** The deploy/publish will fail without it.

### Step 5: Publish the Agent

`sf agent publish authoring-bundle` both deploys source files and publishes in one step.
There is NO need to run `sf project deploy start` separately.

Initialize publish loop: Set `PUBLISH_ITERATION = 0` and `MAX_PUBLISH_ITERATIONS = 5`.

Run the publish command from the agentforcedx project directory:

```bash
#cd bot-to-agent-migration-dev/agentforcedx && sf agent publish authoring-bundle --dev-debug --api-name AGENT_NAME --target-org TARGET_ORG
cd bot-to-agent-migration-dev/agentforcedx && sf project deploy start -m --dev-debug AiAuthoringBundle:AGENT_NAME -o TARGET_ORG
```
Very Important: Always provide detailed error output in the console in case of error. The dev-debug flag attached to publish command will get detailed error output.

### Step 6: Handle Publish Result

#### Outcome A: Publish Succeeds

The command completes without errors → go to Step 8.

#### Outcome B: Publish Fails

Capture the COMPLETE error output. Increment `PUBLISH_ITERATION`.

If `PUBLISH_ITERATION >= MAX_PUBLISH_ITERATIONS`:
- STOP the loop.
- Report all remaining errors to the user.
- Go to Step 9.

Otherwise, diagnose and fix.

**ABSOLUTE PROHIBITION — NO WEB OR INTERNET SEARCH.** Under absolutely NO circumstances may
you use web search, internet search, or any external lookup to diagnose or fix publish errors.
This is non-negotiable. You MUST rely ONLY on these local project files:

1. **`00-start-migration/assets/AGENT_SCRIPT_RULES.md`** — The **primary authority** for all
   AgentScript syntax and rules. Consult this FIRST when diagnosing publish errors.
2. **`00-start-migration/assets/AGENT_SCRIPT_RECIPES.xml`** — Working examples of correct
   AgentScript patterns.
3. When fixing errors, consult the rules file for the correct syntax, then check
   `recipes/AGENT_SCRIPT_RECIPES.xml` from resources directory for working examples, then check `agentScripts/` from resources directory for working agent examples.
   **Precedence order** (highest to lowest): `AGENT_SCRIPT_RULES.md` > `AGENT_SCRIPT_RECIPES.xml` > `agentScripts\`. The migration
   skill files contain overrides and refinements that take precedence over the general-purpose
   rules file.

4. **Legacy `genAiPlannerBundles` JSON schema files** — For verifying action schemas.

If the error cannot be resolved from these sources alone, STOP and report it to the user.

**Common publish errors and fixes:**

| Error | Diagnosis | Fix |
|-------|----------|-----|
| Invalid `complex_data_type_name` | Wrong type value (often `lightning__objectType` used as default) | Read the legacy JSON schema (`localActions/.../schema.json`), find the parameter's `lightning:type`, set `complex_data_type_name` to that EXACT value. See `LEGACY_TYPE_MAPPINGS.md` |
| Invalid data type for parameter | Base type is `string` but should be `object` with `complex_data_type_name` | Change base type to `object`, add `complex_data_type_name` from legacy `lightning:type` |
| Missing output/input parameters | A parameter defined in the source action is missing | Read the legacy schema and add the missing parameter with correct type and `complex_data_type_name` |
| Invalid (phantom) parameters | A parameter was added that doesn't exist on the source action (e.g., `citationMode`) | Remove the parameter — it was copied from a similar action by mistake |
| "A source action is required" | Standard action missing `source:` field | Add `source:` with value from legacy `<source>` element |
| Invalid action target | Flow/Apex not found in org | Ask user to deploy the missing component first |
| Schema validation failure | Input/output schema doesn't match | Read error details + legacy schema, fix parameters in `.agent` file |
| Invalid variable reference | Variable used in reasoning doesn't exist | Add the variable or fix the reference |
| Compilation error on server | Server-side compiler found an issue | Fix the `.agent` file based on the server error |

**Fix procedure:**
1. Read the error message and identify the affected section of the `.agent` file.
2. Apply the fix to the `.agent` file.
3. Re-compile locally (FORBIDDEN: do NOT use `python`/`python3` — use `uv`):
   ```bash
   uv run --refresh --native-tls 00-start-migration/scripts/compile_agentscript.py AGENT_FILE_PATH
   ```
4. If local compilation fails, fix compilation errors first (see `05-compile-agentscript` skill).
5. Return to Step 5 to retry publish (publish handles both deploy and publish).

### Step 7: (Reserved for future use)

### Step 8: Verify and Report Success

After successful publish, verify the agent is accessible:

```bash
sf agent list --target-org TARGET_ORG
```

Look for `AGENT_NAME` in the output.

Display the success report:

```
============================================
   DEPLOYMENT SUCCESSFUL
============================================

Agent '{AGENT_NAME}' has been deployed and published.

   Org:          [instanceUrl]
   Username:     [username]
   Agent Name:   AGENT_NAME

   The agent is now available in Agentforce Builder.

Migration Summary:
   Source:             [LEGACY_BUNDLE_NAME] (genAiPlannerBundle)
   Target:             AGENT_NAME (aiAuthoringBundle / AgentScript)
   Topics migrated:    [count]
   Actions migrated:   [count]
   Variables defined:  [count]
   Publish iterations: PUBLISH_ITERATION

Next steps:
   1. Open Agentforce Builder and verify the agent's configuration
   2. Test the agent with sample conversations
   3. Compare behavior against the legacy agent
   4. Activate the agent when satisfied with testing
============================================
```

### Step 9: Report Failure (if max publish iterations reached)

```
============================================
   PUBLISH FAILED AFTER MAX_PUBLISH_ITERATIONS ATTEMPTS
============================================

Agent:    AGENT_NAME
Org:      [instanceUrl]
Username: [username]

Due to a transient issue, the agent could not be published automatically
after MAX_PUBLISH_ITERATIONS attempts.

============================================
   MANUAL DEPLOYMENT INSTRUCTIONS
============================================

Please deploy the agent manually using Agentforce Builder:

1. **Open Agentforce Builder**
   - Log in to your Salesforce org: [instanceUrl]
   - Navigate to Setup > Agentforce > Agents
   - Click "New Agent"

2. **Create New Agent**
   - Choose "Build Your Own"
   - Enter Agent Name: AGENT_NAME
   - Click "Create"

3. **Copy AgentScript Content**
   - The AgentScript file is located at:
     AGENT_FILE_PATH
   
   - Open this file and copy its entire content

4. **Paste in Script Editor**
   - In Agentforce Builder, click on "Script Editor" view
   - Delete any existing placeholder code
   - Paste the copied AgentScript content

5. **Validate AgentScript**
   - Click the "Validate" button in the Script Editor
   - Ensure all validations pass
   - Fix any errors if shown (refer to validation messages)

6. **Save the Agent**
   - Click "Save" to save the agent configuration
   - Activate the agent when ready for use

============================================
   ALTERNATIVE: CLI RETRY
============================================

If you prefer to retry via CLI:
   1. Review any errors above and apply fixes to: AGENT_FILE_PATH
   2. Re-compile: uv run --refresh --native-tls 00-start-migration/scripts/compile_agentscript.py AGENT_FILE_PATH
   3. Re-publish: sf agent publish authoring-bundle --api-name AGENT_NAME --target-org TARGET_ORG

============================================
```

## Output

- Deployed and published `aiAuthoringBundle` in the target Salesforce org (on success)
- Detailed error report with manual resolution steps (on failure)

## Migration Complete

The 6-skill migration pipeline is complete:

1. **01-retrieve-legacy-agent** — Retrieved and inventoried the legacy bundle
2. **02-design-agent-architecture** — Designed the optimal AgentScript architecture
3. **03-scaffold-agentscript** — Created the initial .agent file structure
4. **04-migrate-agent-topics** — Generated all topic blocks with actions and reasoning
5. **05-compile-agentscript** — Validated and fixed compilation errors
6. **06-deploy-agentscript** — Deployed and published to the target org

The legacy `genAiPlannerBundle` agent has been migrated to the new `aiAuthoringBundle`
(AgentScript) format.
