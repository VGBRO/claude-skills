---
name: generate-full-agentscript
description: Generates the complete agentscript backing an AI agent (agentforce agent) from the pre-generated topics and the full einstein bot metadata/configuration. The topics and the bot data would be provided as input to this skill.
allowed-tools: Write, Edit, Read, Glob
---

# 0. Prerequisite

- If `agentscript.agent` file already exists in the data directory and the user has opted to reuse the existing artifacts in all the previous steps in the full conversion process,
    - ask the user explicitly if they want to skip this step. Something like - "You have opted to use the preprocessed artifacts in all the previous steps, and it looks like the agentscript was already generated for this bot version previously. Do you want to continue reusing the same output or do you want to generate the agentscript again?"
    - **DO NOT mention the file names or paths in question or do not expose the file names/paths to the user.**
    - **DO NOT mention that you looked for these files.**
    - If the user wants to use the existing output from a previously initiated conversion process, then show a message to the user like 'Proceeding to the next step..'. And give back the control.
    - If not, proceed to step #1 below.

- As this is a complex task, if this requires creation of an agent internally, provide the below message about what the agent would do to execute this task:
    ```
    1. Read through the output of bot preprocessing
    2. Understand the conversational flows in bot
    3. Understand the bot intents and redirections
    4. Reference pre-generated topic classification
    5. Generate full agentscript
    6. Validate the generated agentscript
    ```

# 1. Understand the agentscript/agentforce syntax.

## Definition of Agentforce agent (configured in Agentscript language).

An agentforce agent is an orchestrator AI agent working on top of a group of subagents. Each subagent has their own instruction set and a list of allowed tools/actions. The orchestrator agent works in harmony with the subagents by delegating tasks and following the global instructions provided to it.

## Agentforce agent Configuration schema (Agentscript language structure/syntax).

