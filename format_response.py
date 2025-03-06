"""
Response formatting module for the cyphr AI Extension.

This module provides functions for formatting Claude's responses
for display in the Tableau extension.
"""

from typing import Optional, List
import re


def format_response(response: str, format_type: Optional[str] = "auto") -> str:
    """
    Format Claude's response for display.
    
    Args:
        response: The raw response from Claude
        format_type: The type of formatting to apply:
            - "auto": Automatically detect and apply appropriate formatting
            - "bullet": Format as bullet points
            - "paragraph": Format as paragraphs
            - "json": Format as prettified JSON
            - "raw": No formatting (return as-is)
            
    Returns:
        The formatted response
    """
    # Handle empty or None responses
    if not response:
        return "No response received."
    
    # Strip leading/trailing whitespace
    response = response.strip()
    
    # If raw format is requested, return the response as-is
    if format_type == "raw":
        return response
    
    # Auto-detect the format if not specified
    if format_type == "auto":
        # Check if response looks like JSON
        if (response.startswith('{') and response.endswith('}')) or \
           (response.startswith('[') and response.endswith(']')):
            format_type = "json"
        # Check if response already has bullet points
        elif re.search(r'^\s*[•\-\*]\s', response, re.MULTILINE):
            format_type = "bullet"
        # Check if response has multiple lines (potential bullet points)
        elif response.count('\n') > 2:
            format_type = "bullet"
        else:
            format_type = "paragraph"
    
    # Format the response based on the format type
    if format_type == "bullet":
        return format_as_bullets(response)
    elif format_type == "json":
        return format_as_json(response)
    elif format_type == "paragraph":
        return format_as_paragraphs(response)
    else:
        # Unknown format type, return as-is
        return response


def format_as_bullets(response: str) -> str:
    """
    Format a response as bullet points.
    
    Args:
        response: The response to format
        
    Returns:
        The formatted response with bullet points
    """
    # If the response already has bullet points, return it as-is
    if re.search(r'^\s*[•\-\*]\s', response, re.MULTILINE):
        return response
    
    # Split the response into lines
    lines = response.split('\n')
    
    # Process each line
    formatted_lines = []
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            # If we have a paragraph, add it as a bullet point
            if current_paragraph:
                paragraph_text = ' '.join(current_paragraph)
                formatted_lines.append(f"• {paragraph_text}")
                current_paragraph = []
            
            # Add a blank line to separate groups of bullet points
            if formatted_lines and formatted_lines[-1]:
                formatted_lines.append('')
            
            continue
        
        # Add the line to the current paragraph
        current_paragraph.append(line)
    
    # Add any remaining paragraph as a bullet point
    if current_paragraph:
        paragraph_text = ' '.join(current_paragraph)
        formatted_lines.append(f"• {paragraph_text}")
    
    # Join the formatted lines
    return '\n'.join(formatted_lines)


def format_as_paragraphs(response: str) -> str:
    """
    Format a response as paragraphs.
    
    Args:
        response: The response to format
        
    Returns:
        The formatted response with paragraphs
    """
    # Split the response into paragraphs
    paragraphs = re.split(r'\n\s*\n', response)
    
    # Join the paragraphs with double newlines
    return '\n\n'.join(p.replace('\n', ' ') for p in paragraphs if p.strip())


def format_as_json(response: str) -> str:
    """
    Format a JSON response for better readability.
    
    Args:
        response: The JSON response to format
        
    Returns:
        The prettified JSON response
    """
    try:
        import json
        
        # Try to parse the response as JSON
        json_obj = json.loads(response)
        
        # Pretty-print the JSON
        formatted_json = json.dumps(json_obj, indent=2)
        
        return formatted_json
    except:
        # If there's an error parsing as JSON, return the original response
        return response


# Example usage
if __name__ == "__main__":
    # Sample response
    sample_response = """
    This is a sample response from Claude.
    
    It contains multiple paragraphs with different information.
    
    Here are some key points:
    The first important point is that this is just a test.
    Second, formatting can make responses more readable.
    Third, bullet points are often easier to scan than paragraphs.
    
    This final paragraph summarizes everything.
    """
    
    # Format the response as bullet points
    bullet_format = format_response(sample_response, format_type="bullet")
    
    # Print the original and formatted responses
    print("Original response:")
    print(sample_response)
    print("\nFormatted as bullet points:")
    print(bullet_format)