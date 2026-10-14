#!/bin/bash
################################################################################
# fetch_and_parse_invocations.sh
#
# Generic script to:
# 1. Extract Apex/Flow invocations from bot metadata JSON
# 2. Retrieve actual source code from Salesforce org
# 3. Parse @InvocableMethod signatures
# 4. Update bot JSON with correct type information
#
# Usage:
#   bash fetch_and_parse_invocations.sh <bot_json_path> <org_alias> [output_dir] [--quiet]
#
# Example:
#   bash fetch_and_parse_invocations.sh \
#     data/sf-cli/custom/<ORGID_BOTNAME_VERSION>/jsons/<BotName>.json \
#     <org-alias> \
#     data/apex-retrieve \
#     --quiet
################################################################################

set -e  # Exit on error

# Parse arguments
BOT_JSON_PATH="${1}"
ORG_ALIAS="${2}"
OUTPUT_DIR="${3:-data/apex-retrieve}"
QUIET_FLAG="${4}"

# Quiet mode support
QUIET="false"
if [ "$QUIET_FLAG" = "--quiet" ]; then
    QUIET="true"
fi

log() {
    if [ "$QUIET" = "false" ]; then
        echo "$@"
    fi
}

if [ -z "$BOT_JSON_PATH" ] || [ -z "$ORG_ALIAS" ]; then
    echo "Usage: $0 <bot_json_path> <org_alias> [output_dir] [--quiet]"
    log ""
    echo "Example:"
    echo "  $0 data/sf-cli/custom/<ORGID_BOTNAME_VERSION>/jsons/<BotName>.json <org-alias>"
    echo "  $0 <bot_json_path> <org-alias> data/apex-retrieve --quiet"
    exit 1
fi

# Check if bot JSON exists
if [ ! -f "$BOT_JSON_PATH" ]; then
    echo "❌ Error: Bot JSON not found: $BOT_JSON_PATH"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARSER_SCRIPT="$SCRIPT_DIR/parse_apex_invocable_methods.py"

if [ ! -f "$PARSER_SCRIPT" ]; then
    echo "❌ Error: Parser script not found: $PARSER_SCRIPT"
    exit 1
fi

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  Fetch & Parse Invocations"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log ""
log "Bot JSON : $BOT_JSON_PATH"
log "Org      : $ORG_ALIAS"
log "Output   : $OUTPUT_DIR"
log ""

# Create output directories
mkdir -p "$OUTPUT_DIR/classes"
mkdir -p "$OUTPUT_DIR/flows"

################################################################################
# Step 1.7.1: Extract invocation structure from bot metadata
################################################################################
log "━━━ Step 1.7.1: Extract Invocation Structure from Bot Metadata ━━━"

# Extract parameter names from bot metadata
BOT_INVOCATIONS_FILE="$OUTPUT_DIR/bot-invocations.json"
python3 "$SCRIPT_DIR/extract_invocations_from_bot.py" \
    "$BOT_JSON_PATH" \
    --output "$BOT_INVOCATIONS_FILE"

if [ ! -f "$BOT_INVOCATIONS_FILE" ]; then
    echo "❌ Failed to extract invocations from bot metadata"
    exit 1
fi

log ""

################################################################################
# Step 1.7.2: Extract Apex class names for retrieval
################################################################################
log "━━━ Step 1.7.2: Extract Apex Class Names ━━━"

APEX_CLASSES=$(python3 <<EOF
import json
import sys

try:
    with open('$BOT_JSON_PATH', 'r') as f:
        bot_data = json.load(f)
except Exception as e:
    print(f"Error loading bot JSON: {e}", file=sys.stderr)
    sys.exit(1)

apex_classes = set()
flow_names = set()

def find_invocations(obj):
    if isinstance(obj, dict):
        if 'invocationActionName' in obj:
            action_name = obj.get('invocationActionName')
            action_type = obj.get('invocationActionType', 'unknown')

            if action_type == 'apex':
                apex_classes.add(action_name)
            elif action_type == 'flow':
                flow_names.add(action_name)

        for value in obj.values():
            find_invocations(value)
    elif isinstance(obj, list):
        for item in obj:
            find_invocations(item)

find_invocations(bot_data)

# Print counts to stderr for logging
print(f"Found {len(apex_classes)} Apex classes", file=sys.stderr)
print(f"Found {len(flow_names)} Flows", file=sys.stderr)

# Print apex classes to stdout (space-separated)
print(' '.join(sorted(apex_classes)))
EOF
)

if [ -z "$APEX_CLASSES" ]; then
    log "⚠️  No Apex classes found in bot metadata"
    log ""
else
    APEX_COUNT=$(echo "$APEX_CLASSES" | wc -w | tr -d ' ')
    log "✅ Found $APEX_COUNT Apex classes"
    log ""
