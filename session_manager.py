"""
Session management module for the cyphr AI Extension.

This module provides functionality to manage conversation sessions,
store message history, and maintain context between requests.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


class Message:
    """Class representing a message in a conversation."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """
        Initialize a message.
        
        Args:
            role: The role of the message sender (user or assistant)
            content: The message content
            timestamp: The message timestamp (defaults to current time)
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


class Session:
    """Class representing a user session with message history."""
    
    def __init__(self, session_id: str, max_history: int = 10):
        """
        Initialize a session.
        
        Args:
            session_id: The unique session identifier
            max_history: Maximum number of messages to keep in history
        """
        self.id = session_id
        self.max_history = max_history
        self.messages: List[Message] = []
        self.created_at = datetime.now()
        self.last_active = datetime.now()
    
    def add_message(self, role: str, content: str) -> Message:
        """
        Add a message to the session history.
        
        Args:
            role: The role of the message sender (user or assistant)
            content: The message content
            
        Returns:
            The added message
        """
        # Check if we need to trim history
        if len(self.messages) >= self.max_history * 2:  # Double because we count pairs
            # Remove the oldest messages to stay within max_history
            self.messages = self.messages[-(self.max_history * 2):]
        
        # Create new message
        message = Message(role, content)
        self.messages.append(message)
        self.last_active = datetime.now()
        
        return message
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in the session history as dictionaries."""
        return [message.to_dict() for message in self.messages]
    
    def get_prompt_context(self) -> str:
        """
        Get the conversation history formatted for Claude prompt context.
        
        Returns:
            Formatted conversation history
        """
        if not self.messages:
            return ""
        
        # Format as Claude conversation
        formatted_messages = []
        for message in self.messages:
            formatted_role = "Human" if message.role == "user" else "Assistant"
            formatted_messages.append(f"{formatted_role}: {message.content}")
        
        return "\n\n".join(formatted_messages)


class SessionManager:
    """Class for managing multiple user sessions."""
    
    def __init__(self, session_ttl: int = 86400):  # Default 24 hours
        """
        Initialize the session manager.
        
        Args:
            session_ttl: Time to live for sessions in seconds
        """
        self.sessions: Dict[str, Session] = {}
        self.session_ttl = session_ttl
    
    def create_session(self, session_id: Optional[str] = None) -> Session:
        """
        Create a new session.
        
        Args:
            session_id: Optional custom session ID
            
        Returns:
            The created session
        """
        # Generate a session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create a new session
        session = Session(session_id)
        self.sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            The session if found, None otherwise
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_active = datetime.now()
            return session
        return None
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> Tuple[Session, bool]:
        """
        Get a session by ID or create a new one if it doesn't exist.
        
        Args:
            session_id: The session ID
            
        Returns:
            Tuple of (session, was_created)
        """
        # If session_id is None or doesn't exist, create a new session
        if not session_id or session_id not in self.sessions:
            session = self.create_session(session_id)
            return session, True
        
        # Get existing session
        session = self.sessions[session_id]
        session.last_active = datetime.now()
        return session, False
    
    def add_message(self, session_id: str, role: str, content: str) -> Optional[Message]:
        """
        Add a message to a session.
        
        Args:
            session_id: The session ID
            role: The role of the message sender (user or assistant)
            content: The message content
            
        Returns:
            The added message if session exists, None otherwise
        """
        session = self.get_session(session_id)
        if session:
            return session.add_message(role, content)
        return None
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            Number of sessions removed
        """
        current_time = datetime.now()
        expired_ids = []
        
        # Identify expired sessions
        for session_id, session in self.sessions.items():
            time_since_active = (current_time - session.last_active).total_seconds()
            if time_since_active > self.session_ttl:
                expired_ids.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_ids:
            del self.sessions[session_id]
        
        return len(expired_ids)

# Create a singleton instance
session_manager = SessionManager()

# Example usage
if __name__ == "__main__":
    # Create a session
    session, created = session_manager.get_or_create_session()
    print(f"Created new session: {created}, ID: {session.id}")
    
    # Add messages
    session.add_message("user", "Hello, how are you?")
    session.add_message("assistant", "I'm doing well, thank you! How can I help you today?")
    session.add_message("user", "Can you analyze some data for me?")
    
    # Print the conversation context
    print("\nConversation context:")
    print(session.get_prompt_context())
    
    # Access the session using its ID
    retrieved_session = session_manager.get_session(session.id)
    print(f"\nRetrieved session: {retrieved_session.id}")
    print(f"Message count: {len(retrieved_session.messages)}")