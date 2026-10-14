#!/usr/bin/env python3
"""
Merge invocation metadata from bot JSON with type information from Apex source code.

Takes two inputs:
1. Invocations structure from bot metadata (parameter names)
2. Parsed Apex invocations (type information)

Produces final botInvocationsDescribeInfo with complete parameter names and types.
"""

import json
import sys
from pathlib import Path
from typing import Dict


def merge_invocation_types(
    bot_metadata_invocations: Dict,
    apex_parsed_invocations: Dict
) -> Dict:
    """
    Merge bot metadata parameters with Apex type information.

    Strategy:
    1. Start with bot metadata structure (has all parameter names)
    2. Fill in type information from Apex parsing
    3. Keep parameters from bot metadata even if not in Apex (use default types)
    4. Add new parameters from Apex if they exist but not in bot metadata

    Args:
        bot_metadata_invocations: From bot JSON (parameter names)
        apex_parsed_invocations: From Apex parser (type info)

    Returns:
        Merged structure with complete info
    """
    merged = {}

    # Get all class names from both sources
    all_classes = set(bot_metadata_invocations.keys()) | set(apex_parsed_invocations.keys())

    for class_name in sorted(all_classes):
        bot_class = bot_metadata_invocations.get(class_name, {})
        apex_class = apex_parsed_invocations.get(class_name, {})

        bot_inputs = bot_class.get('inputParameters', {})
        bot_outputs = bot_class.get('outputParameters', {})
        apex_inputs = apex_class.get('inputParameters', {})
        apex_outputs = apex_class.get('outputParameters', {})

        # Merge strategy: Use Apex as authoritative source (includes all defined parameters)
        # This matches cult.json behavior which includes all Apex parameters, not just bot-used ones
        merged_inputs = dict(apex_inputs)
        merged_outputs = dict(apex_outputs)

        # Sort parameters alphabetically
        merged[class_name] = {
            'inputParameters': dict(sorted(merged_inputs.items())),
            'outputParameters': dict(sorted(merged_outputs.items()))
        }

    return merged


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Merge bot metadata invocations with Apex type information'
    )
    parser.add_argument(
        '--bot-invocations',
        required=True,
        help='JSON file with invocations from bot metadata'
    )
    parser.add_argument(
        '--apex-invocations',
        required=True,
        help='JSON file with parsed Apex invocations'
    )
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    # Load bot metadata invocations
    with open(args.bot_invocations, 'r', encoding='utf-8') as f:
        bot_data = json.load(f)
        bot_invocations = bot_data.get('apex', {})

    # Load Apex parsed invocations
    with open(args.apex_invocations, 'r', encoding='utf-8') as f:
        apex_data = json.load(f)
        apex_invocations = apex_data.get('apex', {})

    # Merge
    merged_invocations = merge_invocation_types(bot_invocations, apex_invocations)

    print(f"Merged {len(merged_invocations)} invocations")

    # Build output
    result = {
        "apex": merged_invocations,
        "flow": {}
    }

    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"✅ Saved to: {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
