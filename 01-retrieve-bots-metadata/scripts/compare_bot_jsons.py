#!/usr/bin/env python3
"""
Compare two bot JSON files and identify structural and content differences.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from utils import load_json_file


def get_keys_recursive(data: Any, prefix: str = "") -> Set[str]:
    """Recursively get all keys in a nested structure."""
    keys = set()

    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            keys.update(get_keys_recursive(value, full_key))
    elif isinstance(data, list) and data:
        # For arrays, analyze first element structure
        keys.add(f"{prefix}[]")
        if data:
            keys.update(get_keys_recursive(data[0], f"{prefix}[]"))

    return keys


def compare_structure(ref: Dict, gen: Dict) -> Tuple[Set[str], Set[str]]:
    """Compare structure of two JSONs."""
    ref_keys = get_keys_recursive(ref)
    gen_keys = get_keys_recursive(gen)

    missing_in_gen = ref_keys - gen_keys
    extra_in_gen = gen_keys - ref_keys

    return missing_in_gen, extra_in_gen


def count_items(data: Any, path: str = "") -> Dict[str, int]:
    """Count items at various paths."""
    counts = {}

    if isinstance(data, dict):
        for key, value in data.items():
            full_path = f"{path}.{key}" if path else key
            if isinstance(value, list):
                counts[full_path] = len(value)
            elif isinstance(value, dict):
                counts.update(count_items(value, full_path))

    return counts


def compare_values(ref: Dict, gen: Dict, path: str = "") -> List[str]:
    """Compare values at same paths."""
    differences = []

    if isinstance(ref, dict) and isinstance(gen, dict):
        all_keys = set(ref.keys()) | set(gen.keys())

        for key in all_keys:
            full_path = f"{path}.{key}" if path else key

            if key not in ref:
                continue  # Already captured in structure diff
            elif key not in gen:
                continue  # Already captured in structure diff
            else:
                ref_val = ref[key]
                gen_val = gen[key]

                # Compare types
                if type(ref_val) != type(gen_val):
                    differences.append(
                        f"{full_path}: TYPE MISMATCH - "
                        f"Reference={type(ref_val).__name__}, Generated={type(gen_val).__name__}"
                    )
                # Compare scalar values
                elif isinstance(ref_val, (str, int, float, bool, type(None))):
                    if ref_val != gen_val:
                        differences.append(
                            f"{full_path}: VALUE MISMATCH - "
                            f"Reference={ref_val}, Generated={gen_val}"
                        )
                # Compare array lengths
                elif isinstance(ref_val, list):
                    if len(ref_val) != len(gen_val):
                        differences.append(
                            f"{full_path}: LENGTH MISMATCH - "
                            f"Reference={len(ref_val)} items, Generated={len(gen_val)} items"
                        )
                    # Recursively compare first element if exists
                    if ref_val and gen_val:
                        differences.extend(compare_values(ref_val[0], gen_val[0], f"{full_path}[0]"))
                # Recurse into dicts
                elif isinstance(ref_val, dict):
                    differences.extend(compare_values(ref_val, gen_val, full_path))

    return differences


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 compare_bot_jsons.py <reference.json> <generated.json>")
        sys.exit(1)

    ref_file = sys.argv[1]
    gen_file = sys.argv[2]

    print("=" * 80)
    print("Bot JSON Comparison Report")
    print("=" * 80)
    print(f"\nReference: {ref_file}")
    print(f"Generated: {gen_file}\n")

    # Load files
    ref = load_json(ref_file)
    gen = load_json(gen_file)

    # Compare structure
    print("=" * 80)
    print("STRUCTURE COMPARISON")
    print("=" * 80)

    missing, extra = compare_structure(ref, gen)

    if missing:
        print(f"\n❌ MISSING in Generated ({len(missing)} keys):")
        for key in sorted(missing):
            print(f"  - {key}")
    else:
        print("\n✅ No missing keys")

    if extra:
        print(f"\n⚠️  EXTRA in Generated ({len(extra)} keys):")
        for key in sorted(extra):
            print(f"  + {key}")
    else:
        print("\n✅ No extra keys")

    # Count items
    print("\n" + "=" * 80)
    print("ITEM COUNTS COMPARISON")
    print("=" * 80)

    ref_counts = count_items(ref)
    gen_counts = count_items(gen)

    all_paths = sorted(set(ref_counts.keys()) | set(gen_counts.keys()))

    print(f"\n{'Path':<60} {'Reference':<15} {'Generated':<15} {'Status'}")
    print("-" * 110)

    for path in all_paths:
        ref_count = ref_counts.get(path, 0)
        gen_count = gen_counts.get(path, 0)

        if ref_count != gen_count:
            status = "❌ MISMATCH"
        else:
            status = "✅"

        print(f"{path:<60} {ref_count:<15} {gen_count:<15} {status}")

    # Compare values
    print("\n" + "=" * 80)
    print("VALUE COMPARISON")
    print("=" * 80)

    differences = compare_values(ref, gen)

    if differences:
        print(f"\n❌ VALUE MISMATCHES ({len(differences)}):\n")
        for diff in differences[:50]:  # Show first 50
            print(f"  {diff}")

        if len(differences) > 50:
            print(f"\n  ... and {len(differences) - 50} more differences")
    else:
        print("\n✅ All values match")

    # Specific checks
    print("\n" + "=" * 80)
    print("SPECIFIC CHECKS")
    print("=" * 80)

    # Check Bot.fullName
    ref_fullname = ref.get("Bot", {}).get("fullName")
    gen_fullname = gen.get("Bot", {}).get("fullName")
    print(f"\nBot.fullName:")
    print(f"  Reference: {ref_fullname}")
    print(f"  Generated: {gen_fullname}")
    print(f"  Status: {'✅ Match' if ref_fullname == gen_fullname else '❌ Mismatch'}")

    # Check mlSlotClasses
    ref_slots = ref.get("Bot", {}).get("mlSlotClasses")
    gen_slots = gen.get("Bot", {}).get("mlSlotClasses")
    print(f"\nBot.mlSlotClasses:")
    print(f"  Reference: {ref_slots}")
    print(f"  Generated: {gen_slots}")
    print(f"  Status: {'✅ Match' if ref_slots == gen_slots else '❌ Mismatch'}")

    # Check botVersions
    ref_versions = ref.get("Bot", {}).get("botVersions", [])
    gen_versions = gen.get("Bot", {}).get("botVersions", [])
    print(f"\nBot.botVersions:")
    print(f"  Reference: {len(ref_versions)} version(s)")
    print(f"  Generated: {len(gen_versions)} version(s)")
    if ref_versions and gen_versions:
        ref_v_keys = set(ref_versions[0].keys())
        gen_v_keys = set(gen_versions[0].keys())
        missing_v_keys = ref_v_keys - gen_v_keys
        extra_v_keys = gen_v_keys - ref_v_keys

        if missing_v_keys:
            print(f"  ❌ Missing keys in generated version: {', '.join(sorted(missing_v_keys))}")
        if extra_v_keys:
            print(f"  ⚠️  Extra keys in generated version: {', '.join(sorted(extra_v_keys))}")
        if not missing_v_keys and not extra_v_keys:
            print(f"  ✅ Version keys match")

    # Check availableAgentActions
    ref_actions = ref.get("availableAgentActions", {})
    gen_actions = gen.get("availableAgentActions", {})
    print(f"\navailableAgentActions:")
    print(f"  Reference customActions: {len(ref_actions.get('customActions', []))}")
    print(f"  Generated customActions: {len(gen_actions.get('customActions', []))}")
    print(f"  Reference standardActions: {len(ref_actions.get('standardActions', []))}")
    print(f"  Generated standardActions: {len(gen_actions.get('standardActions', []))}")

    if ref_actions.get('standardActions') and not gen_actions.get('standardActions'):
        print(f"  ❌ standardActions empty in generated!")

    # Check botInvocationsDescribeInfo
    ref_invocations = ref.get("botInvocationsDescribeInfo", {}).get("apex", {})
    gen_invocations = gen.get("botInvocationsDescribeInfo", {}).get("apex", {})
    print(f"\nbotInvocationsDescribeInfo.apex:")
    print(f"  Reference: {len(ref_invocations)} invocations")
    print(f"  Generated: {len(gen_invocations)} invocations")
    print(f"  Status: {'✅ Match' if len(ref_invocations) == len(gen_invocations) else '❌ Mismatch'}")

    # Check mlRelatedData
    ref_ml = ref.get("mlRelatedData", {}).get("c", {})
    gen_ml = gen.get("mlRelatedData", {}).get("c", {})
    print(f"\nmlRelatedData.c:")
    print(f"  Reference: {list(ref_ml.keys())}")
    print(f"  Generated: {list(gen_ml.keys())}")
    print(f"  Status: {'✅ Match' if set(ref_ml.keys()) == set(gen_ml.keys()) else '❌ Mismatch'}")

    # Check Bot.botMlDomain.mlIntents
    ref_bot_intents = ref.get("Bot", {}).get("botMlDomain", {}).get("mlIntents", [])
    gen_bot_intents = gen.get("Bot", {}).get("botMlDomain", {}).get("mlIntents", [])
    print(f"\nBot.botMlDomain.mlIntents:")
    print(f"  Reference: {len(ref_bot_intents)} intents")
    print(f"  Generated: {len(gen_bot_intents)} intents")
    print(f"  Status: {'✅ Match' if len(ref_bot_intents) == len(gen_bot_intents) else '❌ Mismatch'}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total_issues = len(missing) + len(differences)
    if total_issues == 0:
        print("\n✅ JSONs are structurally identical!")
    else:
        print(f"\n⚠️  Found {total_issues} differences:")
        print(f"   - {len(missing)} missing keys")
        print(f"   - {len(differences)} value mismatches")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
