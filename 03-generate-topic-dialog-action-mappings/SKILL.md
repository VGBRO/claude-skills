---
name: generate-agentscript-topic-mappings
description: Generates topics for the agentscript backing an AI agent (agentforce agent). These topics would be generated from the preprocessed einstein bot data.
allowed-tools: Write, Edit, Read, Glob
---

# 0. Prerequisite

- If `topic_classification.json` file already exists in the data directory and the user has opted to reuse the existing artifacts in all the previous steps in the full conversion process,
    - ask the user explicitly if they want to skip this step. Something like - "You have opted to use the preprocessed artifacts in all the previous steps, and it looks like the topics were already generated for this bot version previously. Do you want to continue reusing the same output or do you want to identify the topics again?"
    - **DO NOT mention the file names or paths in question or do not expose the file names/paths to the user.**
    - **DO NOT mention that you looked for these files.**
    - If the user wants to use the existing output from a previously initiated conversion process, then show a message to the user like 'Proceeding to the next step..'. And give back the control.
    - If not, proceed to step #1 below.

# 1. Einstein bot concepts:

- Dialog: A dialog is a sequence of steps that are executed in order.
- Dialog group: A dialog group is a collection of dialogs that are related to each other. It is used to group dialogs into a single unit. This grouping could be a logical grouping or a hierarchical grouping or a functional grouping or a combination of these.
- Tool: A tool is an outbound message or a call to an action.
- Outbound transition: An outbound transition is a transition from one dialog to another.
    - Intent redirect: An intent redirect is an outbound transition type that is used to redirect the user to the appropriate dialog based on the user's intent.
    - Call: A call is an outbound transition type that is used to call a dialog. After the target dialog's steps are executed, the conversation will resume from the next step of the calling dialog.
    - Redirect: A redirect is an outbound transition type that is used to redirect the user to the target dialog. Unlike a call, the conversation will not resume from the next step of the calling dialog.
- Action: Can be used interchangeably with tool in this context. It is a function that can be called to perform an action. It is defined by the following information:
  - `target`: The target of the action.
  - `variables_read`: A list of variables that are read by the action i.e., the input variables to the action.
  - `variables_written`: A list of variables that are written by the action i.e., the output variables from the action.
- Variable: Variables that are used by einstein bot, to store the conversational state.

# 2. Parse the preprocessed bot data.

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

# 3. Agentforce/Agentscript concepts:

- Topic: An entity similar to a subagent - an AI subagent is expected to consume this configuration and perform actions related to that particular context, which are in the scope of the subagent. For example,
    - `Order Management` can be a topic with tools/actions `Create_Order`, `List_Orders`, `Cancel_Order` (and with the corresponding instructions on how/when to use the tools available).
    - `Queries and Grievances` can be a topic with tools/actions `Lookup_Answer_For_Query`, `Create_Ticket`, `Get_Ticket_Status` (and with the corresponding instructions on how/when to use the tools available).
- Action/Tool: This is similar to an invocable function, which can be used by an AI subagent to accomplish a task as per the instructions provided.

# 4. Generation of Topics and relevant information from the preprocessed bot.

The main exercise here is to identify a meaningful set of topics/subagents equivalent to the functionality that is executed by the einstein bot in a conversational flow. The output of this analysis should be as below (in json format):
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
    }
}
```

Follow the below steps to figure out the topics and the associated information.

## 1. Parse and understand preprocessed bot metadata.

From the preprocessed bot metadata, parse each action structure.
    - name/target: this name usually provides information about what the action/tool is intended to do. Extract the intention of the tool and the entity on which this operation will be performed. For example,
        - `lookup_results` indicates that the intention here is to `search a database/knowledge-base` and the entity on which this operation will be performed is a `query/question` with the output as `answers/results`.
        - `create_order` indicates that the intention here is to `create an entity` and the entity on which this operation will be performed is `order`.
    - variables_read: this is the list of variables storing conversational data, that are passed as inputs to the action/tool. These also provide information about the intention of the tool and the underlying entity.
    - variables_written: this is the list of variables storing conversational data, that are updated from the outputs of the action/tool. These also provide information about the intention of the tool and the underlying entity.

## 2. Group the actions/tools.

1. Group the actions/tools to represent topics. Each group of actions will represent a topic, and relevant instructions to be followed by the subagent would be generated. Group the actions based on the following priorities (highest priority criteria first). **CRITERIA**:
    - If the actions/tools are working on the same underlying entity, they **should** be grouped together.
    - If the actions/tools are updating/writing the same variable after execution, they **most likely** should be grouped together.
    - If the actions/tools are consuming/reading the same variable as input, they **most likely** should be grouped together.
    - If the dialogs invoking these actions/tools belong to the same dialog group, they **likely** should be grouped together.
    - If the actions/tools have similar intentions, they **can** be grouped together.

2. Have a maximum of 7 actions per topic, and a minimum of 1 action per topic.
    - If the number of actions goes more than 7, split the topic (based on the weighted criteria above) to maintain the highest priority criteria still valid.

3. **MOST IMPORTANT INSTRUCTION** - An action can be a part of multiple topics if the criteria mentioned above, demand this.

## 3. Trace back and construct dialog list for each topic.

1. For each of the topic that is generated/picked, build a list of dialogs associated with those actions. This can be done by back tracing the actions to the dialogs based on the `tools` attached to each dialog.
2. For every action that is associated with a dialog, add a mapping in `action_dialog_mapping` (from action to dialog list) to indicate that the functionality of the conversational path that renders this action/tool should be instructed to the subagent that will process this topic based on natural language instructions.
3. Generate a 2-3 sentence natural language description for each topic based on the associated actions/tools and the associated dialogs. This description should reflect the functionality of the subagent that would execute this topic actions via natural language instructions.

## 4. Output the result to `topic_classification.json` in the data directory. Verify that the format of the output is as below:
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
    }
}
```

