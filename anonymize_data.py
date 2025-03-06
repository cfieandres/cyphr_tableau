"""
Data anonymization module for the cyphr AI Extension.

This module provides functions for anonymizing sensitive data
before sending it for processing.
"""

import re
import json
from typing import Any, Dict, List, Union, Optional

# Regular expressions for identifying sensitive data
PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
    "ssn": r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
    "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
}

# Replacement values for sensitive data
REPLACEMENTS = {
    "email": "[EMAIL REDACTED]",
    "phone": "[PHONE REDACTED]",
    "ssn": "[SSN REDACTED]",
    "credit_card": "[CREDIT CARD REDACTED]",
    "ip_address": "[IP ADDRESS REDACTED]",
}


def anonymize_text(text: str, patterns_to_use: Optional[List[str]] = None) -> str:
    """
    Anonymize sensitive data in text.
    
    Args:
        text: The text to anonymize
        patterns_to_use: List of pattern types to use for anonymization.
                        If None, uses all patterns.
                        
    Returns:
        The anonymized text
    """
    if not text:
        return text
    
    # If no specific patterns are provided, use all
    if patterns_to_use is None:
        patterns_to_use = list(PATTERNS.keys())
    
    # Anonymize each pattern
    result = text
    for pattern_type in patterns_to_use:
        if pattern_type in PATTERNS:
            pattern = PATTERNS[pattern_type]
            replacement = REPLACEMENTS[pattern_type]
            result = re.sub(pattern, replacement, result)
    
    return result


def anonymize_dict(data: Dict[str, Any], fields_to_anonymize: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Anonymize sensitive data in a dictionary.
    
    Args:
        data: The dictionary to anonymize
        fields_to_anonymize: List of field names to anonymize.
                            If None, anonymizes all string fields that might contain sensitive data.
                            
    Returns:
        The anonymized dictionary
    """
    result = {}
    
    for key, value in data.items():
        # If this is a field we should anonymize, or we're checking all fields
        if fields_to_anonymize is None or key in fields_to_anonymize:
            if isinstance(value, str):
                result[key] = anonymize_text(value)
            elif isinstance(value, dict):
                result[key] = anonymize_dict(value, fields_to_anonymize)
            elif isinstance(value, list):
                result[key] = anonymize_list(value, fields_to_anonymize)
            else:
                result[key] = value
        else:
            # Not a field to anonymize, but still need to check nested structures
            if isinstance(value, dict):
                result[key] = anonymize_dict(value, fields_to_anonymize)
            elif isinstance(value, list):
                result[key] = anonymize_list(value, fields_to_anonymize)
            else:
                result[key] = value
    
    return result


def anonymize_list(data: List[Any], fields_to_anonymize: Optional[List[str]] = None) -> List[Any]:
    """
    Anonymize sensitive data in a list.
    
    Args:
        data: The list to anonymize
        fields_to_anonymize: List of field names to anonymize (for dictionaries in the list).
                            If None, anonymizes all string fields that might contain sensitive data.
                            
    Returns:
        The anonymized list
    """
    result = []
    
    for item in data:
        if isinstance(item, str):
            result.append(anonymize_text(item))
        elif isinstance(item, dict):
            result.append(anonymize_dict(item, fields_to_anonymize))
        elif isinstance(item, list):
            result.append(anonymize_list(item, fields_to_anonymize))
        else:
            result.append(item)
    
    return result


def anonymize_data(data: Union[str, Dict[str, Any], List[Any]], fields_to_anonymize: Optional[List[str]] = None) -> Union[str, Dict[str, Any], List[Any]]:
    """
    Anonymize sensitive data in various data formats.
    
    Args:
        data: The data to anonymize (string, dictionary, or list)
        fields_to_anonymize: List of field names to anonymize (for dictionaries).
                            If None, anonymizes all string fields that might contain sensitive data.
                            
    Returns:
        The anonymized data in the same format as the input
    """
    if isinstance(data, str):
        # Try to parse as JSON
        try:
            parsed_data = json.loads(data)
            if isinstance(parsed_data, dict):
                return json.dumps(anonymize_dict(parsed_data, fields_to_anonymize))
            elif isinstance(parsed_data, list):
                return json.dumps(anonymize_list(parsed_data, fields_to_anonymize))
        except:
            # Not valid JSON, treat as text
            return anonymize_text(data)
    elif isinstance(data, dict):
        return anonymize_dict(data, fields_to_anonymize)
    elif isinstance(data, list):
        return anonymize_list(data, fields_to_anonymize)
    else:
        # Not a type we can anonymize
        return data


# Example usage
if __name__ == "__main__":
    # Sample data with sensitive information
    sample_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "ssn": "123-45-6789",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345"
        },
        "credit_cards": [
            {
                "type": "Visa",
                "number": "4111 1111 1111 1111",
                "expiry": "12/25"
            }
        ],
        "ip_address": "192.168.1.1"
    }
    
    # Anonymize the data
    anonymized_data = anonymize_data(sample_data)
    
    # Print the original and anonymized data
    print("Original data:")
    print(json.dumps(sample_data, indent=2))
    print("\nAnonymized data:")
    print(json.dumps(anonymized_data, indent=2))