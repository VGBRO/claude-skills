#!/usr/bin/env python3
"""
Parse Apex class files to extract @InvocableMethod signatures.
Builds accurate botInvocationsDescribeInfo from actual source code.
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from constants import (
    APEX_TYPE_MAP, KEY_TYPE, KEY_SOBJECT_TYPE, KEY_COLLECTION_TYPE,
    KEY_INPUT_PARAMETERS, KEY_OUTPUT_PARAMETERS, KEY_NAME, KEY_REQUIRED,
    REGEX_LIST_TYPE, REGEX_APEX_VARIABLE, REGEX_INVOCABLE_METHOD
)
from utils import load_json_file, save_json_file, parse_list_type, sort_dict_recursive


def parse_apex_type(apex_type: str) -> Dict:
    """
    Convert Apex type to bot invocation type descriptor.

    Examples:
        String -> {"type": "STRING"}
        Boolean -> {"type": "BOOLEAN"}
        CustomObject__c -> {"type": "SOBJECT", "sobjectType": "CustomObject__c"}
        List<String> -> {"type": "STRING", "collectionType": "List"}
    """
    apex_type = apex_type.strip()

    # Handle List types
    inner_type = parse_list_type(apex_type)
    if inner_type:
        result = parse_apex_type(inner_type)
        result[KEY_COLLECTION_TYPE] = "List"
        return result

    # Check if it's a standard type
    if apex_type in APEX_TYPE_MAP:
        return {KEY_TYPE: APEX_TYPE_MAP[apex_type]}

    # Otherwise assume it's an SObject
    if apex_type.endswith('__c') or apex_type in ['Account', 'Contact', 'Case', 'User', 'Lead', 'Opportunity']:
        return {KEY_TYPE: "SOBJECT", KEY_SOBJECT_TYPE: apex_type}

    # Default fallback
    return {KEY_TYPE: "STRING"}


def parse_invocable_variable(line: str) -> Optional[Tuple[str, str, bool]]:
    """
    Parse @InvocableVariable annotation.
    Returns: (variable_name, variable_type, is_required) or None

    Example input:
        @InvocableVariable(required=true)
        public String newAddress;
    """
    # Check if this is an @InvocableVariable line
    if '@InvocableVariable' not in line:
        return None

    # Check for required flag
    required = 'required=true' in line or 'required = true' in line

    return ('', '', required)  # Name and type will be parsed from next line


def parse_variable_declaration(line: str) -> Optional[Tuple[str, str]]:
    """
    Parse variable declaration line.
    Returns: (variable_type, variable_name) or None

    Example:
        public String newAddress; -> ('String', 'newAddress')
        public CustomObject__c record; -> ('CustomObject__c', 'record')
    """
    # Match: public <Type> <name>;
    match = re.search(r'public\s+([\w<>]+)\s+(\w+)\s*;', line)
    if match:
        var_type = match.group(1)
        var_name = match.group(2)
        return (var_type, var_name)
    return None


def parse_simple_invocable_signature(content: str) -> Optional[Dict]:
    """
    Parse simple @InvocableMethod signatures (direct method signature, no Request/Response classes).

    Example:
        @InvocableMethod(...)
        public static List<String> methodName(List<String> inputParam)

    Returns:
        {
            "inputParameters": {"inputParam": {"type": "STRING"}},
            "outputParameters": {"output": {"type": "STRING"}}
        }
    """
    import re

    # Find @InvocableMethod annotation followed by method signature
    pattern = r'@InvocableMethod.*?\n\s*public\s+static\s+([\w<>,\s]+)\s+\w+\s*\((.*?)\)'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return None

    return_type = match.group(1).strip()
    params_str = match.group(2).strip()

    input_params = {}
    output_params = {}

    # Parse input parameter
    if params_str:
        # Simple pattern: Type paramName
        param_match = re.match(r'([\w<>,\s]+)\s+(\w+)', params_str)
        if param_match:
            param_type = param_match.group(1).strip()
            param_name = param_match.group(2).strip()

            # Convert List<String> -> STRING, etc.
            if 'List<String>' in param_type or 'String' in param_type:
                input_params[param_name] = {"type": "STRING"}
            elif 'List<Integer>' in param_type or 'Integer' in param_type:
                input_params[param_name] = {"type": "NUMBER"}
            elif 'List<Boolean>' in param_type or 'Boolean' in param_type:
                input_params[param_name] = {"type": "BOOLEAN"}
            else:
                # Default to STRING for unknown types
                input_params[param_name] = {"type": "STRING"}

    # Parse output (return type)
    if return_type and return_type != 'void':
        # Convert List<String> -> STRING, etc.
        if 'List<String>' in return_type or 'String' in return_type:
            output_params["output"] = {"type": "STRING"}
        elif 'List<Integer>' in return_type or 'Integer' in return_type:
            output_params["output"] = {"type": "NUMBER"}
        elif 'List<Boolean>' in return_type or 'Boolean' in return_type:
            output_params["output"] = {"type": "BOOLEAN"}
        elif return_type != 'void':
            # Default to STRING for unknown types
            output_params["output"] = {"type": "STRING"}

    return {
        "inputParameters": input_params,
        "outputParameters": output_params
    }


def parse_apex_class(apex_file: Path) -> Optional[Dict]:
    """
    Parse an Apex class file and extract @InvocableMethod signature.

    Strategy:
    1. Check actual @InvocableMethod signature to determine parameter pattern
    2. If uses Request/Response classes, parse those
    3. Otherwise, use simple signature parsing

    Returns:
        {
            "inputParameters": {...},
            "outputParameters": {...}
        }
    """
    if not apex_file.exists():
        return None

    with open(apex_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # First, check the actual @InvocableMethod signature
    import re
    method_pattern = r'@InvocableMethod.*?\n\s*public\s+static\s+([\w<>,\s]+)\s+\w+\s*\((.*?)\)'
    method_match = re.search(method_pattern, content, re.DOTALL)

    uses_request_for_input = False
    uses_response_for_output = False

    if method_match:
        return_type = method_match.group(1).strip()
        param_type = method_match.group(2).strip()

        # Check if uses Request class for input
        if 'Request' in param_type:
            uses_request_for_input = True

        # Check if uses Response class for output
        if 'Response' in return_type:
            uses_response_for_output = True

    # Parse Request/Response classes if used
    input_params = {}
    output_params = {}

    if uses_request_for_input or uses_response_for_output:
        lines = content.split('\n')
        input_params = {}
        output_params = {}
        current_class = None
        pending_variable = None

        for i, line in enumerate(lines):
            line = line.strip()

            # Detect inner class definitions
            if 'class' in line and 'Request' in line:
                current_class = 'input'
                continue
            elif 'class' in line and 'Response' in line:
                current_class = 'output'
                continue
            elif line.startswith('public class') or line.startswith('private class'):
                # End of inner class
                if 'Request' not in line and 'Response' not in line:
                    current_class = None
                continue

            # Parse @InvocableVariable
            if '@InvocableVariable' in line:
                var_info = parse_invocable_variable(line)
                if var_info:
                    pending_variable = var_info
                continue

            # Parse variable declaration (follows @InvocableVariable)
            if pending_variable and current_class:
                var_decl = parse_variable_declaration(line)
                if var_decl:
                    var_type, var_name = var_decl
                    _, _, required = pending_variable

                    type_info = parse_apex_type(var_type)
                    if required:
                        type_info['required'] = True

                    if current_class == 'input':
                        input_params[var_name] = type_info
                    elif current_class == 'output':
                        output_params[var_name] = type_info

                    pending_variable = None

        # For mixed patterns, use simple parsing for the non-Request/Response part
        if not uses_request_for_input or not uses_response_for_output:
            simple_result = parse_simple_invocable_signature(content)
            if simple_result:
                # Use simple parsing for input if no Request class
                if not uses_request_for_input and simple_result['inputParameters']:
                    input_params = simple_result['inputParameters']
                # Use simple parsing for output if no Response class
                if not uses_response_for_output and simple_result['outputParameters']:
                    output_params = simple_result['outputParameters']

        return {
            "inputParameters": input_params,
            "outputParameters": output_params
        }

    # Fallback: pure simple signature parsing
    return parse_simple_invocable_signature(content)


def extract_apex_invocations(apex_dir: Path, class_names: List[str]) -> Dict[str, Dict]:
    """
    Extract invocation metadata for all specified Apex classes.

    Args:
        apex_dir: Directory containing retrieved Apex classes
        class_names: List of Apex class names to process

    Returns:
        Dictionary keyed by class name with invocation metadata
    """
    invocations = {}

    for class_name in class_names:
        apex_file = apex_dir / f"{class_name}.cls"

        if not apex_file.exists():
            print(f"  ⚠️  Apex class not found: {class_name}")
            continue

        result = parse_apex_class(apex_file)
        if result:
            invocations[class_name] = result
            print(f"  ✅ Parsed: {class_name} ({len(result['inputParameters'])} inputs, {len(result['outputParameters'])} outputs)")
        else:
            print(f"  ❌ Failed to parse: {class_name}")

    return invocations


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Parse Apex invocable methods from source code')
    parser.add_argument('--apex-dir', required=True, help='Directory containing Apex class files')
    parser.add_argument('--classes', nargs='+', help='List of class names to parse (space-separated)')
    parser.add_argument('--output', '-o', help='Output JSON file')

    args = parser.parse_args()

    apex_dir = Path(args.apex_dir)
    if not apex_dir.exists():
        print(f"Error: Apex directory not found: {apex_dir}")
        sys.exit(1)

    # If no classes specified, find all .cls files
    if not args.classes:
        class_files = list(apex_dir.glob("*.cls"))
        class_names = [f.stem for f in class_files]
    else:
        class_names = args.classes

    print(f"Parsing {len(class_names)} Apex classes from {apex_dir}...")

    invocations = extract_apex_invocations(apex_dir, class_names)

    print(f"\nSuccessfully parsed {len(invocations)} / {len(class_names)} classes")

    # Sort invocations alphabetically by class name
    sorted_invocations = dict(sorted(invocations.items()))

    # Build output structure
    result = {
        "apex": sorted_invocations,
        "flow": {}  # Placeholder for future flow support
    }

    # Output
    if args.output:
        output_file = Path(args.output)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Saved to: {output_file}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
