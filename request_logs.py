"""
Request logging and monitoring module for the cyphr AI Extension.

This module provides functionality to log and track API requests,
token usage, and performance metrics.
"""

import json
import time
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Initialize the database path
DB_PATH = os.path.join(Path(__file__).resolve().parent, "request_logs.db")

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create the request logs table
    c.execute('''
    CREATE TABLE IF NOT EXISTS request_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        selected_endpoint TEXT,
        execution_time_ms INTEGER,
        input_tokens INTEGER,
        output_tokens INTEGER,
        model TEXT,
        prompt_data TEXT,
        response TEXT,
        status TEXT,
        client_ip TEXT,
        user_id TEXT,
        metadata TEXT
    )
    ''')
    
    # Create index for faster lookups
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON request_logs (timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_endpoint ON request_logs (endpoint)')
    
    conn.commit()
    conn.close()

def log_request(
    endpoint: str,
    prompt_data: str,
    response: str,
    selected_endpoint: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    model: Optional[str] = None,
    status: str = "success",
    client_ip: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Log an API request to the database.
    
    Args:
        endpoint: The endpoint that was called
        prompt_data: The data sent in the prompt
        response: The response from the model
        selected_endpoint: The endpoint that was used for processing (may differ from request endpoint)
        execution_time_ms: The execution time in milliseconds
        input_tokens: The number of input tokens
        output_tokens: The number of output tokens
        model: The model that was used
        status: The status of the request (success, error)
        client_ip: The client IP address
        user_id: The user ID
        metadata: Additional metadata to store
        
    Returns:
        The ID of the inserted log entry
    """
    # Ensure the database exists
    if not os.path.exists(DB_PATH):
        init_db()
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Convert metadata to JSON string if it exists
    metadata_json = json.dumps(metadata) if metadata else None
    
    # Prepare the timestamp
    timestamp = datetime.now().isoformat()
    
    # Insert the log entry
    c.execute('''
    INSERT INTO request_logs (
        timestamp, endpoint, selected_endpoint, execution_time_ms,
        input_tokens, output_tokens, model, prompt_data,
        response, status, client_ip, user_id, metadata
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp, endpoint, selected_endpoint, execution_time_ms,
        input_tokens, output_tokens, model, prompt_data,
        response, status, client_ip, user_id, metadata_json
    ))
    
    # Get the ID of the inserted row
    log_id = c.lastrowid
    
    # Commit the transaction
    conn.commit()
    conn.close()
    
    return log_id

def get_logs(
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    endpoint: Optional[str] = None,
    model: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get logs from the database with optional filtering.
    
    Args:
        limit: Maximum number of logs to return
        offset: Offset for pagination
        start_date: Start date for filtering (ISO format)
        end_date: End date for filtering (ISO format)
        endpoint: Filter by endpoint
        model: Filter by model
        status: Filter by status
        
    Returns:
        List of log entries as dictionaries
    """
    # Ensure the database exists
    if not os.path.exists(DB_PATH):
        init_db()
        return []
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()
    
    # Build the query
    query = "SELECT * FROM request_logs"
    params = []
    
    # Add filters
    conditions = []
    
    if start_date:
        conditions.append("timestamp >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("timestamp <= ?")
        params.append(end_date)
    
    if endpoint:
        conditions.append("endpoint = ?")
        params.append(endpoint)
    
    if model:
        conditions.append("model = ?")
        params.append(model)
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    # Add conditions to query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # Add order and limit
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    # Execute the query
    c.execute(query, params)
    
    # Fetch the results
    rows = c.fetchall()
    
    # Convert to list of dictionaries
    logs = []
    for row in rows:
        log = dict(row)
        # Parse metadata if it exists
        if log['metadata']:
            try:
                log['metadata'] = json.loads(log['metadata'])
            except:
                pass
        logs.append(log)
    
    conn.close()
    
    return logs

def get_log_by_id(log_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific log entry by ID.
    
    Args:
        log_id: The ID of the log entry to retrieve
        
    Returns:
        The log entry as a dictionary, or None if not found
    """
    # Ensure the database exists
    if not os.path.exists(DB_PATH):
        return None
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Execute the query
    c.execute("SELECT * FROM request_logs WHERE id = ?", (log_id,))
    
    # Fetch the result
    row = c.fetchone()
    
    # Convert to dictionary
    log = None
    if row:
        log = dict(row)
        # Parse metadata if it exists
        if log['metadata']:
            try:
                log['metadata'] = json.loads(log['metadata'])
            except:
                pass
    
    conn.close()
    
    return log

def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the logged requests.
    
    Returns:
        Dictionary containing statistics
    """
    # Ensure the database exists
    if not os.path.exists(DB_PATH):
        init_db()
        return {
            "total_requests": 0,
            "success_rate": 0,
            "average_execution_time_ms": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "requests_per_endpoint": {},
            "requests_per_model": {}
        }
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Calculate total requests
    c.execute("SELECT COUNT(*) FROM request_logs")
    total_requests = c.fetchone()[0]
    
    # Calculate success rate
    c.execute("SELECT COUNT(*) FROM request_logs WHERE status = 'success'")
    successful_requests = c.fetchone()[0]
    success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
    
    # Calculate average execution time
    c.execute("SELECT AVG(execution_time_ms) FROM request_logs WHERE execution_time_ms IS NOT NULL")
    average_execution_time = c.fetchone()[0] or 0
    
    # Calculate total tokens
    c.execute("SELECT SUM(input_tokens), SUM(output_tokens) FROM request_logs")
    token_counts = c.fetchone()
    total_input_tokens = token_counts[0] or 0
    total_output_tokens = token_counts[1] or 0
    
    # Get requests per endpoint
    c.execute("SELECT endpoint, COUNT(*) FROM request_logs GROUP BY endpoint")
    requests_per_endpoint = {row[0]: row[1] for row in c.fetchall()}
    
    # Get requests per model
    c.execute("SELECT model, COUNT(*) FROM request_logs WHERE model IS NOT NULL GROUP BY model")
    requests_per_model = {row[0]: row[1] for row in c.fetchall()}
    
    # Get requests per day for the last 30 days
    c.execute('''
    SELECT DATE(timestamp) as date, COUNT(*) FROM request_logs 
    WHERE timestamp >= DATE('now', '-30 days')
    GROUP BY DATE(timestamp)
    ORDER BY DATE(timestamp)
    ''')
    requests_per_day = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    
    return {
        "total_requests": total_requests,
        "success_rate": success_rate,
        "average_execution_time_ms": average_execution_time,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "requests_per_endpoint": requests_per_endpoint,
        "requests_per_model": requests_per_model,
        "requests_per_day": requests_per_day
    }

def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text.
    This is a very rough estimation based on words count.
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    # Simple estimation: 1 token ~= 4 characters (very rough)
    if not text:
        return 0
    return len(text) // 4

def clear_logs(days_to_keep: int = 30) -> int:
    """
    Clear logs older than the specified number of days.
    
    Args:
        days_to_keep: Number of days of logs to keep
        
    Returns:
        Number of logs deleted
    """
    # Ensure the database exists
    if not os.path.exists(DB_PATH):
        return 0
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Delete old logs
    c.execute(
        "DELETE FROM request_logs WHERE timestamp < datetime('now', ?)", 
        (f'-{days_to_keep} days',)
    )
    
    # Get the number of deleted rows
    deleted_count = c.rowcount
    
    # Commit the transaction
    conn.commit()
    conn.close()
    
    return deleted_count

# Initialize the database when the module is imported
init_db()

# Example usage
if __name__ == "__main__":
    # Log a sample request
    log_id = log_request(
        endpoint="/test",
        prompt_data="Sample prompt data",
        response="Sample response",
        execution_time_ms=150,
        input_tokens=100,
        output_tokens=50,
        model="test-model",
        metadata={"user_agent": "Test Agent"}
    )
    
    print(f"Logged request with ID: {log_id}")
    
    # Get the log
    log = get_log_by_id(log_id)
    print(f"Retrieved log: {log}")
    
    # Get stats
    stats = get_stats()
    print(f"Statistics: {stats}")