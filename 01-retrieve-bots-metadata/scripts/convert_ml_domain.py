#!/usr/bin/env python3
"""
Convert ML Domain XML metadata to JSON format
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_ml_domain_xml(xml_file):
    """Parse MlDomain XML and convert to JSON structure"""

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Namespace handling
    ns = {'sf': 'http://soap.sforce.com/2006/04/metadata'}

    # Extract ML Domain name from filename
    ml_domain_name = Path(xml_file).stem.replace('.mlDomain-meta', '')

    # Get label (or default to domain name)
    label_elem = root.find('sf:label', ns)
    label = label_elem.text if label_elem is not None else ml_domain_name

    ml_domain = {
        "fullName": ml_domain_name,
        "label": label,
        "mlIntents": []
    }

    # Parse all intents
    for intent_elem in root.findall('sf:mlIntents', ns):
        dev_name_elem = intent_elem.find('sf:developerName', ns)
        label_elem = intent_elem.find('sf:label', ns)

        intent = {
            "developerName": dev_name_elem.text if dev_name_elem is not None else "",
            "label": label_elem.text if label_elem is not None else "",
            "mlIntentUtterances": []
        }

        # Parse utterances
        for utt_elem in intent_elem.findall('sf:mlIntentUtterances', ns):
            utterance_elem = utt_elem.find('sf:utterance', ns)
            if utterance_elem is not None:
                intent["mlIntentUtterances"].append({
                    "utterance": utterance_elem.text
                })

        ml_domain["mlIntents"].append(intent)

    return ml_domain


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_ml_domain.py <ml_domain_xml_file>")
        print("Example:")
        print('  python3 scripts/convert_ml_domain.py \\')
        print('               "data/sf-cli/main/default/mlDomains/MyMLDomain.mlDomain-meta.xml"')
        sys.exit(1)

    xml_file = sys.argv[1]

    if not Path(xml_file).exists():
        print(f"Error: File not found: {xml_file}")
        sys.exit(1)

    print(f"Parsing {xml_file}...")

    ml_domain = parse_ml_domain_xml(xml_file)

    print(f"\n✓ Parsed successfully!")
    print(f"  Domain: {ml_domain['fullName']}")
    print(f"  Label: {ml_domain['label']}")
    print(f"  Intents: {len(ml_domain['mlIntents'])}")

    # Count total utterances
    total_utterances = sum(len(intent['mlIntentUtterances'])
                          for intent in ml_domain['mlIntents'])
    print(f"  Total utterances: {total_utterances}")

    # Show sample intents
    print("\nSample intents:")
    for i, intent in enumerate(ml_domain['mlIntents'][:5], 1):
        utt_count = len(intent['mlIntentUtterances'])
        print(f"  {i}. {intent['developerName']} ({utt_count} utterances)")

    # Save to JSON
    output_file = xml_file.replace('.mlDomain-meta.xml', '.json')
    with open(output_file, 'w') as f:
        json.dump(ml_domain, f, indent=2)

    print(f"\n✓ Saved to: {output_file}")

    return ml_domain


if __name__ == "__main__":
    main()
