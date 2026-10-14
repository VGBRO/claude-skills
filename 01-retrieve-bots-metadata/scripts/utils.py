#!/usr/bin/env python3
"""
Shared utility functions for Step 1: Retrieve Bot Metadata
Eliminates code duplication across scripts.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Callable, Optional


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Load JSON file with consistent error handling.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary containing JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """
    Save JSON file with consistent formatting.

    Args:
        data: Dictionary to save
        file_path: Path where to save the file
        indent: Number of spaces for indentation (default: 2)
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def recursive_process(obj: Any, processor: Callable[[Any], Any]) -> Any:
    """
    Recursively process an object structure (dicts, lists, primitives).

    This is a generic recursive traversal that applies a processor function
    to each leaf value while preserving the structure.

    Args:
        obj: Object to process (dict, list, or primitive)
        processor: Function to apply to leaf values

    Returns:
        Processed object with same structure

    Example:
        >>> def uppercase_strings(val):
        ...     return val.upper() if isinstance(val, str) else val
        >>> recursive_process({"a": "hello", "b": ["world"]}, uppercase_strings)
        {"a": "HELLO", "b": ["WORLD"]}
    """
    if isinstance(obj, dict):
        return {k: recursive_process(v, processor) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_process(item, processor) for item in obj]
    else:
        return processor(obj)


def extract_xml_namespace(element) -> str:
    """
    Extract XML namespace from element tag.

    Args:
        element: XML Element object

    Returns:
        Namespace string (empty if no namespace)

    Example:
        >>> element.tag = '{http://soap.sforce.com/2006/04/metadata}Bot'
        >>> extract_xml_namespace(element)
        'http://soap.sforce.com/2006/04/metadata'
    """
    if '}' in element.tag:
        return element.tag.split('}')[0].strip('{')
    return ''


def extract_tag_name(element) -> str:
    """
    Extract tag name without namespace.

    Args:
        element: XML Element object

    Returns:
        Tag name without namespace prefix

    Example:
        >>> element.tag = '{http://soap.sforce.com/2006/04/metadata}Bot'
        >>> extract_tag_name(element)
        'Bot'
    """
    return element.tag.split('}')[-1]


def parse_list_type(type_string: str) -> Optional[str]:
    """
    Parse List<T> type string and extract inner type.

    Args:
        type_string: Apex type string (e.g., "List<String>")

    Returns:
        Inner type if it's a List, None otherwise

    Example:
        >>> parse_list_type("List<String>")
        'String'
        >>> parse_list_type("String")
        None
    """
    from constants import REGEX_LIST_TYPE
    match = re.match(REGEX_LIST_TYPE, type_string.strip())
    return match.group(1).strip() if match else None


def ensure_array(value: Any, field_name: str, always_array_fields: set) -> Any:
    """
    Ensure certain fields are always arrays, even with single element.

    Args:
        value: Field value to process
        field_name: Name of the field
        always_array_fields: Set of field names that should always be arrays

    Returns:
        Value wrapped in array if field should be array and isn't already

    Example:
        >>> ensure_array("single", "mlIntents", {"mlIntents"})
        ["single"]
        >>> ensure_array(["already", "array"], "mlIntents", {"mlIntents"})
        ["already", "array"]
    """
    if field_name in always_array_fields and not isinstance(value, list):
        return [value] if value is not None else []
    return value


def convert_to_boolean(value: str, field_name: str, boolean_fields: set) -> Any:
    """
    Convert string to boolean if field is in boolean_fields set.

    Args:
        value: String value to convert
        field_name: Name of the field
        boolean_fields: Set of field names that should be booleans

    Returns:
        Boolean value if field should be boolean, original value otherwise

    Example:
        >>> convert_to_boolean("true", "mlIntentTrainingEnabled", {"mlIntentTrainingEnabled"})
        True
        >>> convert_to_boolean("false", "mlIntentTrainingEnabled", {"mlIntentTrainingEnabled"})
        False
    """
    if field_name in boolean_fields and isinstance(value, str):
        return value.lower() == 'true'
    return value


def sort_dict_recursive(obj: Any) -> Any:
    """
    Recursively sort all dictionaries in an object structure.

    Args:
        obj: Object to sort (dict, list, or primitive)

    Returns:
        Sorted object (dicts sorted by keys, lists preserved)

    Example:
        >>> sort_dict_recursive({"z": 1, "a": 2})
        {"a": 2, "z": 1}
    """
    if isinstance(obj, dict):
        return {k: sort_dict_recursive(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [sort_dict_recursive(item) for item in obj]
    else:
        return obj


def get_project_root(current_file: Path, levels_up: int = 4) -> Path:
    """
    Get project root directory by going up from current file.

    Args:
        current_file: Current script file path (__file__)
        levels_up: Number of directory levels to go up

    Returns:
        Path to project root

    Example:
        >>> # If script is at: /project/.claude/skills/01-/scripts/script.py
        >>> get_project_root(Path(__file__), 4)
        Path('/project')
    """
    path = Path(current_file).resolve()
    for _ in range(levels_up):
        path = path.parent
    return path


def safe_get_nested(data: Dict, *keys, default=None) -> Any:
    """
    Safely get nested dictionary value with default.

    Args:
        data: Dictionary to traverse
        *keys: Sequence of keys to traverse
        default: Default value if any key is missing

    Returns:
        Value at nested key path, or default if not found

    Example:
        >>> data = {"a": {"b": {"c": 123}}}
        >>> safe_get_nested(data, "a", "b", "c")
        123
        >>> safe_get_nested(data, "a", "x", "y", default=0)
        0
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries (later dicts override earlier ones).

    Args:
        *dicts: Variable number of dictionaries to merge

    Returns:
        Merged dictionary

    Example:
        >>> merge_dicts({"a": 1}, {"b": 2}, {"a": 3})
        {"a": 3, "b": 2}
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result
