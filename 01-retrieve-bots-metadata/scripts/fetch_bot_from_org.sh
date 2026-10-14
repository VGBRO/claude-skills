#!/bin/bash
# Fetch Einstein Bot metadata from Salesforce org and convert to JSON
# This script retrieves bot structure, invocations, and ML training data

set -e

# Verbose mode - set DEBUG=1 to see all substeps
VERBOSE="${DEBUG:-false}"

log() {
    if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "1" ]; then
        echo "$@"
    fi
}

BOT_NAME="${1}"
ORG="${2:-}"
ML_DOMAIN="${3:-}"  # Optional - will auto-discover if not provided
SKIP_OVERWRITE_CHECK="${4:-}"  # Optional - set to "--skip-overwrite-check" to skip the prompt

# Check if first argument is "interactive"
if [ "$BOT_NAME" = "interactive" ]; then
    INTERACTIVE="true"
    BOT_NAME=""  # Clear bot name so it will be selected interactively

    if [ -z "$ORG" ]; then
        echo "Error: Org alias required for interactive mode"
        echo ""
        echo "Usage: $0 interactive <ORG_ALIAS> [--skip-overwrite-check]"
        echo ""
        echo "Example:"
        echo "  $0 interactive my-org"
        echo "  $0 interactive my-org --skip-overwrite-check"
        exit 1
    fi

    # In interactive mode, 3rd argument can be skip flag (no ML_DOMAIN in interactive)
    if [ "$ML_DOMAIN" = "--skip-overwrite-check" ]; then
        SKIP_OVERWRITE_CHECK="--skip-overwrite-check"
        ML_DOMAIN=""
    fi
else
    INTERACTIVE="false"

    if [ -z "$BOT_NAME" ]; then
        echo "Usage: $0 <BOT_NAME> [ORG_ALIAS] [ML_DOMAIN] [--skip-overwrite-check]"
        echo "   or: $0 interactive <ORG_ALIAS>"
        echo ""
        echo "Examples:"
        echo "  $0 MyBot my-org"
        echo "  $0 MyBot my-org MyMLDomain"
        echo "  $0 interactive my-org            # Interactive bot selection"
        echo ""
        echo "This will:"
        echo "  1. Retrieve bot metadata from Salesforce org"
        echo "  2. Retrieve ML training data (intents + utterances)"
        echo "  3. Extract complete bot structure"
        echo "  4. Save as data/bot.json (ready for migration pipeline)"
        echo ""
        exit 1
    fi
fi

# Determine project root (4 levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

echo "Step 1 — Retrieve Bot Metadata from SF Org"
echo ""

# Step 1.1: Ensure SF project exists (SILENT unless error)
log "Step 1.1: Checking Salesforce DX project setup..."

if [ ! -f "$PROJECT_ROOT/sfdx-project.json" ]; then
    cd "$PROJECT_ROOT"

    if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "1" ]; then
        sf project generate \
            --name "bot-to-agent-migration" \
            --template "empty" \
            --output-dir "."
    else
        sf project generate \
            --name "bot-to-agent-migration" \
            --template "empty" \
            --output-dir "." >/dev/null 2>&1
    fi

    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create Salesforce DX project"
        exit 1
    fi

    # Update sfdx-project.json to use data/sf-cli as package directory
    cat > "$PROJECT_ROOT/sfdx-project.json" <<'EOF'
{
  "packageDirectories": [
    {
      "path": "data/sf-cli",
      "default": true
    }
  ],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "62.0"
}
EOF
fi

log "  ✓ sfdx-project.json exists"
log "  ✓ Package directory structure ready"
log ""

# Ensure package directory structure exists
mkdir -p "$PROJECT_ROOT/data/sf-cli/main/default" 2>/dev/null
mkdir -p "$PROJECT_ROOT/data/resources" 2>/dev/null

# Remove force-app directory if it exists (SF CLI will use it instead of data/sf-cli)
rm -rf "$PROJECT_ROOT/force-app" 2>/dev/null

