#!/usr/bin/env python3
"""
Test script for data optimization.

This script tests the token reduction capabilities of the optimize_data function
by comparing token counts before and after optimization.
"""

import json
import sys
from format_response import optimize_data

def estimate_tokens(text):
    """Estimate token count based on character count."""
    if not text:
        return 0
    return len(text) // 4  # Rough approximation

def test_optimization():
    # Sample dashboard data similar to what would be processed by the app
    sample_data = {
        "dashboardName": "Performance Metrics",
        "worksheets": [
            {
                "name": "Trend Sheet",
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
                        },
                        {
                            "Measure Names": "[federated.0h4dzlz0y0okrc17lta4p18c1we8].[usr:In Store Sale YOY (copy)_1736982137076650003:qk]",
                            "Date Selector Axis": "Nov-24",
                            "Measure Values": 0.39402757476575007
                        },
                        {
                            "Measure Names": "[federated.0h4dzlz0y0okrc17lta4p18c1we8].[sum:Calculation_490892366327939081:qk]",
                            "Date Selector Axis": "Nov-24",
                            "Measure Values": 28137908.304160833
                        },
                        {
                            "Measure Names": "[federated.0h4dzlz0y0okrc17lta4p18c1we8].[usr:Renewals YOY (copy)_1736982137075933198:qk]",
                            "Date Selector Axis": "Nov-24",
                            "Measure Values": 0.2205143969877176
                        },
                        {
                            "Measure Names": "[federated.0h4dzlz0y0okrc17lta4p18c1we8].[sum:MODELLED_COMPENSATION:qk]",
                            "Date Selector Axis": "Nov-24",
                            "Measure Values": 14311161.055839166
                        },
                        {
                            "Measure Names": "[federated.0h4dzlz0y0okrc17lta4p18c1we8].[usr:Total Revenue YOY (copy)_1736982137076244496:qk]",
                            "Date Selector Axis": "Nov-24",
                            "Measure Values": 0.2807718781894567
                        }
                    ]
                }
            }
        ]
    }
    
    # Convert to string with standard JSON formatting
    original_data_str = json.dumps(sample_data, indent=2)
    
    # Get original token count
    original_tokens = estimate_tokens(original_data_str)
    
    # Optimize the data
    optimized_data_str = optimize_data(sample_data)
    
    # Get optimized token count
    optimized_tokens = estimate_tokens(optimized_data_str)
    
    # Calculate token and percentage reduction
    token_reduction = original_tokens - optimized_tokens
    percentage_reduction = (token_reduction / original_tokens) * 100 if original_tokens > 0 else 0
    
    # Print results
    print(f"Original data length: {len(original_data_str)} characters")
    print(f"Optimized data length: {len(optimized_data_str)} characters")
    print(f"Original token count (estimated): {original_tokens}")
    print(f"Optimized token count (estimated): {optimized_tokens}")
    print(f"Token reduction: {token_reduction} tokens ({percentage_reduction:.1f}%)")
    
    print("\nOriginal data:")
    print("=" * 80)
    print(original_data_str[:500] + "..." if len(original_data_str) > 500 else original_data_str)
    print("=" * 80)
    print("\nOptimized data:")
    print("=" * 80)
    print(optimized_data_str)
    print("=" * 80)
    
    return token_reduction > 0

if __name__ == "__main__":
    print("Testing data optimization...")
    success = test_optimization()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)