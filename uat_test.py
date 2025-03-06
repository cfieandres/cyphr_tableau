#!/usr/bin/env python3
"""
User Acceptance Testing (UAT) for the cyphr AI Extension.

This script simulates a typical user flow and checks the quality of the responses,
focusing on readability and usefulness of the generated content.
"""

import requests
import json
import time
import statistics
import re
from typing import Dict, Any, List, Tuple
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default server URL
DEFAULT_URL = "http://localhost:8000"

# Test scenarios
SCENARIOS = [
    {
        "name": "Sales Analysis",
        "data": json.dumps({
            "sales": [120, 150, 200, 250, 300],
            "months": ["Jan", "Feb", "Mar", "Apr", "May"],
            "products": ["Widget A", "Widget B", "Widget C"]
        }),
        "endpoint": "/analytics",
        "format_type": "bullet"
    },
    {
        "name": "Inventory Summary",
        "data": json.dumps({
            "inventory": [50, 75, 25, 100],
            "products": ["Widget A", "Widget B", "Widget C", "Widget D"],
            "warehouses": ["North", "South", "East", "West"]
        }),
        "endpoint": "/summarization",
        "format_type": "paragraph"
    },
    {
        "name": "General Query",
        "data": "What are the key performance indicators for a retail business?",
        "endpoint": "/general",
        "format_type": "auto"
    },
    {
        "name": "Sales Forecast",
        "data": "Based on the trend, what sales can we expect for June?",
        "endpoint": "/route",
        "task_type": "analyze",
        "format_type": "bullet"
    }
]


def send_request(url: str, endpoint: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
    """
    Send a request to the server and measure response time.
    
    Args:
        url: The base URL of the server
        endpoint: The endpoint to call
        data: The request data
        
    Returns:
        A tuple of (response_data, response_time)
    """
    # Construct the full URL
    full_url = f"{url}{endpoint}"
    
    # Send the request and measure time
    start_time = time.time()
    response = requests.post(full_url, json=data)
    response_time = time.time() - start_time
    
    # Raise an exception if the request failed
    response.raise_for_status()
    
    # Return the response data and time
    return response.json(), response_time


def evaluate_response(response_text: str) -> Dict[str, Any]:
    """
    Evaluate the quality of a response.
    
    Args:
        response_text: The response text to evaluate
        
    Returns:
        A dictionary of evaluation metrics
    """
    # Calculate length metrics
    char_count = len(response_text)
    word_count = len(response_text.split())
    lines = response_text.split('\n')
    line_count = len(lines)
    
    # Calculate readability metrics
    words_per_line = word_count / max(1, line_count)
    avg_word_length = sum(len(word) for word in response_text.split()) / max(1, word_count)
    
    # Check for bullet points
    bullet_points = len(re.findall(r'^\s*[•\-\*]\s', response_text, re.MULTILINE))
    
    return {
        "char_count": char_count,
        "word_count": word_count,
        "line_count": line_count,
        "words_per_line": words_per_line,
        "avg_word_length": avg_word_length,
        "bullet_points": bullet_points,
        "is_readable": char_count < 2000 and words_per_line < 20,
        "has_structure": bullet_points > 0 or line_count > 3
    }


def run_uat_tests(url: str = DEFAULT_URL, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Run User Acceptance Tests on the server.
    
    Args:
        url: The base URL of the server
        verbose: Whether to print detailed results
        
    Returns:
        A list of test results
    """
    results = []
    
    print(f"Running UAT tests against {url}...")
    
    # Check server health
    try:
        health_response = requests.get(f"{url}/health")
        health_response.raise_for_status()
        print(f"Server health check: OK (status {health_response.status_code})")
    except Exception as e:
        print(f"Server health check: FAILED ({e})")
        return []
    
    # Run each test scenario
    for scenario in SCENARIOS:
        print(f"\nRunning scenario: {scenario['name']}...")
        
        try:
            # Prepare request data
            request_data = {
                "data": scenario["data"],
                "format_type": scenario["format_type"]
            }
            
            # Add task_type if it's a route request
            if scenario["endpoint"] == "/route":
                request_data["task_type"] = scenario["task_type"]
            
            # Send the request
            response_data, response_time = send_request(url, scenario["endpoint"], request_data)
            
            if "response" in response_data:
                response_text = response_data["response"]
                
                # Evaluate the response
                evaluation = evaluate_response(response_text)
                
                # Calculate an overall quality score (simple heuristic)
                quality_score = 0
                if evaluation["is_readable"]:
                    quality_score += 5
                if evaluation["has_structure"]:
                    quality_score += 5
                if evaluation["word_count"] > 50:
                    quality_score += 3
                if evaluation["bullet_points"] > 0:
                    quality_score += 2
                
                # Prepare result
                result = {
                    "scenario": scenario["name"],
                    "endpoint": scenario["endpoint"],
                    "response_time": response_time,
                    "evaluation": evaluation,
                    "quality_score": quality_score,
                    "success": True
                }
                
                # Print detailed results if verbose
                if verbose:
                    print(f"  Response time: {response_time:.2f}s")
                    print(f"  Response length: {evaluation['char_count']} chars, {evaluation['word_count']} words")
                    print(f"  Quality score: {quality_score}/15")
                    print(f"  Response snippet: {response_text[:100]}...")
                else:
                    print(f"  Success: Response time {response_time:.2f}s, Quality score {quality_score}/15")
            else:
                result = {
                    "scenario": scenario["name"],
                    "endpoint": scenario["endpoint"],
                    "success": False,
                    "error": "No response field in response data"
                }
                print(f"  Failed: No response field in response data")
        
        except Exception as e:
            result = {
                "scenario": scenario["name"],
                "endpoint": scenario["endpoint"],
                "success": False,
                "error": str(e)
            }
            print(f"  Failed: {e}")
        
        results.append(result)
    
    # Calculate summary statistics
    successful_tests = [r for r in results if r.get("success", False)]
    response_times = [r["response_time"] for r in successful_tests if "response_time" in r]
    quality_scores = [r["quality_score"] for r in successful_tests if "quality_score" in r]
    
    if response_times:
        avg_response_time = statistics.mean(response_times)
        avg_quality_score = statistics.mean(quality_scores) if quality_scores else 0
        
        print("\nUAT Summary:")
        print(f"  Total tests: {len(results)}")
        print(f"  Successful tests: {len(successful_tests)}/{len(results)}")
        print(f"  Average response time: {avg_response_time:.2f}s")
        print(f"  Average quality score: {avg_quality_score:.2f}/15")
    
    return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run UAT tests on the cyphr AI Extension server")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="Server URL")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")
    args = parser.parse_args()
    
    run_uat_tests(args.url, args.verbose)


if __name__ == "__main__":
    main()