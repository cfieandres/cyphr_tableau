import sqlite3
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """SQLite database manager for the cyphr AI Extension."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        if db_path is None:
            # Default to a database file in the database directory
            self.db_path = os.path.join(
                Path(__file__).resolve().parent, 
                "cyphr.db"
            )
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Log the database path
            logger.info(f"Using database at: {self.db_path}")
        else:
            self.db_path = db_path
            logger.info(f"Using custom database path: {self.db_path}")
            
        self.connection = None
        self._initialize_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection, creating it if necessary."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Configure connection to return rows as dictionaries
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def _initialize_db(self):
        """Initialize the database schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create endpoints table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS endpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT UNIQUE NOT NULL,
            agent_id TEXT NOT NULL,
            instructions TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            indicators TEXT,
            priority INTEGER DEFAULT 100,
            model TEXT DEFAULT 'claude-3-5-sonnet',
            temperature REAL DEFAULT 0.7,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create request logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            selected_endpoint TEXT,
            prompt_data TEXT,
            response TEXT,
            execution_time_ms INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            model TEXT,
            status TEXT,
            client_ip TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        ''')
        
        # Create session messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        ''')
        
        # Create triggers for updated_at timestamps
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_endpoint_timestamp 
        AFTER UPDATE ON endpoints
        FOR EACH ROW
        BEGIN
            UPDATE endpoints SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        ''')
        
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_session_timestamp 
        AFTER UPDATE ON sessions
        FOR EACH ROW
        BEGIN
            UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
        ''')
        
        # Create index for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_endpoint ON request_logs(endpoint)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON request_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_messages ON session_messages(session_id)')
        
        conn.commit()
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    # Endpoint management methods
    def get_endpoint(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a specific endpoint.
        
        Args:
            endpoint: The endpoint to get configuration for
            
        Returns:
            The endpoint configuration or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM endpoints WHERE endpoint = ?", 
            (endpoint,)
        )
        
        row = cursor.fetchone()
        if row:
            # Parse the indicators JSON field
            endpoint_data = dict(row)
            try:
                endpoint_data['indicators'] = json.loads(endpoint_data['indicators'])
            except (json.JSONDecodeError, TypeError):
                endpoint_data['indicators'] = []
            return endpoint_data
        return None
    
    def get_all_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get all endpoint configurations.
        
        Returns:
            List of all endpoint configurations
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM endpoints ORDER BY priority ASC")
        
        endpoints = []
        for row in cursor.fetchall():
            endpoint_data = dict(row)
            try:
                endpoint_data['indicators'] = json.loads(endpoint_data['indicators'])
            except (json.JSONDecodeError, TypeError):
                endpoint_data['indicators'] = []
            endpoints.append(endpoint_data)
        
        return endpoints
    
    def add_or_update_endpoint(self, 
        endpoint: str, 
        agent_id: str, 
        instructions: str,
        name: str = "",
        description: str = "",
        indicators: List[str] = None,
        priority: int = 100,
        model: str = "claude-3-5-sonnet", 
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Add or update configuration for an endpoint.
        
        Args:
            endpoint: The endpoint path (e.g., "/analytics")
            agent_id: Identifier for the agent
            instructions: Instructions for the agent
            name: Display name for the endpoint
            description: Description of what the endpoint does
            indicators: List of keywords that suggest this endpoint should be used
            priority: Priority order (lower numbers have higher priority)
            model: The AI model to use (any model supported by Snowflake Cortex)
            temperature: The temperature parameter (0.0-1.0, controls randomness)
            
        Returns:
            The updated endpoint configuration
        """
        # Use default name if not provided
        if not name:
            name = endpoint.strip('/').capitalize()
            
        # Use instructions as description if not provided
        if not description:
            description = instructions.split('.')[0] + '.'
            
        # Initialize indicators if None
        if indicators is None:
            indicators = []
            
        # Convert indicators to JSON string
        indicators_json = json.dumps(indicators)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if the endpoint already exists
        cursor.execute(
            "SELECT id FROM endpoints WHERE endpoint = ?", 
            (endpoint,)
        )
        
        if cursor.fetchone():
            # Update existing endpoint
            cursor.execute("""
            UPDATE endpoints SET 
                agent_id = ?,
                instructions = ?,
                name = ?,
                description = ?,
                indicators = ?,
                priority = ?,
                model = ?,
                temperature = ?
            WHERE endpoint = ?
            """, (
                agent_id, instructions, name, description, indicators_json,
                priority, model, temperature, endpoint
            ))
        else:
            # Insert new endpoint
            cursor.execute("""
            INSERT INTO endpoints (
                endpoint, agent_id, instructions, name, description, 
                indicators, priority, model, temperature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                endpoint, agent_id, instructions, name, description,
                indicators_json, priority, model, temperature
            ))
        
        conn.commit()
        
        # Return the updated endpoint
        return self.get_endpoint(endpoint)
    
    def delete_endpoint(self, endpoint: str) -> bool:
        """
        Delete the configuration for an endpoint.
        
        Args:
            endpoint: The endpoint to delete configuration for
            
        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM endpoints WHERE endpoint = ?", 
            (endpoint,)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        
        return deleted
    
    # Request logging methods
    def log_request(self,
        endpoint: str,
        prompt_data: str = "",
        response: str = "",
        selected_endpoint: Optional[str] = None,
        execution_time_ms: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: Optional[str] = None,
        status: str = "success",
        client_ip: Optional[str] = None
    ) -> int:
        """
        Log a request to the database.
        
        Args:
            endpoint: The API endpoint that was called
            prompt_data: The data sent in the request
            response: The response returned
            selected_endpoint: The endpoint that was actually used (for routing)
            execution_time_ms: The execution time in milliseconds
            input_tokens: The number of input tokens
            output_tokens: The number of output tokens
            model: The model used for processing
            status: The status of the request (success/error)
            client_ip: The client IP address
            
        Returns:
            The ID of the logged request
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO request_logs (
            endpoint, prompt_data, response, selected_endpoint,
            execution_time_ms, input_tokens, output_tokens,
            model, status, client_ip
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            endpoint, prompt_data, response, selected_endpoint,
            execution_time_ms, input_tokens, output_tokens,
            model, status, client_ip
        ))
        
        log_id = cursor.lastrowid
        conn.commit()
        
        return log_id
    
    def get_logs(self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        endpoint: Optional[str] = None,
        selected_endpoint: Optional[str] = None,
        model: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get request logs with optional filtering.
        
        Args:
            limit: Maximum number of logs to return
            offset: Offset for pagination
            start_date: Start date for filtering (ISO format)
            end_date: End date for filtering (ISO format)
            endpoint: Filter by endpoint
            selected_endpoint: Filter by selected endpoint
            model: Filter by model
            status: Filter by status
            
        Returns:
            List of log entries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM request_logs WHERE 1=1"
        params = []
        
        # Add filters
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        if endpoint:
            query += " AND endpoint = ?"
            params.append(endpoint)
        if selected_endpoint:
            query += " AND selected_endpoint = ?"
            params.append(selected_endpoint)
        if model:
            query += " AND model = ?"
            params.append(model)
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific log entry by ID.
        
        Args:
            log_id: The ID of the log entry to retrieve
            
        Returns:
            The log entry or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM request_logs WHERE id = ?", 
            (log_id,)
        )
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_request_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the logged requests.
        
        Returns:
            Dictionary containing statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {
            "total_requests": 0,
            "total_success": 0,
            "total_errors": 0,
            "avg_execution_time": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "endpoint_usage": [],
            "selected_endpoint_usage": [],
            "model_usage": []
        }
        
        # Get total counts and averages
        cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as total_success,
            SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as total_errors,
            AVG(execution_time_ms) as avg_execution_time,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens
        FROM request_logs
        """)
        
        row = cursor.fetchone()
        if row:
            stats.update({
                "total_requests": row["total_requests"],
                "total_success": row["total_success"],
                "total_errors": row["total_errors"],
                "avg_execution_time": row["avg_execution_time"] or 0,
                "total_input_tokens": row["total_input_tokens"] or 0,
                "total_output_tokens": row["total_output_tokens"] or 0
            })
        
        # Get endpoint usage
        cursor.execute("""
        SELECT endpoint, COUNT(*) as count
        FROM request_logs
        GROUP BY endpoint
        ORDER BY count DESC
        """)
        
        stats["endpoint_usage"] = [dict(row) for row in cursor.fetchall()]
        
        # Get selected endpoint usage
        cursor.execute("""
        SELECT selected_endpoint, COUNT(*) as count
        FROM request_logs
        WHERE selected_endpoint IS NOT NULL
        GROUP BY selected_endpoint
        ORDER BY count DESC
        """)
        
        stats["selected_endpoint_usage"] = [dict(row) for row in cursor.fetchall()]
        
        # Get model usage
        cursor.execute("""
        SELECT model, COUNT(*) as count
        FROM request_logs
        WHERE model IS NOT NULL
        GROUP BY model
        ORDER BY count DESC
        """)
        
        stats["model_usage"] = [dict(row) for row in cursor.fetchall()]
        
        return stats
    
    def clear_logs(self, days_to_keep: int = 30) -> int:
        """
        Clear logs older than the specified number of days.
        
        Args:
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of logs deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM request_logs WHERE timestamp < datetime('now', ?)",
            (f"-{days_to_keep} days",)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        return deleted_count
    
    # Session management methods
    def get_or_create_session(self, session_id: Optional[str] = None, metadata: Optional[Dict] = None) -> Tuple[Dict[str, Any], bool]:
        """
        Get or create a session.
        
        Args:
            session_id: The session ID (optional, will generate if not provided)
            metadata: Additional metadata for the session (optional)
            
        Returns:
            Tuple containing the session data and a flag indicating if it was created
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        created = False
        
        if not session_id:
            # Generate a new session ID
            import uuid
            session_id = str(uuid.uuid4())
            created = True
        
        # Check if the session exists
        cursor.execute(
            "SELECT * FROM sessions WHERE id = ?", 
            (session_id,)
        )
        
        row = cursor.fetchone()
        
        if row:
            # Update last_active timestamp
            cursor.execute(
                "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,)
            )
            session_data = dict(row)
            
            # Parse metadata JSON
            try:
                session_data['metadata'] = json.loads(session_data['metadata'])
            except (json.JSONDecodeError, TypeError):
                session_data['metadata'] = {}
                
        else:
            # Create new session
            metadata_json = json.dumps(metadata or {})
            
            cursor.execute(
                "INSERT INTO sessions (id, metadata) VALUES (?, ?)",
                (session_id, metadata_json)
            )
            
            session_data = {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            created = True
        
        conn.commit()
        
        return session_data, created
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            The session data or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM sessions WHERE id = ?", 
            (session_id,)
        )
        
        row = cursor.fetchone()
        if row:
            session_data = dict(row)
            try:
                session_data['metadata'] = json.loads(session_data['metadata'])
            except (json.JSONDecodeError, TypeError):
                session_data['metadata'] = {}
            return session_data
        return None
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update the metadata for a session.
        
        Args:
            session_id: The session ID
            metadata: The new metadata
            
        Returns:
            True if updated, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata)
        
        cursor.execute(
            "UPDATE sessions SET metadata = ? WHERE id = ?",
            (metadata_json, session_id)
        )
        
        updated = cursor.rowcount > 0
        conn.commit()
        
        return updated
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM sessions WHERE id = ?", 
            (session_id,)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        
        return deleted
    
    def cleanup_expired_sessions(self, days_inactive: int = 7) -> int:
        """
        Clean up sessions that have been inactive for a specified number of days.
        
        Args:
            days_inactive: Number of days of inactivity before cleanup
            
        Returns:
            Number of sessions deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM sessions WHERE last_active < datetime('now', ?)",
            (f"-{days_inactive} days",)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        return deleted_count
    
    def add_message(self, session_id: str, role: str, content: str) -> int:
        """
        Add a message to a session.
        
        Args:
            session_id: The session ID
            role: The role of the message sender (user/assistant)
            content: The message content
            
        Returns:
            The ID of the added message
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO session_messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        
        message_id = cursor.lastrowid
        
        # Update session last_active timestamp
        cursor.execute(
            "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,)
        )
        
        conn.commit()
        
        return message_id
    
    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of messages
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM session_messages WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,)
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_prompt_context(self, session_id: str, max_messages: int = 10) -> str:
        """
        Get a formatted prompt context from the session history.
        
        Args:
            session_id: The session ID
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted conversation history for prompts
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT role, content FROM session_messages 
            WHERE session_id = ? 
            ORDER BY timestamp DESC LIMIT ?
            """,
            (session_id, max_messages)
        )
        
        # Get messages in reverse chronological order, then reverse to get chronological
        messages = list(reversed([dict(row) for row in cursor.fetchall()]))
        
        if not messages:
            return ""
        
        # Format the conversation history
        formatted_history = ""
        for msg in messages:
            role = "User" if msg["role"].lower() == "user" else "Assistant"
            formatted_history += f"{role}: {msg['content']}\n\n"
        
        return formatted_history.strip()

# Create a global instance for easy import elsewhere
db = Database()

# Example usage
if __name__ == "__main__":
    # Add default endpoints
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
    
    # Print all endpoints
    print("All endpoints:")
    for endpoint in db.get_all_endpoints():
        print(f"- {endpoint['name']} ({endpoint['endpoint']})")