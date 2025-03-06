"""
Script to initialize the database with sample endpoints.
Run this script to create default endpoints in a new installation.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent))

# Import the database
from database.db import db

def initialize_database():
    """Initialize the database with sample endpoints."""
    print("Initializing database with sample endpoints...")
    
    # Add analytics endpoint
    db.add_or_update_endpoint(
        endpoint="/analytics",
        agent_id="analytics-agent",
        name="Analytics",
        description="Analyze dashboard data to identify trends, patterns, and insights",
        instructions="Analyze data and provide comprehensive insights with bullet points.",
        indicators=["trend", "analysis", "correlation", "insight", "detail", "breakdown"],
        priority=10,
        model="claude-3-5-sonnet",
        temperature=0.5
    )
    print("Added analytics endpoint")
    
    # Add summarization endpoint
    db.add_or_update_endpoint(
        endpoint="/summarization",
        agent_id="summary-agent",
        name="Summarization",
        description="Provide concise summaries of dashboard data",
        instructions="Create a concise summary of the provided data, highlighting key points.",
        indicators=["summary", "overview", "report", "brief"],
        priority=20,
        model="claude-3-5-sonnet",
        temperature=0.3
    )
    print("Added summarization endpoint")
    
    # Add general endpoint
    db.add_or_update_endpoint(
        endpoint="/general",
        agent_id="general-agent",
        name="General Questions",
        description="Answer specific questions about dashboard data",
        instructions="Respond helpfully to user queries about the data.",
        indicators=["question", "query", "what", "why", "how", "when", "where"],
        priority=30,
        model="claude-3-5-sonnet",
        temperature=0.7
    )
    print("Added general endpoint")
    
    # Add store-perf endpoint
    db.add_or_update_endpoint(
        endpoint="/store-perf",
        agent_id="store-performance",
        name="Store Performance Analysis",
        description="Analysis for Store Performance related manners",
        instructions="Analyze the provided insurance agency store's Profit and Loss (P&L) statement and performance data. Provide 5 high-level, actionable insights to improve profitability. Each insight should include a clear, concise recommendation for immediate implementation",
        indicators=["store", "p&l", "performance"],
        priority=40,
        model="claude-3-5-sonnet",
        temperature=0.7
    )
    print("Added store-perf endpoint")
    
    # Print all endpoints
    endpoints = db.get_all_endpoints()
    print(f"\nTotal of {len(endpoints)} endpoints in database:")
    for endpoint in endpoints:
        print(f"- {endpoint['name']} ({endpoint['endpoint']})")

if __name__ == "__main__":
    initialize_database()