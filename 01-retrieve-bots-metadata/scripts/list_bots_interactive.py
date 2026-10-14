#!/usr/bin/env python3
"""
Interactive bot selector - lists all bots with versions and prompts user to select one
"""

import json
import subprocess
import sys
from typing import List, Dict, Optional, Tuple


def run_sf_command(query: str, org: Optional[str] = None) -> List[Dict]:
    """Run sf data query and return results as list of dicts"""
    cmd = [
        "sf", "data", "query",
        "--query", query,
        "--result-format", "json"
    ]

    if org:
        cmd.extend(["--target-org", org])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return data.get("result", {}).get("records", [])
    except subprocess.CalledProcessError as e:
        print(f"Error querying Salesforce: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}", file=sys.stderr)
        sys.exit(1)


def list_bots(org: Optional[str] = None) -> List[Dict]:
    """Query all bot versions from org (Einstein Bots only, excludes Agentforce Agents)"""
    query = """
    SELECT
        BotDefinition.DeveloperName,
        BotDefinition.MasterLabel,
        BotDefinition.Description,
        VersionNumber,
        LastModifiedDate,
        Status
    FROM BotVersion
    WHERE BotDefinition.Type = 'Bot'
    ORDER BY BotDefinition.MasterLabel, VersionNumber DESC
    """

    return run_sf_command(query, org)


def group_by_bot(versions: List[Dict]) -> Dict[str, List[Dict]]:
    """Group versions by bot developer name"""
    grouped = {}
    for version in versions:
        bot_name = version["BotDefinition"]["DeveloperName"]
        if bot_name not in grouped:
            grouped[bot_name] = []
        grouped[bot_name].append(version)
    return grouped


def display_bot_list(bot_list: List[str], grouped_bots: Dict[str, List[Dict]]) -> None:
    """Display numbered list of bots in table format"""
    print("\n" + "="*120)
    print("Available Bots")
    print("="*120)

    # Table header - Only Bot Name and Description
    print(f"\n{'#':<5} {'Bot Name':<35} {'Description':<80}")
    print("-" * 120)

    for i, dev_name in enumerate(bot_list, 1):
        versions = grouped_bots[dev_name]

        # Get bot master label (display name) and description
        bot_label = versions[0]["BotDefinition"].get("MasterLabel", dev_name)
        bot_desc = versions[0]["BotDefinition"].get("Description", "N/A")
        if len(bot_desc) > 80:
            bot_desc = bot_desc[:77] + "..."

        print(f"[{i}]{' ':<3} {bot_label:<35} {bot_desc:<80}")

    print("-" * 120)
    print(f"[0]    Cancel / Exit")
    print("=" * 120)


def display_bot_details(bot_name: str, versions: List[Dict]) -> None:
    """Display detailed version information for a selected bot"""
    # Get master label for display
    bot_label = versions[0]["BotDefinition"].get("MasterLabel", bot_name)

    print("\n" + "="*80)
    print(f"Bot Details: {bot_label}")
    print("="*80)

    # Bot description
    bot_desc = versions[0]["BotDefinition"].get("Description", "N/A")
    print(f"\nDescription: {bot_desc}")

    # Sort versions alphabetically by version number
    sorted_versions = sorted(versions, key=lambda v: v["VersionNumber"])

    # Version details
    print(f"\n{'#':<5} {'Version':<10} {'Status':<12} {'Last Modified':<20}")
    print("-" * 50)

    for i, version in enumerate(sorted_versions, 1):
        ver_num = version["VersionNumber"]
        status = version.get("Status", "Unknown")
        last_modified = version["LastModifiedDate"][:10] if version.get("LastModifiedDate") else "N/A"
        print(f"[{i}]{' ':<3} v{ver_num:<9} {status:<12} {last_modified:<20}")


def get_user_choice(prompt: str, max_choice: int) -> int:
    """Get numeric choice from user"""
    while True:
        try:
            choice_str = input(prompt).strip()
            choice = int(choice_str)
            if 0 <= choice <= max_choice:
                return choice
            else:
                print(f"Please enter a number between 0 and {max_choice}")
        except ValueError:
            print("Please enter a valid number")
        except (KeyboardInterrupt, EOFError):
            print("\n")
            return 0


def confirm_selection(bot_label: str, bot_dev_name: str, version: int) -> bool:
    """Confirm bot and version selection"""
    print()
    while True:
        response = input(f"Fetch {bot_label} v{version}? [y/n]: ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        elif response == '':
            continue
        else:
            print("Please enter 'y' or 'n'")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 list_bots_interactive.py <ORG_ALIAS>", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print("  python3 list_bots_interactive.py my-org", file=sys.stderr)
        sys.exit(1)

    org = sys.argv[1]

    print(f"\nQuerying bots from org: {org}...")

    # Fetch bot versions
    versions = list_bots(org)

    if not versions:
        print("\nNo bots found in org.", file=sys.stderr)
        sys.exit(1)

    # Group by bot
    grouped_bots = group_by_bot(versions)

    # Interactive selection
    bot_list = sorted(grouped_bots.keys())

    print(f"\nFound {len(bot_list)} bot(s) with {sum(len(v) for v in grouped_bots.values())} version(s)")

    while True:
        # Display bot list
        display_bot_list(bot_list, grouped_bots)

        # Get user selection
        choice = get_user_choice("\nEnter bot number (0 to cancel): ", len(bot_list))

        if choice == 0:
            print("\n✗ Selection cancelled")
            sys.exit(0)

        # Get selected bot
        selected_bot = bot_list[choice - 1]
        versions = grouped_bots[selected_bot]

        # Version selection loop
        while True:
            # Display bot details
            display_bot_details(selected_bot, versions)

            # Sort versions alphabetically for consistent indexing
            sorted_versions = sorted(versions, key=lambda v: v["VersionNumber"])

            # Get version selection
            version_choice = get_user_choice("\nEnter version number (0 to go back): ", len(sorted_versions))

            if version_choice == 0:
                print("\n↩ Going back to bot list...")
                break

            # Get selected version
            selected_version = sorted_versions[version_choice - 1]
            selected_version_num = selected_version["VersionNumber"]

            # Get bot label for display
            bot_label = versions[0]["BotDefinition"].get("MasterLabel", selected_bot)

            # Confirm selection
            if confirm_selection(bot_label, selected_bot, selected_version_num):
                # Output selected bot name (DeveloperName) and version to stdout for shell script to capture
                print(f"\n✓ Bot selected: {bot_label} v{selected_version_num}")
                print(f"SELECTED_BOT={selected_bot}")
                print(f"SELECTED_VERSION={selected_version_num}")
                sys.exit(0)
            # If not confirmed, loop back to version list


if __name__ == "__main__":
    main()