fi

################################################################################
# Step 1.7.3: Retrieve Apex classes from org
################################################################################
if [ -n "$APEX_CLASSES" ]; then
    log "━━━ Step 1.7.3: Retrieve Apex Classes from Org ━━━"

    APEX_COUNT=$(echo "$APEX_CLASSES" | wc -w | tr -d ' ')
    BATCH_SIZE=50

    if [ "$APEX_COUNT" -le "$BATCH_SIZE" ]; then
        # Single call for small number of classes
        log "  Retrieving $APEX_COUNT classes in single call..."
        log ""

        # Generate package.xml
        PACKAGE_XML="$OUTPUT_DIR/package.xml"
        cat > "$PACKAGE_XML" <<'PACKAGE_START'
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
PACKAGE_START

        # Add each class as a member
        for class in $APEX_CLASSES; do
            echo "        <members>$class</members>" >> "$PACKAGE_XML"
        done

        # Close the XML
        cat >> "$PACKAGE_XML" <<'PACKAGE_END'
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
PACKAGE_END

        # Single retrieve command (files go to data/sf-cli/main/default/classes/)
        if sf project retrieve start \
            --manifest "$PACKAGE_XML" \
            --target-org "$ORG_ALIAS" 2>&1 | grep -E "(Succeeded|Failed|Retrieved)"; then
            log "  ✅ Retrieved $APEX_COUNT classes successfully"

            # Copy retrieved files to output directory
            mkdir -p "$OUTPUT_DIR/classes"
            cp -r data/sf-cli/main/default/classes/*.cls "$OUTPUT_DIR/classes/" 2>/dev/null || true
            cp -r data/sf-cli/main/default/classes/*.cls-meta.xml "$OUTPUT_DIR/classes/" 2>/dev/null || true
        else
            log "  ❌ Failed to retrieve classes"
            log "  Check package.xml at: $PACKAGE_XML"
        fi

    else
        # Batching for large number of classes
        log "  Retrieving $APEX_COUNT classes in batches of $BATCH_SIZE..."
        log ""

        # Convert to array for batching
        APEX_ARRAY=($APEX_CLASSES)
        TOTAL_BATCHES=$(( (APEX_COUNT + BATCH_SIZE - 1) / BATCH_SIZE ))
        BATCH_NUM=0
        SUCCESS_BATCHES=0
        FAILED_BATCHES=0

        for ((i=0; i<${#APEX_ARRAY[@]}; i+=BATCH_SIZE)); do
            ((BATCH_NUM++))

            # Get batch slice
            BATCH_CLASSES=("${APEX_ARRAY[@]:i:BATCH_SIZE}")
            BATCH_COUNT=${#BATCH_CLASSES[@]}

            log "  Batch $BATCH_NUM/$TOTAL_BATCHES ($BATCH_COUNT classes)..."

            # Generate package.xml for this batch
            BATCH_PACKAGE_XML="$OUTPUT_DIR/package_batch_${BATCH_NUM}.xml"
            cat > "$BATCH_PACKAGE_XML" <<'BATCH_START'
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
BATCH_START

            # Add batch classes
            for class in "${BATCH_CLASSES[@]}"; do
                echo "        <members>$class</members>" >> "$BATCH_PACKAGE_XML"
            done

            # Close the XML
            cat >> "$BATCH_PACKAGE_XML" <<'BATCH_END'
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
BATCH_END

            # Retrieve this batch (files go to data/sf-cli/main/default/classes/)
            if sf project retrieve start \
                --manifest "$BATCH_PACKAGE_XML" \
                --target-org "$ORG_ALIAS" > /dev/null 2>&1; then
                log "    ✅ Batch $BATCH_NUM succeeded"
                ((SUCCESS_BATCHES++))
            else
                log "    ❌ Batch $BATCH_NUM failed"
                ((FAILED_BATCHES++))
            fi
        done

        log ""
        log "  Summary: $SUCCESS_BATCHES/$TOTAL_BATCHES batches succeeded"

        if [ $FAILED_BATCHES -gt 0 ]; then
            log "  ⚠️  Warning: $FAILED_BATCHES batches failed"
        fi

        # Copy retrieved files to output directory
        mkdir -p "$OUTPUT_DIR/classes"
        cp -r data/sf-cli/main/default/classes/*.cls "$OUTPUT_DIR/classes/" 2>/dev/null || true
        cp -r data/sf-cli/main/default/classes/*.cls-meta.xml "$OUTPUT_DIR/classes/" 2>/dev/null || true
    fi

    log ""
fi

################################################################################
# Step 1.7.4: Parse Apex classes to extract type information
################################################################################
if [ -n "$APEX_CLASSES" ]; then
    log "━━━ Step 1.7.4: Parse Apex Invocable Methods ━━━"

    PARSED_APEX_OUTPUT="$OUTPUT_DIR/parsed-apex-types.json"

    if [ "$QUIET" = "true" ]; then
        python3 "$PARSER_SCRIPT" \
            --apex-dir "$OUTPUT_DIR/classes" \
            --output "$PARSED_APEX_OUTPUT" >/dev/null 2>&1
    else
        python3 "$PARSER_SCRIPT" \
            --apex-dir "$OUTPUT_DIR/classes" \
            --output "$PARSED_APEX_OUTPUT"
    fi

    log ""
fi

################################################################################
# Step 1.7.5: Merge bot metadata with Apex types
################################################################################
if [ -f "$BOT_INVOCATIONS_FILE" ] && [ -f "$OUTPUT_DIR/parsed-apex-types.json" ]; then
    log "━━━ Step 1.7.5: Merge Bot Metadata with Apex Types ━━━"

    MERGED_OUTPUT="$OUTPUT_DIR/merged-invocations.json"

    if [ "$QUIET" = "true" ]; then
        python3 "$SCRIPT_DIR/merge_invocation_types.py" \
            --bot-invocations "$BOT_INVOCATIONS_FILE" \
            --apex-invocations "$OUTPUT_DIR/parsed-apex-types.json" \
            --output "$MERGED_OUTPUT" >/dev/null 2>&1
    else
        python3 "$SCRIPT_DIR/merge_invocation_types.py" \
            --bot-invocations "$BOT_INVOCATIONS_FILE" \
            --apex-invocations "$OUTPUT_DIR/parsed-apex-types.json" \
            --output "$MERGED_OUTPUT"
    fi

    log ""
fi

################################################################################
# Step 1.7.6: Update bot JSON with merged data
################################################################################
if [ -f "$OUTPUT_DIR/merged-invocations.json" ]; then
    log "━━━ Step 1.7.6: Update Bot JSON ━━━"

    UPDATED_BOT_JSON="${BOT_JSON_PATH%.json}_with_parsed_invocations.json"

    # Export variables so Python can access them
    export BOT_JSON_PATH
    export OUTPUT_DIR
    export UPDATED_BOT_JSON

    if [ "$QUIET" = "true" ]; then
        python3 <<'EOF'
import json
import sys
import os

try:
    bot_path = os.environ['BOT_JSON_PATH']
    output_dir = os.environ['OUTPUT_DIR']
    updated_path = os.environ['UPDATED_BOT_JSON']

    # Load original bot JSON
    with open(bot_path, 'r') as f:
        bot_data = json.load(f)

    # Load merged invocations
    with open(f'{output_dir}/merged-invocations.json', 'r') as f:
        merged_invocations = json.load(f)

    # Replace botInvocationsDescribeInfo with merged data
    bot_data['botInvocationsDescribeInfo'] = merged_invocations

    # Save updated bot JSON
    with open(updated_path, 'w') as f:
        json.dump(bot_data, f, indent=2)
except Exception as e:
    print(f"Error updating bot JSON: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    else
        python3 <<'EOF'
import json
import sys
import os

try:
    bot_path = os.environ['BOT_JSON_PATH']
    output_dir = os.environ['OUTPUT_DIR']
    updated_path = os.environ['UPDATED_BOT_JSON']

    # Load original bot JSON
    with open(bot_path, 'r') as f:
        bot_data = json.load(f)

    # Load merged invocations
    with open(f'{output_dir}/merged-invocations.json', 'r') as f:
        merged_invocations = json.load(f)

    # Replace botInvocationsDescribeInfo with merged data
    bot_data['botInvocationsDescribeInfo'] = merged_invocations

    # Save updated bot JSON
    with open(updated_path, 'w') as f:
        json.dump(bot_data, f, indent=2)

    print(f"✅ Updated bot JSON saved to:")
    print(f"   {updated_path}")
except Exception as e:
    print(f"Error updating bot JSON: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    fi

    log ""
fi

################################################################################
# Summary
################################################################################
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "  Apex Invocation Processing Complete"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log ""
log "✅ Bot invocations structure: $BOT_INVOCATIONS_FILE"
log "✅ Apex classes retrieved to: $OUTPUT_DIR/classes/"
log "✅ Apex type information: $OUTPUT_DIR/parsed-apex-types.json"
log "✅ Merged invocations: $OUTPUT_DIR/merged-invocations.json"

if [ -f "${BOT_JSON_PATH%.json}_with_parsed_invocations.json" ]; then
    echo "✅ Updated bot JSON: ${BOT_JSON_PATH%.json}_with_parsed_invocations.json"
fi

log ""
