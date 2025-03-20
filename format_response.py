"""
Response formatting module for the cyphr AI Extension.

This module provides functions for formatting Claude's responses
for display in the Tableau extension and optimizing data to reduce token usage.
"""

from typing import Optional, List, Dict, Any, Union
import re
import json
import logging

logger = logging.getLogger(__name__)


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


def optimize_data(data: Union[str, Dict[str, Any], List[Any]]) -> str:
    """
    Optimize data to reduce token count for LLM processing.
    
    Implements several optimization strategies:
    1. Abbreviate repetitive strings in measure names
    2. Use compact data formats (CSV-style for simple data)
    3. Round numerical precision
    4. Compress descriptive names with abbreviations
    
    Args:
        data: The data to optimize, either as a string or parsed JSON object
        
    Returns:
        Optimized data as a string
    """
    # If data is a string, try to parse it as JSON
    if isinstance(data, str):
        try:
            parsed_data = json.loads(data)
            return optimize_data(parsed_data)
        except json.JSONDecodeError:
            # If it's not JSON, return as is
            return data
    
    # If it's a dashboard with worksheets
    if isinstance(data, dict) and 'worksheets' in data and isinstance(data['worksheets'], list):
        dashboard_name = data.get('dashboardName', 'Dashboard')
        formatted_data = f"# {dashboard_name}\n\n"
        
        for worksheet in data['worksheets']:
            ws_name = worksheet.get('name', 'Unnamed Worksheet')
            ws_data = worksheet.get('data', {})
            
            formatted_data += f"## {ws_name}\n"
            
            # Add processing notes
            formatted_data += "\n**Processing Notes:**\n"
            formatted_data += "- Data has been optimized to reduce token usage\n"
            formatted_data += "- Measure names have been abbreviated\n"
            formatted_data += "- Numerical values have been rounded for efficiency\n\n"
            
            # Apply optimizations to worksheet data
            if isinstance(ws_data, dict):
                # Extract column name mappings and constant values
                column_mappings = {}
                constant_values = {}
                
                # If there are rows, process them
                if 'rows' in ws_data and isinstance(ws_data['rows'], list):
                    rows = ws_data['rows']
                    
                    # Extract column mappings and abbreviate
                    if rows and isinstance(rows[0], dict):
                        # Find columns with common prefixes/identifiers to abbreviate
                        measure_name_prefixes = {}
                        for row in rows:
                            for key, value in row.items():
                                if key == "Measure Names" and isinstance(value, str):
                                    # Extract federated ID prefixes
                                    match = re.search(r'\[federated\.([^]]+)]', value)
                                    if match:
                                        prefix = match.group(0)
                                        if prefix not in measure_name_prefixes:
                                            measure_name_prefixes[prefix] = f"F{len(measure_name_prefixes) + 1}"
                    
                    # Process constant values across all rows
                    if rows and len(rows) > 0:
                        # Find values that are constant across all rows
                        sample_row = rows[0]
                        for key, value in sample_row.items():
                            if key != "Measure Names" and key != "Measure Values" and key != "Date Selector Axis":
                                is_constant = True
                                constant_value = value
                                
                                for row in rows[1:]:
                                    if key not in row or row[key] != constant_value:
                                        is_constant = False
                                        break
                                
                                if is_constant:
                                    constant_values[key] = constant_value
                    
                    # Optimize the rows data
                    optimized_rows = []
                    for row in rows:
                        optimized_row = {}
                        
                        for key, value in row.items():
                            # Skip constant values
                            if key in constant_values:
                                continue
                            
                            if key == "Measure Names" and isinstance(value, str):
                                # Abbreviate measure names
                                abbreviated = value
                                for prefix, abbr in measure_name_prefixes.items():
                                    abbreviated = abbreviated.replace(prefix, abbr)
                                # Remove long IDs
                                abbreviated = re.sub(r'_\d{15,}', '_ID', abbreviated)
                                optimized_row[key] = abbreviated
                            elif key == "Measure Values" and isinstance(value, (int, float)):
                                # Round numerical values
                                if abs(value) < 0.001 or abs(value) > 1000000:
                                    # Use scientific notation for very small or large numbers
                                    optimized_row[key] = f"{value:.2e}"
                                elif abs(value) < 0.1:
                                    # Keep 4 decimal places for small numbers
                                    optimized_row[key] = round(value, 4)
                                elif abs(value) < 1:
                                    # Keep 3 decimal places for medium small numbers
                                    optimized_row[key] = round(value, 3)
                                elif abs(value) < 10:
                                    # Keep 2 decimal places for medium numbers
                                    optimized_row[key] = round(value, 2)
                                else:
                                    # Round to nearest integer for larger numbers
                                    optimized_row[key] = round(value)
                            else:
                                optimized_row[key] = value
                        
                        optimized_rows.append(optimized_row)
                    
                    # Determine if CSV format would be more efficient
                    use_csv_format = len(optimized_rows) > 5 and all(
                        len(row) <= 3 for row in optimized_rows
                    )
                    
                    # Output column mappings if we abbreviated
                    if measure_name_prefixes:
                        formatted_data += "\n**Abbreviated Column Prefixes:**\n"
                        for prefix, abbr in measure_name_prefixes.items():
                            formatted_data += f"- `{abbr}`: {prefix}\n"
                    
                    # Output constant values
                    if constant_values:
                        formatted_data += "\n**Constant Values (apply to all rows):**\n"
                        for key, value in constant_values.items():
                            formatted_data += f"- `{key}`: {value}\n"
                    
                    formatted_data += f"\n*Dataset sampled: showing {len(optimized_rows)} rows. *\n\n"
                    
                    # Use CSV format for better token efficiency if appropriate
                    if use_csv_format and optimized_rows:
                        # Get the headers
                        headers = list(optimized_rows[0].keys())
                        
                        # Create CSV header
                        csv_data = ",".join([f'"{h}"' for h in headers]) + "\n"
                        
                        # Add rows
                        for row in optimized_rows:
                            row_values = []
                            for header in headers:
                                val = row.get(header, "")
                                if isinstance(val, str):
                                    val = f'"{val}"'
                                else:
                                    val = str(val)
                                row_values.append(val)
                            csv_data += ",".join(row_values) + "\n"
                        
                        formatted_data += f"```csv\n{csv_data}```\n\n"
                    else:
                        # Use compact JSON for fewer tokens
                        compacted_rows = json.dumps({"rows": optimized_rows}, separators=(',', ':'))
                        formatted_data += f"```json\n{compacted_rows}\n```\n\n"
                else:
                    # No rows, just output the data in compact format
                    compacted_data = json.dumps(ws_data, separators=(',', ':'))
                    formatted_data += f"```json\n{compacted_data}\n```\n\n"
            else:
                # Not a dict, just output as is
                formatted_data += f"```\n{json.dumps(ws_data, separators=(',', ':'))}\n```\n\n"
        
        return formatted_data
    
    # For regular data (not dashboard format)
    elif isinstance(data, dict):
        # Compact JSON with minimal whitespace
        return json.dumps(data, separators=(',', ':'))
    
    elif isinstance(data, list):
        # If it's a simple list of primitive values
        if all(isinstance(item, (str, int, float, bool)) for item in data):
            return str(data)
        
        # Compact JSON for complex lists
        return json.dumps(data, separators=(',', ':'))
    
    # Default case
    return str(data)


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
    
    # Sample data optimization
    sample_data = {
        "worksheets": [
            {
                "name": "Sample Sheet",
                "data": {
                    "rows": [
                        {
                            "Measure Names": "[federated.0h4dzlz0y0okrc17lta4p18c1we8].[usr:F2F index YOY (copy)_1736982137076514834:qk]",
                            "Date Selector Axis": "Nov-24",
                            "Measure Values": 0.06761604004140297
                        },
                        {
                            "Measure Names": "[federated.0h4dzlz0y0okrc17lta4p18c1we8].[usr:Calculation_490892366328508426:qk]",
                            "Date Selector Axis": "Nov-24",
                            "Measure Values": 0.6137627999541156
                        }
                    ]
                }
            }
        ]
    }
    
    optimized = optimize_data(sample_data)
    print("\nOptimized data:")
    print(optimized)