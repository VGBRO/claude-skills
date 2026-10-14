---
name: process-einstein-bot
description: Pre-processes an einstein bot's structure to filter out noise, and retain relevant data necessary to convert the bot into an agentscript backing an AI agent (agentforce agent).
allowed-tools: Write, Edit, Read, Glob
---

# 0. Prerequisite

- If both `preprocessed_bot.json` and `intent_digest.json` files already exists in the data directory,
    - ask the user explicitly if they want to skip this step. Something like - "It looks like this version of the bot has already been processed before. Do you want to reuse the same output or do you want to process the bot again?"
    - **DO NOT mention the file names or paths in question or do not expose the file names/paths to the user.**
    - **DO NOT mention that you looked for these files.**
    - If the user wants to use the existing output from a previously initiated conversion process, then show a message to the user like 'Proceeding to the next step..'. And give back the control.
    - If not, proceed to step #1 below.

# 1. Reformat and refine the bot structure.

Import `preprocess_bot.py` from `scripts` folder and invoke the `run` method in the file by passing the data directory and the bot name as inputs.

# 2. Process Bot Intents.

- Inform the user that you're processing the intents configured in the bot dialogs to understand the redirections.
- First, read the json content at the path `Bot.botMlDomain.mlIntents` from `bot.json` file located in the data directory.
- This data represents a set of intents. Every intent will have the following information:
  - `description`: The description of the intent.
  - `developerName`: The developer name of the intent.
  - `label`: The name of the intent.
  - `mlIntentUtterances`: An array of objects used to train a predictive AI model to understand the particular intent and later classify the user's input into the intent.
    - `utterance`: The natural language utterance used to train the intent.
- Create an intent digest (a json dictionary) in the following structure:
    - key: The developer name of the intent.
    - value: A 2-3 sentence description/summary of the user's intent. This description would later be used by a generative AI agent as a subagent's context to match against the user's intent.
- Save the intent digest to `intent_digest.json` file in the data directory.

# 3. Show Bot Details.

Show the bot details in a tabular format as suggested below:

1. Show action/invocation details. Here, action_type can be `apex` or `flow` or `standardInvocableAction` or similar.
=======================================
ACTIONS
=======================================
| Action/Invocation Name | Invocation Type |
|------------------------|------------------|
| <action_name> | <action_type> |

2. Show dialogs containing at least one action, and a comma-separated list of actions in the dialog.
=======================================
DIALOGS WITH ACTIONS
=======================================
| Dialog Name | Actions/Invocations |
|------------------------|------------------|
| <dialog_name> | <list_of_actions_in_the_dialog> |

- Do not show the generated files or file paths to the user.

# 4. Wait for user response.

- Ask if they have any questions related to the bot metadata or if they want to proceed further to the next step.
    - Provide a few suggestions for questions. Like -
        - Summarize dialogs with actions/invocations.
        - Summarize dialogs with intents.
        - Show all actions/invocations.
        - Show details of any particular apex/flow action.
- If the user has any questions, look for the answers from the content in the generated files (`intent_digest.json` or `preprocessed_bot.json`) or the original `bot.json` file.
    - If the question is out of the scope of these files, then inform the user that the question is out of scope and inform them that you can answer questions related to the bot configuration and provide examples of questions about dialogs, actions, dialog to action mappings etc.
    - If the user asks questions about all the dialogs, and if there are too many dialogs in the bot (more than 20), nudge user towards a more specific question instead of displaying all the dialogs at once.
    - User CANNOT ask to modify/update any information about the bot. And hence, the generated files and the original bot json file cannot be modified via user interactions at this point. This is only an informational interaction with the user and not intended to take any feedback from the user.
**IMPORTANT INSTRUCTION** - Do not make any changes to `bot.json` or `preprocessed_bot.json` or `intent_digest.json` files while interacting with the user.
- If the user wants to proceed to the next step, provide a message to the user like 'Proceeding to the next step..'.