# Remove any empty metadata directories that cause SF CLI scandir errors
rmdir "$PROJECT_ROOT/data/sf-cli/main/default/bots" 2>/dev/null || true
rmdir "$PROJECT_ROOT/data/sf-cli/main/default/mlDomains" 2>/dev/null || true
rmdir "$PROJECT_ROOT/data/sf-cli/main/default/aiAuthoringBundles" 2>/dev/null || true

# Step 1.1.1: Interactive bot selection (if enabled)
if [ "$INTERACTIVE" = "true" ]; then
    # Run interactive bot selector - redirect only the SELECTED_BOT line to capture it
    TEMP_OUTPUT=$(mktemp)

    # Run the script with full terminal access, capture only the output
    python3 "$SCRIPT_DIR/list_bots_interactive.py" "$ORG" 2>&1 | tee "$TEMP_OUTPUT"
    EXIT_CODE=${PIPESTATUS[0]}

    if [ $EXIT_CODE -ne 0 ]; then
        rm -f "$TEMP_OUTPUT"
        echo ""
        echo "Bot selection cancelled or failed."
        exit 0
    fi

    # Extract selected bot name and version from captured output
    SELECTED_BOT=$(grep "SELECTED_BOT=" "$TEMP_OUTPUT" | cut -d'=' -f2)
    SELECTED_VERSION=$(grep "SELECTED_VERSION=" "$TEMP_OUTPUT" | cut -d'=' -f2)
    rm -f "$TEMP_OUTPUT"

    if [ -z "$SELECTED_BOT" ]; then
        echo ""
        echo "No bot selected. Exiting."
        exit 0
    fi

    # Set BOT_NAME to selected bot
    BOT_NAME="$SELECTED_BOT"

    # Log selected version (optional, for user visibility)
    if [ -n "$SELECTED_VERSION" ]; then
        log "  ✓ Selected version: v${SELECTED_VERSION}"
    fi

    echo ""
fi

# Step 1.2: Get org ID and bot version to create folder name
log "Step 1.2: Getting org details and bot version..."

