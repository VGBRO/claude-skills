import json
import os

def run(data_directory, bot_name):
    if os.path.exists(data_directory + '/bot.json'):
        bot_file = data_directory + '/bot.json'
    elif os.path.exists(data_directory + '/' + bot_name + '.json'):
        bot_file = data_directory + '/' + bot_name + '.json'
    else:
        return
    
    with open(bot_file, 'r') as f:
        bot_json = json.loads(f.read())
    
    bot = bot_json.get('Bot', {})
    bot_version = bot.get('botVersions', [])[0]
    bot_intents = bot.get('botMlDomain', {}).get('mlIntents', [])

    actions = {}

    # process bot dialogs and dialog groups - build the dialog structure
    dialogs = {}
    intents_configured = False
    for bot_dialog in bot_version.get('botDialogs', []):
        dialog = {
            'dialog_group': bot_dialog.get('botDialogGroup', ''),
            'developer_name': bot_dialog.get('developerName', ''),
            'description': bot_dialog.get('description', ''),
            'label': bot_dialog.get('label', ''),
            'tools': [],
            'outbound_transitions': [],
        }

        for bot_dialog_step in bot_dialog.get('botSteps', []):
            dialog_step_type = bot_dialog_step.get('type', '')
            if dialog_step_type == 'Message':
                dialog['tools'].append({
                    'type': 'outbound_message',
                    'message': bot_dialog_step.get('botMessages')[0].get('message', '')
                })

            tool_call = bot_dialog_step.get('botVariableOperation', {}).get('botInvocation', {}) or bot_dialog_step.get('botInvocation', {})
            if tool_call:
                tool_call_name = tool_call.get('invocationActionName', '')
                tool_call_type = tool_call.get('invocationActionType', '')
                tool_call_parameters = tool_call.get('invocationMappings', [])
                dialog['tools'].append({
                    'type': 'tool',
                    'name': tool_call_name
                })
                actions[tool_call_name] = {
                    'target': f'{tool_call_type}::{tool_call_name}',
                    'variables_read': [param.get('variableName', '') for param in tool_call_parameters if param.get('type', '') == 'Input'],
                    'variables_written': [param.get('variableName', '') for param in tool_call_parameters if param.get('type', '') == 'Output'],
                }
            
            if dialog_step_type == 'Group':
                navigation = bot_dialog_step.get('botSteps')[0].get('botNavigation', {})
                if navigation:
                    navigation_target = navigation.get('botNavigationLinks')[0].get('targetBotDialog')
                    dialog['outbound_transitions'].append(
                        {
                            'target': navigation_target,
                            'type': navigation.get('type')
                        }
                    )
            
            if dialog_step_type == 'Wait':
                intents_configured = True
                dialog['outbound_transitions'].append(
                    {
                        'target': 'intent_redirect',
                        'type': 'Redirect'
                    }
                )

        dialogs[bot_dialog.get('developerName')] = dialog
    
    if intents_configured:
        dialogs['intent_redirect'] = {
            'dialog_group': None,
            'developer_name': 'intent_redirect',
            'description': 'Dialog that handles all user intent based redirections',
            'label': 'Intent Redirect',
            'tools': [],
            'outbound_transitions': [],
        }
        for bot_intent in bot_intents:
            dialogs['intent_redirect']['outbound_transitions'].append(
                {
                    'target': bot_intent.get('developerName'),
                    'type': 'Intent'
                }
            )

    bot_output = {
        'dialogs': dialogs,
        'actions': actions,
    }
    with open(data_directory + '/preprocessed_bot.json', 'w') as f:
        f.write(json.dumps(bot_output, indent=4))
        f.flush()