# 5. Show Topic and Dialog/Action mapping summary.

- Provide information about the data. Inform the user that the following topics are generated based on their relevance, proximity (based on different criteria) and other similarities.
- Show the details of topics in a tabular format as below:
=======================================
TOPICS
=======================================
| Topic Name | Topic Description | Associated Dialog Names | Associated Action Names |
|------------|-------------------|-------------------------|-------------------------|

# 6. Wait for user response and feedback, and incorporate any changes suggested.

- Ask if they would like to add/edit/delete the topics and their corresponding dialogs or actions OR proceed to the next step.
    - Provide a few suggestions for making changes. Like -
        - Delete the topic `topic_name` and all the logic in it.
        - Why is the topic `topic_name` included in the generated list of topics?
        - Remove the dialog `dialog_name` from the topic `topic_name`.
        - Move the dialog `dialog_name` from the topic `topic_name` to topic `topic_name`.
- Restrict the user operations in this phase to only CRUD operations on the topics. Below are the operations:
    - User can add a new topic.
        - In this scenario, ask for the associated actions and dialogs. Provide a list of available actions and dialogs.
            - If the list of dialogs is too large (more than 30 dialogs), then inform the user about this and ask them to provide the dialog names directly. And then validate that the dialog actually exists in the bot. If not, nudge the user to provide the correct dialog name.
            - Do not allow user to add non-existent or new dialog or action.
        - Check if the provided dialogs or actions are already part of another topic (that has been generated). If so, then ask the user for confirmation to add it to the new topic.
        - While adding a new topic to the generated list of topics, verify the new topic configuration with the validations mentioned below (in step #7).
    - User can delete a topic.
        - In this scenario, ask for a confirmation before deleting the topic.
            - Provide info that the associated actions and dialogs would also be removed. And the corresponding logic might not be captured in the generated agentforce agent (agentscript).
            - Provide an alternate option to move the dialogs/actions to other topics first (if the logic is to be retained), and then delete the topic.
            - Provide another alternate option to merge multiple topics together.
            - If the user still wants to delete the topic, then move the topic (along with its associated actions and dialogs) to `deleted_topics` section in the `topic_classification.json` file.
    - User can edit a topic.
        - In this scenario, inform the user that they can move actions/invocations between topics. And the associated dialogs would be automatically moved to maintain consistency.
            - Associated dialog to an action can be found based on `action_dialog_mapping` within each topic.
        - When the user selects a topic, show the associated actions and ask to select which one should be moved. And then select the destination topic, and move the action/invocation along with associated dialog.
        - After all the changes are done, verify the new topic configuration with the validations mentioned below (in step #7).
- If the user question/query is out of the scope of these operations, then inform the user that the question is out of scope and reiterate the operations that you can perform and provide sample questions mentioned above.
- After every modification made by the user, print the updated table (maintain the same format as mentioned in step #5) and ask the user what they want to do.
- If the user wants to proceed to the next step, proceed to step #7.

# 7. Validate the topic-dialog-action mappings.

- Validate that the final mappings in `topic_classification.json` is valid.
    - For every action included in a topic, there should be at least one dialog included, which has the action invocation in the original bot.
    - Every dialog that is included in the topic should have invoked at least one action (that is included in the topic) in the original bot.
    - Verify that the `action_dialog_mapping` for every topic is valid.
- Finally, provide a message to the user like 'Proceeding to the next step..'.