# Get org ID (suppress JSON output since we parse it, not user-facing)
if [ -z "$ORG" ]; then
    ORG_INFO=$(sf org display --json 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "❌ Error: No default org set. Please specify org with --target-org or set a default org."
        echo "   Run: sf org display to check available orgs"
        exit 1
    fi
else
    ORG_INFO=$(sf org display --target-org "$ORG" --json 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to get org details for: $ORG"
        echo "   Check that the org alias is correct and you're authenticated."
        exit 1
    fi
fi

ORG_ID=$(echo "$ORG_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('result', {}).get('id', ''))" 2>/dev/null)

if [ -z "$ORG_ID" ]; then
    echo "❌ Error: Failed to retrieve org ID from org info"
    exit 1
fi

log "  ✓ Org ID: $ORG_ID"

# Use selected version from interactive mode if available, otherwise query org
if [ -n "$SELECTED_VERSION" ]; then
    BOT_VERSION="$SELECTED_VERSION"
    log "  ✓ Bot Version: $BOT_VERSION (from selection)"
else
    # Query bot version (suppress JSON output since we parse it, not user-facing)
    if [ -z "$ORG" ]; then
        BOT_VERSION_QUERY=$(sf data query --query "SELECT VersionNumber FROM BotVersion WHERE BotDefinition.DeveloperName='${BOT_NAME}' ORDER BY VersionNumber DESC LIMIT 1" --json 2>/dev/null)
    else
        BOT_VERSION_QUERY=$(sf data query --query "SELECT VersionNumber FROM BotVersion WHERE BotDefinition.DeveloperName='${BOT_NAME}' ORDER BY VersionNumber DESC LIMIT 1" --target-org "$ORG" --json 2>/dev/null)
    fi

    BOT_VERSION=$(echo "$BOT_VERSION_QUERY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['result']['records'][0]['VersionNumber'] if data['result']['records'] else '1')")

    if [ -z "$BOT_VERSION" ]; then
        log "  ⚠️  Could not determine bot version, defaulting to 1"
        BOT_VERSION="1"
    fi

    log "  ✓ Bot Version: $BOT_VERSION (from query)"
fi

# Define new directory structure with lowercase paths
# Convert to lowercase for directory paths
ORG_ID_LOWER=$(echo "$ORG_ID" | tr '[:upper:]' '[:lower:]')
BOT_NAME_LOWER=$(echo "$BOT_NAME" | tr '[:upper:]' '[:lower:]')

# Define paths
BOT_VERSION_DIR="$PROJECT_ROOT/data/bots/${ORG_ID_LOWER}/${BOT_NAME_LOWER}/v${BOT_VERSION}"
STEP1_DIR="${BOT_VERSION_DIR}/step1"
FINAL_OUTPUT_FILE="${BOT_VERSION_DIR}/${BOT_NAME}.json"

log "  ℹ️  Will organize files into: bots/${ORG_ID_LOWER}/${BOT_NAME_LOWER}/v${BOT_VERSION}"

# Check if bot metadata already exists (check for final JSON file, not just directory)
if [ -f "$FINAL_OUTPUT_FILE" ] && [ "$SKIP_OVERWRITE_CHECK" != "--skip-overwrite-check" ]; then
    echo ""
    echo "⚠️  ${BOT_NAME}.json already exists for version ${BOT_VERSION}"
    echo ""
    echo "Do you want to overwrite the existing data?"
    echo ""
    echo "  [yes]  Overwrite and re-retrieve metadata"
    echo "  [no]   Skip retrieval (use existing data)"
    echo ""
    echo "Your choice: "
    read OVERWRITE_CHOICE

    case "${OVERWRITE_CHOICE,,}" in
        yes|y)
            log "  🗑️  Cleaning previous run: $BOT_VERSION_DIR"
            rm -rf "$BOT_VERSION_DIR"
            echo ""
            ;;
        no|n|skip)
            echo ""
            echo "✅ Skipping retrieval. Using existing ${BOT_NAME}.json"
            echo ""
            echo "File location:"
            echo "  ${FINAL_OUTPUT_FILE}"
            echo ""
            echo "Next Step:"
            echo "  /02-process-and-build-inventory"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo "❌ Invalid choice. Please run again and choose 'yes' or 'no'."
            exit 1
            ;;
    esac
elif [ -f "$FINAL_OUTPUT_FILE" ] && [ "$SKIP_OVERWRITE_CHECK" = "--skip-overwrite-check" ]; then
    # Explicit skip flag passed - just clean and proceed
    log "  🗑️  Cleaning previous run: $BOT_VERSION_DIR"
    rm -rf "$BOT_VERSION_DIR"
fi

log ""

# Show single user-facing message (always shown, not verbose-gated)
echo "Downloading metadata for ${BOT_NAME}..."
echo ""

# Step 1.3: Retrieve bot metadata
log "Step 1.3: Retrieving bot metadata from Salesforce org..."
log ""

# Change to project root for SF CLI commands
cd "$PROJECT_ROOT"

# Always show SF CLI output (it has useful progress info)
if [ -z "$ORG" ]; then
    sf project retrieve start \
        --metadata "Bot:${BOT_NAME}"
else
    sf project retrieve start \
        --metadata "Bot:${BOT_NAME}" \
        --target-org "${ORG}"
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error: Failed to retrieve bot metadata"
    echo "   Check that:"
    echo "     - Bot name is correct (DeveloperName, not Label)"
    echo "     - You're authenticated to the org"
    echo "     - The bot exists in the org"
    exit 1
fi

log ""

# Step 1.4: Auto-discover ML domains from bot metadata (if not provided)
log "Step 1.4: Auto-discovering ML domains..."
log ""

