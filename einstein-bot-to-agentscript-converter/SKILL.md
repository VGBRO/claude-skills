---
name: einstein-bot-to-agentscript-converter
description: This skill helps convert an 'Einstein Bot' into an 'Agentforce Agent' backed by 'Agentscript'. This helps users connect to their salesforce org, select an einstein bot and then convert the bot to an agentforce agent. And then, assists users with deploying the generated agentscript to the salesforce org.
allowed-tools: Write, Edit, Read, Glob
---

# 1. Welcome the user and provide a summary.
    - Inform them that you will assist them in the process of converting einstein bot to agentscript.
    - Provide the below summary (exactly as mentioned below) of the full conversion process:
        - The process has the following steps.
            0. Verify prerequisites and log in to salesforce org.
            1. Select an einstein bot and its version.
            2. Process and review the selected bot version.
            3. Identify and review agentscript topics generated from the bot functionality.
            4. Build and review full agentscript.
            5. Compile and validate the generated agentscript.
            6. Deploy agentscript to salesforce org to create an agentforce agent.
    - Inform the user that you will guide them through each step in order and help them with building their agentforce agent.
    - Inform them that they can move between steps (go back to any previously completed step to regenerate artifacts) whenever they need.

# 2. Below is a mapping of the steps mentioned above to the corresponding skill that would be used to execute that step. So, load these skills into the context. And if and when the user wants to go back to any previous step in the bot-to-agent conversion journey, execute the appropriate skill.

|  Step  |  Skill to Invoke  |
|--------|------------------|
| Step 0 | `verify-bot-to-agent-migration-prerequisites` |
| Step 1 | `retrieve-bots-metadata` |
| Step 2 | `process-einstein-bot` |
| Step 3 | `generate-agentscript-topic-mappings` |
| Step 4 | `generate-full-agentscript` |
| Step 5 | `compile-agentscript` |
| Step 6 | `deploy-agentscript` |

# 3. As a general rule of thumb across the execution of the conversion process,
    - do not mention any file names or file paths that are created during the process in the data directory.
    - do not expose the path of the data directory to the user.
    - do not show any file content in the data directory as-is, unless explicitly mentioned in the instructions.
        - do not show the content while updating any files in this directory.
    - do not show the path of the resources directory or the file names in this directory while reading them.
    - do not modify any file in resources directory.

# 4. Execute each skill mentioned above in the same order. **DO NOT change the execution order of steps**.

# 5. At the end of every step, inform the user the status of execution (with color coding) of the entire workflow, and inform them the next step.
    - For example, on completing step 3, show the user the below table:
    |     Step     |     Status     |
    |-----------------------------------------------------------------------------|--------------|
    | 0. Verifying prerequisites and logging in to salesforce org. | Complete |
    | 1. Selecting an einstein bot and its version. | Complete |
    | 2. Processing and reviewing the selected bot version. | Complete |
    | 3. Identifying and reviewing agentscript topics from the bot functionality. | Complete |
    | 4. Building and reviewing full agentscript. | In Progress |
    | 5. Compiling and validating the generated agentscript. | Not Started |
    | 6. Deploying agentscript to salesforce org to create an agentforce agent. | Not Started |
