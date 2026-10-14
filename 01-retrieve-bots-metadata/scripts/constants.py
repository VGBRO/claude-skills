#!/usr/bin/env python3
"""
Central constants file for Step 1: Retrieve Bot Metadata
All hard-coded values are defined here for easy maintenance.
"""

# ============================================================================
# API VERSIONS
# ============================================================================
SALESFORCE_API_VERSION = "67.0"
SOURCE_API_VERSION = "62.0"
SALESFORCE_LOGIN_URL = "https://login.salesforce.com"

# ============================================================================
# PROJECT STRUCTURE
# ============================================================================
PROJECT_LEVELS_UP = 4
PACKAGE_DIR = "data/sf-cli"
MAIN_DEFAULT_DIR = "main/default"

# ============================================================================
# DIRECTORY NAMES
# ============================================================================
DIR_BOTS = "bots"
DIR_ML_DOMAINS = "mlDomains"
DIR_STEP1 = "step1"
DIR_XML = "xml"
DIR_JSON = "json"
DIR_APEX_INVOCATIONS = "apex-invocations"
DIR_CLASSES = "classes"
DIR_AI_AUTHORING_BUNDLES = "aiAuthoringBundles"

# ============================================================================
# FILE NAMES
# ============================================================================
FILE_BOT_INVOCATIONS = "bot-invocations.json"
FILE_PARSED_APEX_TYPES = "parsed-apex-types.json"
FILE_MERGED_INVOCATIONS = "merged-invocations.json"
FILE_PACKAGE_XML = "package.xml"

# ============================================================================
# BOT METADATA FIELD NAMES
# ============================================================================
# Fields that should ALWAYS be arrays, even with single element
ALWAYS_ARRAY_FIELDS = {
    'mlSlotClasses',
    'nlpProviders',
    'botVariableOperands',
    'mlIntentUtterances',
    'invocationMappings',
    'botStepConditions',
    'botSteps',
    'conversationVariables',
    'botDialogs',
    'contextVariables',
    'mlIntents',
    'botDialogGroups',
    'conversationSystemDialogs',
    'relatedMlIntents',
    'botNavigationLinks',
    'botMessages',
    'conversationRecordLookupFields',
    'lookupFields',
    'conditions',
    'entryDialog'
}

# Fields that should be converted from string to boolean
BOOLEAN_FIELDS = {
    'mlIntentTrainingEnabled',
    'showInFooterMenu',
    'isPlaceholderDialog',
    'optionalCollect',
    'articleAnswersGPTEnabled',
    'citationsEnabled',
    'intentDisambiguationEnabled',
    'knowledgeActionEnabled',
    'knowledgeFallbackEnabled',
    'smallTalkEnabled',
    'staticPromptsEnabled'
}

# ============================================================================
# APEX TYPE MAPPINGS
# ============================================================================
# Maps Apex types to Salesforce bot invocation types
APEX_TYPE_MAP = {
    'String': 'STRING',
    'Boolean': 'BOOLEAN',
    'Integer': 'INTEGER',
    'Long': 'INTEGER',
    'Double': 'NUMBER',
    'Decimal': 'NUMBER',
    'Date': 'DATE',
    'DateTime': 'DATETIME',
    'Time': 'TIME',
    'Id': 'STRING',
}

# ============================================================================
# PROCESSING CONSTANTS
# ============================================================================
BATCH_SIZE = 50
MAX_PACKAGE_ITEMS = 50

# ============================================================================
# FORMATTING CONSTANTS (for display tables)
# ============================================================================
BOT_TABLE_NAME_WIDTH = 30
BOT_TABLE_DESC_WIDTH = 45
BOT_TABLE_VERSION_WIDTH = 10
BOT_TABLE_DATE_WIDTH = 20
BOT_TABLE_TOTAL_WIDTH = 120

# ============================================================================
# SOQL QUERY
# ============================================================================
BOT_LIST_QUERY = """
SELECT BotDefinition.DeveloperName,
       BotDefinition.Description,
       VersionNumber,
       LastModifiedDate
FROM BotVersion
ORDER BY BotDefinition.DeveloperName, VersionNumber DESC
"""

# ============================================================================
# REGEX PATTERNS
# ============================================================================
REGEX_LIST_TYPE = r'List<(.+)>'
REGEX_APEX_VARIABLE = r'public\s+([\w<>]+)\s+(\w+)\s*;'
REGEX_INVOCABLE_METHOD = r'@InvocableMethod.*?\n\s*public\s+static\s+([\w<>,\s]+)\s+\w+\s*\((.*?)\)'

# ============================================================================
# SALESFORCE CLI COMMANDS
# ============================================================================
SF_CLI_RETRIEVE_ML_DOMAIN = "sf project retrieve start --metadata MlDomain:{domain_name}"
SF_CLI_RETRIEVE_START = "sf project retrieve start"
SF_CLI_ORG_DISPLAY = "sf org display --json"

# ============================================================================
# JSON KEYS (commonly used)
# ============================================================================
KEY_INPUT_PARAMETERS = "inputParameters"
KEY_OUTPUT_PARAMETERS = "outputParameters"
KEY_APEX = "apex"
KEY_FLOW = "flow"
KEY_INVOCATION_MAPPINGS = "invocationMappings"
KEY_TARGET_TYPE = "targetType"
KEY_TARGET = "target"
KEY_SOBJECT_TYPE = "sobjectType"
KEY_TYPE = "type"
KEY_NAME = "name"
KEY_REQUIRED = "required"
KEY_COLLECTION_TYPE = "collectionType"

# ============================================================================
# METADATA TYPES
# ============================================================================
METADATA_TYPE_BOT = "Bot"
METADATA_TYPE_BOT_VERSION = "BotVersion"
METADATA_TYPE_ML_DOMAIN = "MlDomain"
METADATA_TYPE_APEX_CLASS = "ApexClass"
METADATA_TYPE_FLOW = "Flow"

# ============================================================================
# PATH TEMPLATES
# ============================================================================
def get_step1_dir(org_id: str, bot_name: str, version: int) -> str:
    """Generate Step 1 directory path."""
    org_id_lower = org_id.lower()
    bot_name_lower = bot_name.lower()
    return f"data/bots/{org_id_lower}/{bot_name_lower}/v{version}/{DIR_STEP1}"

def get_bot_xml_path(bot_name: str) -> str:
    """Generate bot XML file path."""
    return f"{PACKAGE_DIR}/{MAIN_DEFAULT_DIR}/{DIR_BOTS}/{bot_name}/{bot_name}.bot-meta.xml"

def get_bot_version_xml_path(bot_name: str, version: int) -> str:
    """Generate bot version XML file path."""
    return f"{PACKAGE_DIR}/{MAIN_DEFAULT_DIR}/{DIR_BOTS}/{bot_name}/v{version}.botVersion-meta.xml"

def get_ml_domain_xml_path(domain_name: str) -> str:
    """Generate ML domain XML file path."""
    return f"{PACKAGE_DIR}/{MAIN_DEFAULT_DIR}/{DIR_ML_DOMAINS}/{domain_name}.mlDomain-meta.xml"