if [ -z "$ML_DOMAIN" ]; then
    # Parse bot metadata to find relatedMlIntents (from default location)
    DEFAULT_BOT_DIR="$PROJECT_ROOT/data/sf-cli/main/default/bots/${BOT_NAME}"
    BOT_META_FILE="${DEFAULT_BOT_DIR}/${BOT_NAME}.bot-meta.xml"

    if [ -f "$BOT_META_FILE" ]; then
        # Extract ML domain names from relatedMlIntent tags (format: "DomainName.IntentName")
        DISCOVERED_DOMAINS=$(grep -o '<relatedMlIntent>[^<]*</relatedMlIntent>' "$BOT_META_FILE" | \
                            sed 's/<[^>]*>//g' | \
                            cut -d'.' -f1 | \
                            sort -u | \
                            tr '\n' ' ')

        if [ -n "$DISCOVERED_DOMAINS" ]; then
            log "  ✓ Discovered ML domain(s): $DISCOVERED_DOMAINS"
            ML_DOMAINS_TO_FETCH="$DISCOVERED_DOMAINS"
        else
            log "  ℹ  No external ML domains referenced - will use bot's internal mlDomain only"
            ML_DOMAINS_TO_FETCH=""
        fi
    else
        log "  ⚠️  Bot metadata file not found, skipping auto-discovery"
        ML_DOMAINS_TO_FETCH=""
    fi
else
    log "  ℹ  Using provided ML domain: $ML_DOMAIN"
    ML_DOMAINS_TO_FETCH="$ML_DOMAIN"
fi

log ""

# Step 1.5: Retrieve ML training data
if [ -n "$ML_DOMAINS_TO_FETCH" ]; then
    log "Step 1.5: Retrieving ML training data..."
    log ""

    # Ensure we're in project root for SF CLI commands
    cd "$PROJECT_ROOT"

    ML_DOMAIN_RETRIEVED=false

    for DOMAIN in $ML_DOMAINS_TO_FETCH; do
        log "  Fetching ML domain: $DOMAIN"

        # Capture stderr to temp file to avoid flooding console
        TEMP_ERR=$(mktemp)

        if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "1" ]; then
            if [ -z "$ORG" ]; then
                sf project retrieve start \
                    --metadata "MlDomain:${DOMAIN}" 2>&1
                EXIT_CODE=$?
            else
                sf project retrieve start \
                    --metadata "MlDomain:${DOMAIN}" \
                    --target-org "${ORG}" 2>&1
                EXIT_CODE=$?
            fi
        else
            if [ -z "$ORG" ]; then
                sf project retrieve start \
                    --metadata "MlDomain:${DOMAIN}" >"$TEMP_ERR" 2>&1
                EXIT_CODE=$?
            else
                sf project retrieve start \
                    --metadata "MlDomain:${DOMAIN}" \
                    --target-org "${ORG}" >"$TEMP_ERR" 2>&1
                EXIT_CODE=$?
            fi

            # Only show errors if command failed (ignore ENOENT scandir warnings)
            if [ $EXIT_CODE -ne 0 ]; then
                grep -v -E "(ENOENT.*scandir|Error \(ENOENT\):)" "$TEMP_ERR" || true
            fi
        fi
        rm -f "$TEMP_ERR"

        # Check if files were actually retrieved
        if [ -f "$PROJECT_ROOT/data/sf-cli/main/default/mlDomains/${DOMAIN}.mlDomain-meta.xml" ]; then
            log "    ✓ Retrieved $DOMAIN"
            ML_DOMAIN_RETRIEVED=true
        else
            log "    ⚠️  Failed to retrieve $DOMAIN (may not exist in org)"
        fi
    done

    if [ "$ML_DOMAIN_RETRIEVED" = false ]; then
        log ""
        log "  ⚠️  No ML domains retrieved successfully"
        log "  Continuing with bot's internal mlDomain only..."
    fi
else
    log "Step 1.5: Skipping ML domain retrieval (none specified or discovered)"
    ML_DOMAIN_RETRIEVED=false
fi

log ""

# Step 1.5.1: Copy all retrieved files to step1 organized folder
log "Step 1.5.1: Copying files to step1 folder..."
log ""

# Create step1 folder structure
mkdir -p "$STEP1_DIR/xml/bots"
mkdir -p "$STEP1_DIR/xml/mlDomains"
mkdir -p "$STEP1_DIR/json"
mkdir -p "$STEP1_DIR/apex-invocations/classes"