- First, lookup and understand `AgentScriptLexer.g4` and `AgentScriptParser.g4` files in the `grammar` folder in available resources. These are antlr files (lexer and parser) that define the structure and grammar of the agentscript language.
- `system` section captures system consumed values.
- `config` section provides configuration values and settings.
- `variables` section captures the configuration runtime variables used to store the session state.
- `knowledge` section captures the details of a knowledge base configured to provide the necessary information to answer queries.
- `topic/start_agent` in the language represents the subagent.
    - `actions` within a topic capture the tools that the topic/subagent has access to.
    - `reasoning` section with the topic captures the logic that should be followed by the subagent to execute the task.
        - `actions` within the reasoning section are equivalent to `tools` that can be used by LLM. They are references to actions within the scope of the topic, or references to some standard actions provided by the framework.
        - `instructions` within the reasoning section are natural language instructions followed by subagent to figure out the next steps to execute. Usually, reasoning happens in a loop (taking into consideration, the previous iterations' outputs).
    - `before_reasoning` section contains the logic that should be executed by the subagent before the reasoning loop starts. This is similar to hooks in subagent framework. This is only executed once before the reasoning starts (independent of the number of iterations in the reasoning loop).
    - `after_reasoning` section contains the logic that should be executed by the subagent after the reasoning loop ends. This is similar to hooks in subagent framework. This is only executed once after the reasoning ends (independent of the number of iterations in the reasoning loop).

# 2. Understand the einstein bot metadata's structure.

## Definition of Einstein Bot

An Einstein bot is an autonomous software which is equipped to execute certain steps based on the configured workflows and user inputs. Simply put, bot is an automation software which deterministically follows a certain workflow to execute pre-configured steps (in order) based on the Einstein Bot Configuration.


## Einstein Bot Configuration Schema

Einstein Bot metadata configuration has the following attributes:
- Bot: Object that stores all the metadata information about the configuration. A bot will only have one botVersion. A Bot is composed of the following attributes:

    - botVersions: Object that contains the conversation flow configuration for a given Bot. The main elements in a bot version include:
        - botDialogs: These are groups of botSteps which are executed in order. Steps are executed sequentially. A dialog can optionally have an associated "mlIntent" and in turn the sample "mlIntentUtterances" that come with it. Simply put, this dialog should be invoked if the corresponding intent is inferred from the user input. A botDialog has the following attributes:
            - developerName: Unique identifier of the dialog.
            - mlIntent: Name of the mlIntent entity attached to this dialog.
            - botSteps: These define the specific conversational actions followed within a dialog. Supported step types include:
                - Message: Outputs a message
                    - Navigation: Controls conversation flow by redirecting or calling another dialog via bot navigation links. Types of navigation include:
                        - Redirect: Stop executing the current stack of steps and move on to the target dialog. This is a transfer of control to the target dialog.
                            - An entity is used to capture the details of target bot dialog via field targetBotDialog.
                        - Call: Start executing the steps in the target dialog. After their execution is complete, resume the execution of the current dialog. This is similar to a function call, where the control returns after completion of execution of the function.
                            - An entity is used to capture the details of target bot dialog via field targetBotDialog.
                    - VariableOperation: Used to manipulate conversational variables, the supported types of variable operations include:
                        - Set: Explicitly assign a value to a variable from another variable or an explicit value. If the variable has to be assigned an explicit value based on output of invocable actions, this step will have a reference to an invocation step and the corresponding parameter to variable mappings.
                        - Unset: Clear a variable value.
                        - Collect : Asking a question to populate a value into a variable. For collect operations, we support providing static or dynamic options.
                            - An entity is used to define the applicable target variable data types and collection behavior. If a collect option has dynamic options it will have an internal invocation step with an output parameter mapping to populate the list of options.
                            - Normally, variable collection is only enforced if the target variable hasn’t been set. To override this, askCollectIfSet can be set to TRUE in order to always force a variable collection regardless of the variable state.
                        - SetConversationLanguage: Set a system-level variable that controls the user language.
                        - CollectAttachment: Used to collect a file from the user.
                    - Invocation: Represents and external invocation action which is triggered to achieve relevant intent. These actions specify mapping input/output parameters to conversationVariables. Each invocation has an associated botInvocation entity capturing the details of the invocation action name and invocation action type. Invocations can be backed by any of the following action types:
                        - apex
                        - flow
                        - standardInvocableAction
                        - externalService
                        - quickAction
                        - api
                        - logFeedback: Not relevant for Agents
                        - logGoalAchieved: Not relevant for Agents
                        - logDisambiguation: Not relevant for Agents
                    - Wait: Used to pause the conversation flow and switch control to the user to trigger an intent.
                    - Group: Used to create a composite step that wraps.
                    - SystemMessage: Used to trigger system level actions, examples of system messages include:
                        - Transfer: Initiate an action to transfer the conversation to a human.
                        - EndChat: Initiate an action to end the current conversation session.
                    - RecordLookup: Used to perform a query action against a defined SObject type and results are populated back into a list object variable.
                    - RichMessage: Used to send a rich message definition on supported channels. Examples of rich messages include:
                        - Authentication
                        - Forms
                        - Payments
                        - Time Selector
                        - Enhanced Links
                        - etc...
                    - GoalStep: Not relevant for Agents
                - conversationVariables:  List of custom variables used throughout the dialog flows. Supported variable data types include:
                    - Text
                    - Number
                    - Boolean
                    - Date
                    - DateTime
                    - Currency
                    - Id
                    - Object: This data type was used to capture complex data structures, like SObjects, Apex Types or Maps.
                - conversationSystemDialogs: These entries represent an assignment of a dialog to common system state behaviors. Supported behaviors include:
                    - TransferFailed
                    - ErrorHandling
                    - KnowledgeFallback
                    - Disambiguation
                    - DisambiguationFailed
                    - KnowledgeAction
                    - entryDialog (via a botVersion property)
                    - mainMenuDialog (via a botVersion property)

    - botMlDomain: This contains the details of all the intents associated with dialogs. A botMlDomain will have the following attributes:
        - mlIntents: List of all the intents. An mlIntent will have the following attributes:
            - developerName: Unique identifier for this intent.
            - description: A simple description of this intent.
            - mlIntentUtterances: List of sample sentences used to train an LLM for intent detection. These utterances can be in multiple languages like English, German, Spanish, French etc...

- botInvocationsDescribeInfo: This is a map containing the configuration of all apex and flow actions. Details of each action along with input/output parameter mappings would be captured against its name within the invocation action type entry in the map.

- availableAgentActions: A list of custom and standard agent actions that already exist in the customer's org for invocable actions used by the bot. We should not create new Agent actions for those invocationTargets that are exposed as availableAgentActions.

- mlRelatedData: Contains intent and entity data for related MlIntents and mlSlotClasses that are not present in the bot metadata.

# 3. Read the provided Einstein bot metadata's structure

Read the file `bot.json` from the data directory and parse the structure to map to the einstein bot metadata structure.

# 4. Parse the preprocessed bot data.

- Read the json content from `preprocessed_bot.json` file located in the data directory.
- This file contains the preprocessed bot data. This data is in the following structure:
  - `dialogs`: A dictionary of dialogs.
    - key: The developer name of the dialog. This is the unique identifier for the dialog.
    - value: A dictionary of dialog information.
      - `dialog_group`: The group of the dialog.
      - `developer_name`: The developer name of the dialog.
      - `description`: The description of the dialog.
      - `label`: The label of the dialog.
      - `tools`: A list of tools/actions used in the dialog.
      - `outbound_transitions`: A list of outbound transitions from the dialog.
        - `target`: The target dialog of the transition. This stores the developer name of the target dialog.
        - `type`: The type of the transition.
  - `actions`: A dictionary of actions.
    - key: unique identifier (developer name) of the action.
    = value: A dictionary of Action information.

# 5. Read the pre-selected topics and the topic-dialog mappings.

Read the file `topic_classification.json` from the data directory. This file has the below structure:
```
{
    "topics": {
        <topic_name>: {
            description: "",
            associated_dialogs: [],
            associated_actions: [],
            action_dialog_mapping: {
                <action_name>: [<dialog_list>]
            }
        }
    },
    "deleted_topics": {
        <topic_name>: {
            description: "",
            associated_dialogs: [],
            associated_actions: [],
            action_dialog_mapping: {
                <action_name>: [<dialog_list>]
            }
        }
    }
}
```

Below is the interpretation of this structure:
1. Each topic in the topics dictionary has been selected by carefully reviewing the einstein bot metadata. These are the topics/subagents that would be included in the agentforce agent to mimic/replicate the einstein bot functionality as best as possible.
2. Each topic has an associated list of actions/tools. These are the ones that the final topic/subagent will have access to.
3. Each topic has an associated list of bot dialogs. These are the dialogs from whose functionality the topic has been selected.
4. Each topic also has a mapping of action/tool name to a dialog list. This signifies that this topic/subagent should represent the execution behavior of the action in this set of dialogs (among the dialogs that are associated with the topic). Instructions for this topic should be generated based on the execution logic of these actions.
5. **Consider the deleted topics the same as the topics for which the agent configuration would be generated.**

# 6. Understand the intent digest.

Read the file `intent_digest.json` from the data directory. This file contains the below structure:
```
{
    <dialog_name>: <dialog_intent_description>
}
```

In the einstein bot metadata, intents can be configured corresponding to each dialog, indicating the purpose of the dialog via natural language utterances that can be used to train AI predictive models. When a user asks something, intent classification is done using this model to decide the next steps of execution.

Intent digest contains a summary/overview of the intent of every dialog for which an intent has been configured.


# 7. Generate the agentscript for the agentforce agent.

Follow the below steps to generate the final agentscript:

## 1. Generate system section in agentscript.

Format:
```
system:
    instructions: "You are a helpful customer service representative"
```

Generate a generic system instruction that reflects the following:
- The agent is an AI powered orchestrator
- The agent will help with a summary of all the topic descriptions combined

## 2. Generate config section in agentscript.

Sample structure:
```
config:
    agent_name: "ServiceBot"
    agent_id: "1"
    agent_type: "AgentforceServiceAgent"
    default_agent_user: "xyz@company.com"
```

- Generate the `agent_name` from a hash of a combination of botId (bot metadata json path `Bot.fullName`), botVersionId (bot metadata json path `Bot.botVersions[0].fullName`). Format of agent_name: `agent_<bot_name>_<hash>`.
- Leave the `default_agent_user` field as-is, to capture the placeholder value. Add a comment in the agentscript (as per the agentscript syntax) to inform the user that this field should be populated before using the agent.

## 3. Retain context variables.

Context variables are present in bot metadata at the json path `Bot.contextVariables`. Translate them as-is into `linked` variables in agentscript. Refer agentscript syntax to do this.

Sample variable in the agentscript:
```
<variable_name>: linked string = ''
    description: "dummy sample variable"
    source: @MessagingSession.<variable_name>
```

**IMPORTANT - Make sure to align with the agentscript syntax**

## 4. Generate knowledge section in agentscript.

Knowledge base in bot is used to lookup a user text, in case none of the intents configured in the bot match the query. This is more like a backup to serve the user better and acts like a catch-all cushion.

1. Find the dialog corresponding to knowledge feedback in bot. This would be a conversation system dialog (bot metadata json path `Bot.botVersions[0].conversationSystemDialogs`) of type `KnowledgeFeedback`.
2. If the dialog does not exist, knowledge is not configured in bot, and this knowledge block can be ignored in agentscript.
3. If the dialog exists, then add the knowledge block (leave the placeholders as-is), and add a comment to inform the user to update these values before using the agent.
4. Knowledge block format in agentscript :
```
knowledge:
   rag_feature_config_id: "<placeholder_id>"
   citations_enabled: True
   citations_url: "https://help.example.com"
```

## 5. Generate language section.

1. Language block format in agentscript :
```
language:
   default_locale: "en_US"
   additional_locales: "en_GB,de,fr"
   all_additional_locales: False
```
2. Iterate through `nlpProviders` (bot metadata json path `Bot.botVersions[0].nlpProviders`).
    - Capture the values in `language` field within each nlpProvider.
    - Filter this list of languages to include the ones that the agent supports. Agent supports the following locales:
        - de,fr,en_GB,en_AU,it,es,es_MX,ja,pt_PT,pt_BR,fr_CA,ca,nl_NL,da,no,sv,fi,zh_CN,zh_TW,ko
    - Exclude en_US from the list of languages.

## 6. Generate topics.

### 6.1 Create topics from pre-selected topics.

Follow the below steps for each topic in the selected topics:
1. Generate `actions` section. Create an action corresponding to every action/tool in `associated_actions` attached to the topic.
    - `target` in the action should be of the format "apex://<action_name>" or "flow://<action_name>".
        - If the action is not an apex or flow action, `target` should just contain the name of the action. Also, add a comment to indicate that this should be fixed before using the agent.
    - populate `inputs` and `outputs` for every action. Retrieve this information from `botInvocationsDescribeInfo` in bot metadata.
        - **Important Instruction** - Ensure that the names of the inputs and outputs match exactly with the provided data in `botInvocationsDescribeInfo`.
        - if inputs or outputs are of type object,
            - include the field `complex_data_type_name`. This can be obtained from the `sObjectType` in inputParameters or outputParameters in `botInvocationsDescribeInfo`.
            - if the value of the field `sObjectType` exists and starts with `lightning__`, retain the same value.
            - Else, hardcode the value of this field to `lightning__recordInfoType`.
    - Try to populate all the fields (including optional fields) in the action definitions.
2. Generate `reasoning` section.
    - Generate instructions and tools for each topic. To do this:
        - For every action in topic's `action_dialog_mapping`, go through the list of dialogs mapped to each action to find the logical flow in which the action would be executed. For example,
            - An action can be executed conditionally (variable condition)
            - An action can be executed based on user selection (from the menu options provided)
            - An action can be executed based on a user intent
            - An action can be executed in a conversational path based on redirections from one dialog to another
        - While understanding the logical flow of conversation, figure out the intent of the flow. Use the below things to figure out the intent:
            - The option selected by the user among a menu of options
                - for example, user selects an option to "Return item" (from the menu of options) -- intent is to return the product
            - The natural language input provided by the user matching an intent from the `intent_digest`
                - for example, user enters "I want to return a product", which matches with the intent digest of a dialog "Process_Return". So, the intent of redirection to this dialog was to "return a product/item"
        - Based on this logical flow of conversation:
            - Prepare a list of instructions providing a summary of what the action does, when to use this action/tool and the steps involved, and add it in the `instructions` section within reasoning block. These instructions
                - should capture the intent behind the logical conversational flow.
                - MUST capture the conditions (if any) for this flow to happen.
                - if invoking an action, **MUST** have the reference to action in the format `{!@actions.<action_name>}`.
                - Example of an instruction with a condition and an action reference: "If the user wants to login to their account, invoke {!@actions.user_login}".
            - Generate an action corresponding to this particular action/tool, and add it in the `actions` section within reasoning block.
                - Map input and output variables to these actions. Two possibilities here:
                    - if the value of the variable is required to be stored in conversational state, add an explicit variable for this (in the `variables` section in agentscript), and pass it as an input to the action. for example,
                        - if a variable value stores something retrieved from a previously executed action in the bot conversational flow, then retain the same behavior in the agentscript by adding a variable explicitly.
                        - a clear example of this would be: the user credentials or the logged-in user object, which would be accessed during the entire lifecycle of the conversation.
                    - if the value of the variable is not necessary for further conversation processing, then the subagent (via LLM) would automatically handle passing this variable value via user input. for example, 
                        - if the action input only requires something entered by the user for this particular step, then do not create a variable for this in the agentscript (as the agent can handle this on its own).
                        - a clear example of this would be: the booking id to be selected for cancellation (this would not be accessed across the conversation, and is only necessary until the cancellation is complete).
                - Do NOT assign state variables as inputs to actions, if they are not previously set by any action output explicitly.
                - Generate conditions for the tool to be available (`available when` in agentscript syntax). Two possibilities here:
                    - if the tool accepts a complex input that cannot be entered directly by the user, then this tool should only be available if the corresponding conversational variable holding this value in agentscript is populated.
                        - for example, a tool named `list_user_bookings`, which accepts logged-in user info, should only be populated if the variable corresponding to the logged-in user is populated.
                    - in all the possible logical conversational flows in the bot, if the tool/action is invoked only after a certain variable is set, then this tool should only be available if the corresponding conversational variable holding this value in agentscript is populated.
                - Update the state variables (mutable variables) in the agent based on the outputs of the action and the variables written by that particular action (this can be obtained from `preprocessed_bot.json`) by using `set` statement in the action definition.
                - A sample:
                    ```
                    reasoning:
                       actions:
                          profile_login: @actions.profile_login
                             available when @variables.user_profile is None
                             set @variables.user_profile = @outputs.logged_in_profile
                    ```
        - If the bot step contains a transition to another dialog which is part of another topic,
            - capture this as a tool in the reasoning section of the topic with signature `@utils.transition to @topic.<target_topic_name>`. For example,
                ```
                reasoning:
                   actions:
                      transition_to_target: @utils.transition to @topic.target_topic
                ```
            - add an instruction in the topic asking to invoke this action. For example, "Invoke {!@actions.transition_to_target} to move to the target topic."
        - If the bot step is of type `SystemMessage` with internal message type `Transfer` (which is intended to transfer the conversation to a human), then include a transition action with name `escalate_to_human` in the `reasoning.actions` list and include an instruction capturing when to invoke this action. For example,
            ```
            reasoning:
               actions:
                  escalate_to_human: @utils.escalate
               instructions: ->
                  | Invoke {!@actions.escalate_to_human} to escalate the conversation to a human agent.
            ```

### 6.2 Create topics routing to pre-selected topics.

The einstein bot may also contain some logic/functionality outside the dialogs attached to the pre-defined topics. So, in order to stitch everything together, follow the below steps:
1. Create a topic (mark it as `start_agent` in agentscript) to indicate the start of conversation. Name of the topic should be `agent_entrypoint`. Generate an appropriate description for this topic.
2. Parse through the `intent_digest`. If the bot has intent enabled dialogs,
    - create a topic with the name `topic_router`, corresponding to the intent routing.
    - Generate an appropriate description for the topic indicating that this topic routes the conversation according to the user's intention.
    - Add an outbound transition from `topic_router` to every other topic that has at least one dialog which has intent enabled (add the target topic's description as the description of the transition).
3. If the bot has at least one bot step of type `SystemMessage` with internal message type `Transfer` (which is intended to transfer the conversation to a human), then
    - create a connection with the name `escalate_to_human`, corresponding to transferring conversation to a human.
    - Generate an appropriate escalation_message for the connection indicating that this topic transfers conversation to a human.
    - outbound_route_type should be `OmniChannelFlow`.
    - Generate a meaningful outbound_route_name based on what the bot does, and what transferring to an agent means, given the context.
    - Sample:
        ```
        connection escalate_to_human:
           escalation_message: "Let me connect you with one of our agents who can better assist you."
           outbound_route_type: "OmniChannelFlow"
           outbound_route_name: "Emirates_Customer_Service_Queue"
           adaptive_response_allowed: True
        ```
3. Start traversing the bot metadata (in a DFS manner) starting from the `Welcome` dialog in the bot. Follow the below steps:
    - DFS graph structure:
        - Nodes are Bot Dialogs
        - Edges (uni-directional) are bot transitions (call/redirect) from source dialog to target dialog. These can be found in preprocessed_bot (`outbound_transitions`).
            - type=`call`: this transition type executes the target and brings the control back to the source. So, backtrack and resume the source execution to find the full conversational path.
            - type=`redirect`: this transition type executes the target and does not brings the control back to the source. So, continue with the next transitions.
            - type=`intent_redirect`: this transition type means a possible transition to any of the intent enabled dialogs (depending on the user input). Stop here.
    - **Important Instruction** - Stop DFS when a dialog which was already a part of the pre-selected topics is seen. This means that the control should move to the already generated topic via a transition in agentscript.
    - **Important Instruction** - If `intent_redirect` type transition is seen in the conversational path flow, add a transition to the topic `topic_router`, and generate appropriate description.
    - If a bot step of type `SystemMessage` with internal message type `Transfer` (which is intended to transfer the conversation to a human) is seen, then include a transition action with name `escalate_to_human` in the `reasoning.actions` list and include an instruction capturing when to invoke this action. For example,
            ```
            reasoning:
               actions:
                  escalate_to_human: @utils.escalate
               instructions: ->
                  | Invoke {!@actions.escalate_to_human} to escalate the conversation to a human agent.
            ```
    - Summarize each path (the steps in the path before another dialog which is already a part of the pre-selected topics is seen in the path). After covering all the paths, try to group these paths based on similarities. for example,
        - below are similar paths:
            - a path where user selects an option "modify profile", and enters "I want to update my password" in the next step
            - a path where user selects an option "modify profile", and enters "I want to update my phone" in the next step
    - For every meaningful group, create a topic in agentscript, with appropriate transitions (as `reasoning.actions`) and the instructions on when to use these transitions.
        - For example,
        ```
        reasoning:
           actions:
              transition_to_target: @utils.transition to @topic.target_topic
           instructions: ->
              | Invoke the tool {!@actions.transition_to_target} to transition to the target topic.
        ```
    - **Important Instruction** - Follow the agentscript syntax according to the grammar files.
4. **Important Instruction** - All the action references should be in the format `{!@actions.<action_name>}`. Modify the instructions to ensure this, if necessary.

### 6.3 Topic consolidation.

Among the generated topics, try to merge the topics if (highest criteria first):
- the topic is not a pre-generated topic.
- the topics don't have any actions.
- the topic descriptions are similar. similarity priority
    - underlying entity on which the topics/subagents are supposed to work on
    - underlying intention

Delete the topics generated corresponding to the `deleted_topics` in the `topic_classification.json` file. And delete any transition references to these topics in the rest of the agentscript.

# 8. Validations.

1. **Important Instruction** - Ensure that the final agentforce configuration (agentscript) adheres to the syntax of the agentscript as per the provided antlr files.
2. **Important Instruction** - Read through the rules provided at `rules/AGENT_SCRIPT_RULES.md` in the available resources and align the generated agentscript to strictly follow these rules.
3. If necessary, try fixing any syntax alignment issues by looking at examples in `recipes/AGENT_SCRIPT_RECIPES.xml` in the available resources.
4. Ensure that the transitions in the agentscript do not point to non-existent topics. If so, either modify the transition to point to the right topic or delete the transition and corresponding instructions.
5. Consolidate all the comments at the start of the agentscript. Comment starts with '#'.
6. Ensure that comments are added to explain every placeholder entry in the agentscript.
7. Ensure that all actions have correct input and output mappings in the right expected variable formats. If not, fix the problem by matching the format with `botInvocationsDescribeInfo` in bot metadata.
    - Ensure that the variable names in the actions generated match the variables inputs/outputs names provided in the corresponding action in `botInvocationsDescribeInfo`.
    - Ensure that if the input/output type is `object`, the value of `complex_data_type_name` is populated and starts with `lightning__`.
8. The agent execution starts from the topic labelled `start_agent`. Make sure that every other topic is reachable in any path via transitions. If a topic is not reachable, delete that topic.
9. Ensure that all the instructions that are referencing action invocations have the format {!@actions.<action_name>}.
10. Ensure that all the instructions that are referencing variables have the format {!@variables.<variable_name>}.

# 9. Wait for user response and feedback, and incorporate any changes suggested.

- First, inform the user that the agentscript has been generated successfully. Then, provide the below list of the sections generated in agentscript:
    1. system
    2. config
    3. variables
    4. knowledge
    5. language
    6. topics

- **Important Instruction** - Review the sections in the agentscript. DO NOT skip the review process by default.

## 1. Review `system` section in agentscript.

- Print ONLY the system section in the generated agentscript.
- Inform the user that the instructions in this section would apply to the entire agent in general. And help them update the instructions as per their requirements.
- If the user wants to update the error or welcome messages, help them do so.
    - User cannot delete these entries, as they are mandatory fields in an agentscript.
- If the user wants to do anything else, inform them that it is out of the scope for now.
- If the user wants to move to the next section, go to the next step.

## 2. Review `config` section in agentscript.

- Print ONLY the config section in the generated agentscript.
- Inform that they can modify the name of the agent if they want. And help them do it.
- **Important Instruction** - The user CANNOT modify `agent_type`. This should always be `AgentforceServiceAgent`. If they want to edit this, inform the user that this is a standard value provided for all agentforce service agents.
- Inform the user that they would have to create a new user in their salesforce org with agentforce service user permissions OR assign an existing user with those permissions, in the field `default_agent_user` before deploying the agent. Help them update this value if necessary.
- If the user wants to update the description, help them do so.
- User cannot delete any of these fields as they are all mandatory.
- If the user wants to do anything else, inform them that it is out of the scope for now.
- If the user wants to move to the next section, go to the next step.

## 3. Review `variables` section in agentscript.

- **Important Instruction** - User CANNOT delete the variables which are referenced in the agentscript.
- **Important Instruction** - User CANNOT modify the existing variables which are referenced in the agentscript.
- User can add more variables if necessary. Help them add new variables, and make sure they will align with the agentscript syntax.
- If the user wants to do anything else, inform them that it is out of the scope for now.
- If the user wants to move to the next section, go to the next step.

## 4. Review `knowledge` section in agentscript.

- Print ONLY the knowledge section in the generated agentscript.
- User can edit any field in this section. Help user update this section.
- User cannot add new fields in this section.
- If the user wants to do anything else, inform them that it is out of the scope for now.
- If the user wants to move to the next section, go to the next step.

## 5. Review `language` section in agentscript.

- Print ONLY the language section in the generated agentscript.
- User behavior for the three fields in this section:
    - `default_locale` - value should be one of the locales supported (that are mentioned above). This field is mandatory and hence should be populated.
    - `additional_locales` - comma separated list of supported locales.
    - `all_additional_locales` - Boolean (true/false) indicating if all locales should be supported.
- Provide the user the list of locales that can be added in each field.
- After user updates this section, validate that the locales provided in the fields are all valid.
- User cannot add new fields in this section.

## 6. Review topics in agentscript.

- First, provide the user with information about topics and what can be done with those. Like -
    - Each topic has a name, a description, a list of associated actions and a set of natural language instructions.
    - All of these are editable. And I will help you review each topic and update them whenever necessary.
- **Important Instruction** - User cannot add/delete any topic. They can only edit/update topics.
- User will review topics (marked as `topic` OR `start_agent`). Show the user one topic per step, and ask for modifications.
- Start with `start_agent` topic and continue to other topics. For every topic, do the following:
1. Print the following data:
    - topic configuration in a tabular format. Columns:
        - Topic Details
            - Contains topic name with topic description in braces.
        - Instructions
            - Contains an ordered list of natural language instructions for that particular topic.
            - **Print one instruction per line along with the instruction number.**
    - action configuration (`reasoning.actions`) in a tabular format. Columns:
        - Action name
        - Action type
            - `action` or `transition` or `variable_update`
        - Action condition
            - the variable condition. for example, `abc == 2`
        - State updates
            - state variable (mutable variable) updates after the action is performed
2. **Important Instruction** - Ordering of instructions is crucial as the LLM (GenAI agent) would later process the instructions in the same order as configured.
3. Ask the user if they want to edit any instructions or actions. **This is the most crucial step**. Provide the user with the below options along with a one line description as suggested below.
    - Reorder instructions (Instructions order can be changed based on the order in the numbered list provided)
    - Delete instructions (Instructions can be deleted based on the order in the numbered list provided)
    - Add instructions (Instructions can be added based on the order in the numbered list provided)
    - Consolidate instructions (Instructions can be merged based on the order in the numbered list provided)
    - Make instruction deterministic (Any action invocation or variable assignment or transition to other topics are eligible)
    - Move instructions to `before_reasoning` (if there are actions/tools to be executed before any decision making via LLM is involved in the topic execution - like any setup actions)
    - Move instructions to `after_reasoning` (if there are actions/tools to be executed after all decision making via LLM is complete in the topic execution - like any cleanup actions)
    - Update variable based conditions to reasoning actions
    - Update state updates post action execution
4. Maintain the instruction order whenever an instruction is added/updated/deleted. If necessary, ask the user where they want to insert/delete an instruction.
5. Allow adding, reordering, deleting and merging instructions. Help the user form a more meaningful instruction that can be understood by an AI agent.
6. If the user wants to make an instruction deterministic, follow the below steps:
    - The instruction is eligible for this operation only if it has an action invocation (like `{!@actions.<action_name>}`) or a variable assignment (like `{!@variables.<variable_name>}`) or a transition via action execution (like invoking an action which has the signature `@utils.transition to @topic.<topic_name>`).
    - Deterministic instruction format:
        - Conditional action invocation sample:
            ```
               if @variables.<variable_name> == False:
                  run @actions.<action_name>
            ```
        - Conditional variable assignment sample:
            ```
               if @variables.<variable_name> is None:
                  set @variables.<variable_name> = 0
            ```
        - Conditional transition sample:
            ```
               if @variables.<variable_name> is not None:
                  @utils.transition to @topic.<topic_name>
            ```
    - If the instruction is not eligible for this conversion, inform the user about this, and ask them what to do next.
    - Convert the natural language instruction to a deterministic instruction. **Capturing the condition is very important to retain the logic exactly**.
    - **Important Instruction** - Conditional deterministic instruction is only supported over variable conditions (like `@variables.xyz == 1` or `@variables.xyz is not None` or `@variables.xyz == True`). If the condition is a natural language instruction and cannot be converted into an equivalent variable condition, ask the user to provide an equivalent variable condition. If this is not possible, inform the user that the instruction cannot be converted into a deterministic instruction.
    - Help user to modify the instruction if necessary. For example, user can ask - "Add a condition for the variable value xyz to be equal to 5, to execute this instruction".
    - Ask the user if they want to move this instruction to `before_reasoning` or `after_reasoning`. If they want to do so, move this particular instruction to the corresponding section in the topic.
7. If the user wants to move the instruction to `before_reasoning` or `after_reasoning`, move this particular instruction to the corresponding section in the topic.
8. If the user wants to modify any action conditions OR state updates post action execution, help them do so, and validate that the conditions and updates are based on the variables (can be mutable variables or linked variables).
7. If the user edits instructions - at every step, print the updated instruction list for that particular topic (along with `before_reasoning` and `after_reasoning` sections if applicable).
8. Before updating the instructions list, make sure that there are no references to actions that are not actually attached to the topic. If there are any such references, inform the user and ask them what to do about it.
9. **Important Instruction** - Maintain the indentation while editing instructions, so that the agentscript syntax is adhered to.
10. Before updating the final topic, ask the user for confirmation by showing the final instruction list for that particular topic.

- Once all the topics have been reviewed, inform the user that you would be saving the final agentscript.

# 10. Output the agentscript

- Validate that the agentscript follows all the rules mentioned in step # 8.
- Write the generated agentscript to `agentscript.agent` in the data directory.
- Finally, provide a message to the user like 'Proceeding to the next step..'.
