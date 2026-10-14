#!/usr/bin/env python3
"""
Extract invocation parameter names from bot metadata.
This provides the baseline structure with all parameter names,
which will be enriched with type information from Apex source code.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


def extract_invocations_from_metadata(bot_data: Dict) -> Dict[str, Dict]:
    """
    Extract invocation parameter names from bot metadata.

    Returns:
        {
            "ClassNameA": {
                "inputParameters": {"param1": {}, "param2": {}},
                "outputParameters": {"result": {}}
            },
            ...
        }
    """
    invocations = {}

    def process_object(obj: Any):
        if isinstance(obj, dict):
            # Check if this is an invocation
            if 'invocationActionName' in obj and obj.get('invocationActionType') == 'apex':
                action_name = obj['invocationActionName']

                if action_name not in invocations:
                    invocations[action_name] = {
                        'inputParameters': {},
                        'outputParameters': {}
                    }

                # Extract parameter mappings
                mappings = obj.get('invocationMappings', [])
                if isinstance(mappings, list):
                    for mapping in mappings:
                        param_name = mapping.get('parameterName')
                        mapping_type = mapping.get('type')  # 'Input' or 'Output'

                        if param_name:
                            # Initialize with empty dict - types will be filled by Apex parser
                            if mapping_type == 'Input':
                                invocations[action_name]['inputParameters'][param_name] = {}
                            elif mapping_type == 'Output':
                                invocations[action_name]['outputParameters'][param_name] = {}

            # Recurse into nested objects
            for value in obj.values():
                process_object(value)
        elif isinstance(obj, list):
            for item in obj:
                process_object(item)

    process_object(bot_data)

    # Sort alphabetically
    sorted_invocations = {}
    for class_name in sorted(invocations.keys()):
        class_data = invocations[class_name]
        sorted_invocations[class_name] = {
            'inputParameters': dict(sorted(class_data['inputParameters'].items())),
            'outputParameters': dict(sorted(class_data['outputParameters'].items()))
        }

    return sorted_invocations


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract invocation parameter names from bot metadata'
    )
    parser.add_argument('bot_json', help='Path to bot JSON file')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    # Load bot JSON
    bot_json_path = Path(args.bot_json)
    if not bot_json_path.exists():
        print(f"Error: Bot JSON not found: {bot_json_path}", file=sys.stderr)
        sys.exit(1)

    with open(bot_json_path, 'r', encoding='utf-8') as f:
        bot_data = json.load(f)

    # Extract invocations
    invocations = extract_invocations_from_metadata(bot_data)

    print(f"Extracted {len(invocations)} invocations from bot metadata")

    # Build output structure
    result = {
        "apex": invocations,
        "flow": {}
    }

    # Output
    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Saved to: {output_file}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