# Copy bot XML files to step1/xml/bots/
DEFAULT_BOT_DIR="$PROJECT_ROOT/data/sf-cli/main/default/bots/${BOT_NAME}"
if [ -d "$DEFAULT_BOT_DIR" ]; then
    cp -r "$DEFAULT_BOT_DIR"/*.bot-meta.xml "$STEP1_DIR/xml/bots/" 2>/dev/null || true
    cp -r "$DEFAULT_BOT_DIR"/*.botVersion-meta.xml "$STEP1_DIR/xml/bots/" 2>/dev/null || true
    log "  ✓ Bot XML files copied to step1/xml/bots/"
fi

# Copy ML domain XML files to step1/xml/mlDomains/
DEFAULT_ML_DIR="$PROJECT_ROOT/data/sf-cli/main/default/mlDomains"
if [ -d "$DEFAULT_ML_DIR" ] && [ "$(ls -A $DEFAULT_ML_DIR 2>/dev/null)" ]; then
    cp -r "$DEFAULT_ML_DIR"/*.mlDomain-meta.xml "$STEP1_DIR/xml/mlDomains/" 2>/dev/null || true
    log "  ✓ ML domain XML files copied to step1/xml/mlDomains/"
fi

log ""

# Step 1.6: Convert bot XML to JSON
log "Step 1.6: Converting bot XML to JSON..."
log ""

if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "1" ]; then
    python3 "$SCRIPT_DIR/convert_bot_xml_to_json.py" "${BOT_NAME}" "${STEP1_DIR}"
else
    python3 "$SCRIPT_DIR/convert_bot_xml_to_json.py" "${BOT_NAME}" "${STEP1_DIR}" >/dev/null 2>&1
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error: Failed to convert bot XML to JSON"
    exit 1
fi

log ""

# Step 1.6.1: Convert ML domain XML to JSON FIRST (before extraction needs it)
if [ "$ML_DOMAIN_RETRIEVED" = true ]; then
    log "Step 1.6.1: Converting ML domain XML to JSON..."
    log ""

    ML_DOMAIN_CONVERTED=false

    # Convert all retrieved ML domain XML files in step1 folder
    for ML_XML_FILE in "$STEP1_DIR/xml/mlDomains"/*.mlDomain-meta.xml; do
        if [ -f "$ML_XML_FILE" ]; then
            log "  Converting: $(basename "$ML_XML_FILE")"

            if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "1" ]; then
                python3 "$SCRIPT_DIR/convert_ml_domain.py" "$ML_XML_FILE"
            else
                python3 "$SCRIPT_DIR/convert_ml_domain.py" "$ML_XML_FILE" >/dev/null 2>&1
            fi

            if [ $? -eq 0 ]; then
                log "    ✓ Converted successfully"
                # Move JSON from xml/mlDomains to json folder
                JSON_FILE="${ML_XML_FILE%.mlDomain-meta.xml}.json"
                if [ -f "$JSON_FILE" ]; then
                    mv "$JSON_FILE" "$STEP1_DIR/json/"
                    log "    ✓ Moved to json/"
                fi
                ML_DOMAIN_CONVERTED=true
            else
                log "    ⚠️  Conversion failed"
            fi
        fi
    done

    if [ "$ML_DOMAIN_CONVERTED" = false ]; then
        log ""
        log "  ⚠️  No ML domain XML files found or all conversions failed"
    fi
else
    log "Step 1.6.1: Skipped (ML domain not retrieved)"
    ML_DOMAIN_CONVERTED=false
fi

log ""

# Step 1.6.2: Extract bot data (now IntentSets.json is available if needed)
log "Step 1.6.2: Extracting bot metadata to JSON..."
log ""

if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "1" ]; then
    python3 "$SCRIPT_DIR/extract_bot_metadata.py" "${BOT_NAME}" --step1-dir "${STEP1_DIR}"
else
    python3 "$SCRIPT_DIR/extract_bot_metadata.py" "${BOT_NAME}" --step1-dir "${STEP1_DIR}" >/dev/null 2>&1
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error: Failed to extract bot metadata"
    exit 1
fi

log ""

# Step 1.7: Fetch and parse Apex invocations from org (replaces inference logic)
log "Step 1.7: Fetching real Apex class signatures from org..."
log ""

# Temporary file before Apex parsing (in step1/json)
TEMP_BOT_FILE="${STEP1_DIR}/json/${BOT_NAME}.json"

# Check if bot JSON exists
if [ ! -f "$TEMP_BOT_FILE" ]; then
    echo "❌ Error: Bot JSON not found at $TEMP_BOT_FILE"
    exit 1
fi

# Run fetch and parse invocations script
APEX_OUTPUT_DIR="${STEP1_DIR}/apex-invocations"

if [ "$VERBOSE" = "true" ] || [ "$VERBOSE" = "1" ]; then
    bash "$SCRIPT_DIR/fetch_and_parse_invocations.sh" \
        "$TEMP_BOT_FILE" \
        "$ORG" \
        "$APEX_OUTPUT_DIR"
    APEX_EXIT_CODE=$?
else
    bash "$SCRIPT_DIR/fetch_and_parse_invocations.sh" \
        "$TEMP_BOT_FILE" \
        "$ORG" \
        "$APEX_OUTPUT_DIR" \
        --quiet
    APEX_EXIT_CODE=$?
fi

if [ $APEX_EXIT_CODE -ne 0 ]; then
    log ""
    log "⚠️  Warning: Failed to fetch Apex invocations from org"
    log "    Continuing with inferred types (may be incorrect)"
    log ""
    # Move temp file to final location without Apex updates
    mv "$TEMP_BOT_FILE" "$FINAL_OUTPUT_FILE"
else
    # Replace the temp file with the updated one, then move to final location
    UPDATED_BOT_FILE="${TEMP_BOT_FILE%.json}_with_parsed_invocations.json"
    if [ -f "$UPDATED_BOT_FILE" ]; then
        mv "$UPDATED_BOT_FILE" "$FINAL_OUTPUT_FILE"
        log "✅ Bot JSON updated with real Apex signatures and moved to root"
    else
        # If no update file, move original
        mv "$TEMP_BOT_FILE" "$FINAL_OUTPUT_FILE"
    fi
fi

# Clean up temporary JSON file in step1/json if it still exists
if [ -f "$TEMP_BOT_FILE" ]; then
    rm "$TEMP_BOT_FILE"
    log "  🗑️  Cleaned up temporary file: step1/json/${BOT_NAME}.json"
fi

log ""

# Step 1.11: Removed (merge_ml_data.py is obsolete)
# extract_bot_metadata.py now handles ML intent extraction correctly by parsing
# relatedMlIntents and extracting ONLY the referenced intents from Intent Sets.

# Check final file exists at root of bot version directory
if [ ! -f "$FINAL_OUTPUT_FILE" ]; then
    echo "Error: Final bot JSON not found at $FINAL_OUTPUT_FILE"
    exit 1
fi

# Save pipeline state for session resumption
STATE_FILE="$PROJECT_ROOT/.claude/pipeline-state.json"
mkdir -p "$(dirname "$STATE_FILE")"
cat > "$STATE_FILE" <<EOF
{
  "currentStep": 1,
  "botName": "${BOT_NAME}",
  "botVersion": "v${BOT_VERSION}",
  "orgId": "${ORG_ID}",
  "orgAlias": "${ORG:-default}",
  "botJsonPath": "${FINAL_OUTPUT_FILE}",
  "lastUpdated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")"
}
EOF

log "  💾 Saved pipeline state to .claude/pipeline-state.json"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅  STEP 1 COMPLETE"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Bot metadata successfully retrieved and saved."
echo ""
echo "Final JSON location:"
echo "  data/bots/${ORG_ID_LOWER}/${BOT_NAME_LOWER}/v${BOT_VERSION}/${BOT_NAME}.json"
echo ""
echo "Next Step:"
echo "  /02-process-and-build-inventory"
echo ""
echo "This will parse the bot metadata and show you a complete"
echo "inventory of dialogs, intents, actions, and variables."
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
