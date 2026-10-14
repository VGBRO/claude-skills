#!/usr/bin/env python3
"""
Generic script to extract bot metadata from Salesforce metadata files.
Works with ANY bot - no hardcoded values.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List, Set, Optional, Tuple
from constants import DIR_XML, DIR_JSON, DIR_ML_DOMAINS, SF_CLI_RETRIEVE_ML_DOMAIN
from utils import load_json_file, save_json_file, recursive_process


def normalize_retry_messages(obj: Any) -> Any:
    """
    Normalize all retryMessages fields to always be arrays of objects.

    Einstein Bot metadata has inconsistent retryMessages structure:
    - Sometimes: {"message": "...", "messageIdentifier": "..."}  (single object)
    - Sometimes: [{"message": "...", "messageIdentifier": "..."}, ...]  (array)

    This function ensures all retryMessages are arrays for consistency.
    """
    if isinstance(obj, dict):
        # Check if this dict has retryMessages key
        if 'retryMessages' in obj:
            retry = obj['retryMessages']
            # If it's a dict (single object), wrap it in an array
            if isinstance(retry, dict):
                obj['retryMessages'] = [retry]
            # If it's already a list, leave it as-is
            elif isinstance(retry, list):
                pass
            # If it's None or other type, convert to empty array
            elif retry is None:
                obj['retryMessages'] = []

        # Recurse into all values
        for key, value in obj.items():
            obj[key] = normalize_retry_messages(value)

    elif isinstance(obj, list):
        # Recurse into all list items
        return [normalize_retry_messages(item) for item in obj]

    return obj



def parse_related_ml_intents(bot_meta: Dict) -> Dict[str, List[str]]:
    """
    Parse relatedMlIntents from bot metadata.

    Each bot dialog with mlIntentTrainingEnabled can reference an external Intent Set.
    Format: "relatedMlIntents": {"relatedMlIntent": "IntentSetName.IntentName"}

    Returns: {
        "IntentSetName": ["IntentName1", "IntentName2", ...],
        ...
    }

    Example:
        "relatedMlIntents": {"relatedMlIntent": "MyMLDomain.MyIntent"}

    Returns:
        {"MyMLDomain": ["MyIntent"]}
    """
    from collections import defaultdict

    intent_set_map = defaultdict(list)

    bot_ml_domain = bot_meta.get("Bot", {}).get("botMlDomain", {})
    ml_intents = bot_ml_domain.get("mlIntents", [])

    for intent in ml_intents:
        if not isinstance(intent, dict):
            continue

        related_ml = intent.get("relatedMlIntents")

        # Handle both array and dict formats
        if isinstance(related_ml, list):
            # Array format: [{"relatedMlIntent": "IntentSetName.IntentName"}]
            for item in related_ml:
                if isinstance(item, dict):
                    related_intent = item.get("relatedMlIntent", "")
                    if related_intent and '.' in related_intent:
                        intent_set_name, intent_name = related_intent.split('.', 1)
                        intent_set_map[intent_set_name].append(intent_name)
        elif isinstance(related_ml, dict):
            # Dict format: {"relatedMlIntent": "IntentSetName.IntentName"}
            related_intent = related_ml.get("relatedMlIntent", "")
            if related_intent and '.' in related_intent:
                intent_set_name, intent_name = related_intent.split('.', 1)
                intent_set_map[intent_set_name].append(intent_name)

    return dict(intent_set_map)


def load_intent_set_json(intent_set_name: str, step1_dir: Path = None) -> Optional[Dict]:
    """Load Intent Set JSON file. Returns None if not found."""
    # Try step1 folder first if step1_dir provided
    if step1_dir:
        # Check json folder first
        ml_domain_file = step1_dir / "json" / f"{intent_set_name}.json"
        if ml_domain_file.exists():
            try:
                with open(ml_domain_file) as f:
                    return json.load(f)
            except Exception:
                pass

        # Then check xml/mlDomains folder
        ml_domain_file = step1_dir / "xml" / "mlDomains" / f"{intent_set_name}.json"
        if ml_domain_file.exists():
            try:
                with open(ml_domain_file) as f:
                    return json.load(f)
            except Exception:
                pass

    # Fallback to default location
    ml_domain_file = Path(f"data/sf-cli/main/default/mlDomains/{intent_set_name}.json")

    if not ml_domain_file.exists():
        return None

    try:
        with open(ml_domain_file) as f:
            return json.load(f)
    except Exception:
        return None


def extract_specific_intents_from_set(intent_set_data: Dict, intent_names: List[str]) -> List[Dict]:
    """
    Extract ONLY specific intents from an Intent Set.
    Does not extract all intents - only the ones referenced by the bot.
    """
    all_intents = intent_set_data.get("mlIntents", [])

    # Create map for quick lookup
    intent_map = {
        intent["developerName"]: intent
        for intent in all_intents
    }

    # Extract only requested intents
    extracted_intents = []
    for intent_name in intent_names:
        if intent_name in intent_map:
            extracted_intents.append(intent_map[intent_name])

    return extracted_intents


def extract_ml_data_from_bot_meta_generic(bot_meta: Dict) -> Dict[str, Any]:
    """Extract ML domain and intent data generically from bot metadata."""
    print("    Extracting ML data from bot metadata...")

    bot_ml_domain = bot_meta.get("Bot", {}).get("botMlDomain", {})

    if not bot_ml_domain:
        return {"c": {}}

    domain_label = bot_ml_domain.get("label", "MlDomain")
    domain_name = bot_ml_domain.get("name", domain_label.replace(" ", ""))
    ml_intents_raw = bot_ml_domain.get("mlIntents", [])

    # Convert to standard bot JSON format
    ml_intents = []
    for intent in ml_intents_raw:
        if not isinstance(intent, dict):
            continue

        ml_intent_utterances = []
        utterances = intent.get("mlIntentUtterances", [])

        for utterance in utterances:
            if isinstance(utterance, dict):
                ml_intent_utterances.append({
                    "utterance": utterance.get("utterance", "")
                })

        ml_intents.append({
            "developerName": intent.get("developerName", ""),
            "label": intent.get("label", ""),
            "mlIntentUtterances": ml_intent_utterances
        })

    print(f"      Found {len(ml_intents)} intents")

    # Use domain name as key
    return {
        "c": {
            domain_name: {
                "MlDomain": {
                    "fullName": domain_name,
                    "label": domain_label,
                    "mlIntents": ml_intents
                }
            }
        }
    }


def get_empty_agent_actions() -> Dict[str, Any]:
    """
    Return empty agent actions structure.
    """
    return {
        "customActions": [],
        "standardActions": []
    }


def simplify_context_variables_generic(context_vars: List[Dict]) -> List[Dict]:
    """Simplify context variables to bot JSON format (only core fields)."""
    simplified = []
    for var in context_vars:
        if not isinstance(var, dict):
            continue

        simplified.append({
            "dataType": var.get("dataType"),
            "developerName": var.get("developerName"),
            "label": var.get("label")
        })
    return simplified


def rebuild_bot_json_generic(
    bot_meta: Dict,
    bot_version: Dict,
    bot_name: str
) -> Dict[str, Any]:
    """Rebuild bot JSON format from metadata files generically."""
    print("\n  Rebuilding bot JSON format from metadata...\n")

    bot_data = bot_meta.get("Bot", {})
    bot_version_data = bot_version.get("BotVersion", {})

    # Use bot_name as fullName (not botVersion.fullName which is just "v1")
    full_name = bot_name

    # Extract Bot structure
    bot_data = {
        "fullName": full_name,
        "botMlDomain": bot_data.get("botMlDomain", {}),
        "contextVariables": simplify_context_variables_generic(
            bot_data.get("contextVariables", [])
        ),
        "description": bot_data.get("description", ""),
        "label": bot_data.get("label", ""),
        "botVersions": [bot_version_data]
    }

    # NOTE: Invocations are now fetched from org using fetch_and_parse_invocations.sh
    # This provides REAL type information from Apex source code instead of inference.
    # The botInvocationsDescribeInfo will be populated by the pipeline after this script runs.

    # Extract ML data generically
    ml_data = extract_ml_data_from_bot_meta_generic(bot_meta)

    # Get agent actions (from existing bot JSON if available)
    agent_actions = get_empty_agent_actions()

    # Combine
    result = {
        "Bot": bot_data,
        "availableAgentActions": agent_actions,
        "botInvocationsDescribeInfo": {
            "apex": {},  # Will be populated by fetch_and_parse_invocations.sh
            "flow": {}
        },
        "mlRelatedData": ml_data
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Extract bot JSON from metadata files (generic, works with any bot)"
    )
    parser.add_argument("bot_name", help="Bot developer name")
    parser.add_argument("--output", "-o", help="Output file path for final JSON (defaults to step1/json/<bot_name>.json)")
    parser.add_argument("--step1-dir", help="Step1 directory path (default: data/sf-cli/main/default/bots/{bot_name})")

    args = parser.parse_args()

    bot_name = args.bot_name

    if args.step1_dir:
        step1_dir = Path(args.step1_dir)
    else:
        step1_dir = Path(f"data/sf-cli/main/default/bots/{bot_name}")

    print("="*80)
    print(f"Extracting Bot JSON from Metadata (Generic): {bot_name}")
    print("="*80)

    # Load metadata files from json directory
    print("\n  Loading metadata files...")
    json_dir = step1_dir / "json"
    bot_meta_file = json_dir / f"{bot_name}.bot-meta.json"

    if not bot_meta_file.exists():
        print(f"Error: {bot_meta_file} not found", file=sys.stderr)
        sys.exit(1)

    bot_meta = load_json_file(bot_meta_file)

    # Find botVersion file in json directory
    version_files = list(json_dir.glob("*.botVersion-meta.json"))
    if not version_files:
        print(f"Error: No botVersion-meta.json found in {json_dir}", file=sys.stderr)
        sys.exit(1)

    bot_version = load_json_file(version_files[0])
    print(f"    ✓ Loaded {bot_meta_file.name}")
    print(f"    ✓ Loaded {version_files[0].name}")

    # Rebuild
    print("\n  Extracting and combining data...")
    rebuilt = rebuild_bot_json_generic(bot_meta, bot_version, bot_name)

    # Normalize retryMessages to always be arrays
    print("\n  Normalizing retryMessages structure...")
    rebuilt = normalize_retry_messages(rebuilt)
    print("    ✓ All retryMessages normalized to arrays")

    # Create json subdirectory if it doesn't exist
    json_dir.mkdir(parents=True, exist_ok=True)

    # Save initial version (temporary)
    temp_file = step1_dir / "generated_temp.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(rebuilt, f, indent=2, ensure_ascii=False)

    print(f"\n    ✓ Saved temporary file to {temp_file}")

    # Extract and merge related ML intents from Intent Sets
    print("\n  Extracting related ML intents from Intent Sets...")
    intent_set_map = parse_related_ml_intents(bot_meta)

    if intent_set_map:
        print(f"    ✓ Found references to {len(intent_set_map)} Intent Set(s):")
        for intent_set_name, intent_names in intent_set_map.items():
            print(f"        - {intent_set_name}: {len(intent_names)} intent(s) - {', '.join(intent_names)}")

        # Build mlRelatedData with only the referenced intents
        ml_related_data = {"c": {}}
        total_intents = 0
        total_utterances = 0
        missing_sets = []

        for intent_set_name, intent_names in intent_set_map.items():
            intent_set_data = load_intent_set_json(intent_set_name, step1_dir)

            if intent_set_data:
                # Extract ONLY the referenced intents
                extracted_intents = extract_specific_intents_from_set(intent_set_data, intent_names)

                if extracted_intents:
                    utterance_count = sum(
                        len(intent.get("mlIntentUtterances", []))
                        for intent in extracted_intents
                    )

                    ml_related_data["c"][intent_set_name] = {
                        "MlDomain": {
                            "fullName": intent_set_data.get("fullName", intent_set_name),
                            "label": intent_set_data.get("label", intent_set_name),
                            "mlIntents": extracted_intents
                        }
                    }

                    total_intents += len(extracted_intents)
                    total_utterances += utterance_count
                    print(f"        ✓ Extracted {len(extracted_intents)} intent(s) with {utterance_count} utterances from {intent_set_name}")
            else:
                missing_sets.append(intent_set_name)

        if ml_related_data["c"]:
            # Replace mlRelatedData with the extracted intents
            rebuilt["mlRelatedData"] = ml_related_data

            # Determine output file location
            if args.output:
                output_file = Path(args.output)
            else:
                output_file = json_dir / f"{bot_name}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rebuilt, f, indent=2, ensure_ascii=False)

            print(f"\n    ✓ Final version saved to: {output_file}")
            print(f"    🎉 Extracted {total_intents} intent(s) with {total_utterances} utterances")

            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
                print(f"    ✓ Cleaned up temporary file: {temp_file}")
        else:
            # No ML related data, save with determined output location
            if args.output:
                output_file = Path(args.output)
            else:
                output_file = json_dir / f"{bot_name}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rebuilt, f, indent=2, ensure_ascii=False)

            print(f"\n    ✓ Saved to: {output_file}")

            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
                print(f"  ✓ Cleaned up temporary file: {temp_file}")

        if missing_sets:
            print(f"\n  ⚠  Missing Intent Set(s): {', '.join(missing_sets)}")
            for missing_set in missing_sets:
                print(f"  💡 Run: sf project retrieve start --metadata MlDomain:{missing_set}")
                print(f"  💡 Then: python3 scripts/custom/convert_intentsets_xml.py")
    else:
        print(f"  ℹ  No relatedMlIntents found - using bot's internal ML domain only")

        # Determine output file location
        if args.output:
            output_file = Path(args.output)
        else:
            output_file = json_dir / f"{bot_name}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rebuilt, f, indent=2, ensure_ascii=False)

        print(f"\n  ✓ Saved to: {output_file}")

        # Clean up temporary file
        if temp_file.exists():
            temp_file.unlink()
            print(f"  ✓ Cleaned up temporary file: {temp_file}")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
