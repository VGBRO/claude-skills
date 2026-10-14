#!/usr/bin/env python3
"""
Convert Bot XML metadata files to JSON format
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from constants import ALWAYS_ARRAY_FIELDS, BOOLEAN_FIELDS, DIR_XML, DIR_JSON, DIR_BOTS
from utils import extract_tag_name, save_json_file


def xml_to_dict(element):
    """Recursively convert XML element to dictionary"""
    result = {}
    tag_name = extract_tag_name(element)

    # Add text content if present
    if element.text and element.text.strip():
        text = element.text.strip()

        # Convert boolean strings
        if tag_name in BOOLEAN_FIELDS:
            return text.lower() == 'true'

        return text

    # Process child elements
    for child in element:
        child_data = xml_to_dict(child)
        tag = extract_tag_name(child)

        if tag in result:
            # Convert to list if multiple elements with same tag
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(child_data)
        else:
            # Check if this field should always be an array
            if tag in ALWAYS_ARRAY_FIELDS:
                result[tag] = [child_data]
            else:
                result[tag] = child_data

    return result


def convert_bot_xml(xml_file: Path) -> dict:
    """Convert bot XML file to JSON structure"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Convert to dict
    bot_data = xml_to_dict(root)

    # Wrap in appropriate key based on file type
    if xml_file.name.endswith('.bot-meta.xml'):
        return {"Bot": bot_data}
    elif xml_file.name.endswith('.botVersion-meta.xml'):
        return {"BotVersion": bot_data}
    else:
        return bot_data


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_bot_xml_to_json.py <bot_name> <step1_dir>")
        print("\nExample:")
        print("  python3 convert_bot_xml_to_json.py MyBot /path/to/step1")
        sys.exit(1)

    bot_name = sys.argv[1]
    step1_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("step1")

    bots_dir = step1_dir / DIR_XML / DIR_BOTS
    jsons_dir = step1_dir / DIR_JSON

    jsons_dir.mkdir(parents=True, exist_ok=True)

    # Convert bot-meta.xml
    bot_xml = bots_dir / f"{bot_name}.bot-meta.xml"
    if bot_xml.exists():
        print(f"Converting {bot_xml}...")
        bot_data = convert_bot_xml(bot_xml)
        jsons_output = jsons_dir / f"{bot_name}.bot-meta.json"
        save_json_file(bot_data, jsons_output)
        print(f"  ✓ Created {jsons_output}")
    else:
        print(f"Error: {bot_xml} not found")
        sys.exit(1)

    # Convert botVersion XML files
    for version_xml in bots_dir.glob("*.botVersion-meta.xml"):
        print(f"Converting {version_xml}...")
        version_data = convert_bot_xml(version_xml)
        jsons_output = jsons_dir / version_xml.with_suffix('.json').name
        save_json_file(version_data, jsons_output)
        print(f"  ✓ Created {jsons_output}")

    print("\n✅ XML to JSON conversion complete!")


if __name__ == "__main__":
    main()
