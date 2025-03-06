from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path
from pydantic import BaseModel

class AgentSettings(BaseModel):
    """Model for agent configuration settings."""
    endpoint: str
    agent_id: str
    instructions: str
    model: str = "claude-3-5-sonnet"
    temperature: float = 0.7

class AgentConfig:
    """
    Manages agent configurations for different endpoints.
    
    This class provides functionality to store, retrieve, and update
    agent configurations used for different AI processing endpoints.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the agent configuration manager.
        
        Args:
            config_file: Path to the configuration file. If None, uses a default path.
        """
        if config_file is None:
            # Default to a JSON file in the same directory as this script
            self.config_file = os.path.join(
                Path(__file__).resolve().parent, 
                "agent_configs.json"
            )
        else:
            self.config_file = config_file
        
        # Initialize empty configurations dictionary
        self.configs: Dict[str, AgentSettings] = {}
        
        # Load existing configurations if file exists
        self._load_configs()
        
        # Add default configurations if none exist
        if not self.configs:
            self._add_default_configs()
    
    def _load_configs(self):
        """Load configurations from the config file if it exists."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Convert the loaded data to AgentSettings objects
                for endpoint, settings in config_data.items():
                    self.configs[endpoint] = AgentSettings(**settings)
            except Exception as e:
                print(f"Error loading configurations: {e}")
    
    def _save_configs(self):
        """Save the current configurations to the config file."""
        try:
            # Convert AgentSettings objects to dictionaries
            config_dict = {
                endpoint: settings.dict() 
                for endpoint, settings in self.configs.items()
            }
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving configurations: {e}")
    
    def _add_default_configs(self):
        """Add default configurations for standard endpoints."""
        # Default configuration for analytics endpoint
        self.add_or_update_config(
            endpoint="/analytics",
            agent_id="analytics-agent",
            instructions="Analyze data and provide comprehensive insights with bullet points.",
            model="claude-3-5-sonnet",
            temperature=0.5
        )
        
        # Default configuration for summarization endpoint
        self.add_or_update_config(
            endpoint="/summarization",
            agent_id="summary-agent",
            instructions="Create a concise summary of the provided data, highlighting key points.",
            model="claude-3-5-sonnet",
            temperature=0.3
        )
        
        # Default configuration for general endpoint
        self.add_or_update_config(
            endpoint="/general",
            agent_id="general-agent",
            instructions="Respond helpfully to user queries about the data.",
            model="claude-3-5-sonnet",
            temperature=0.7
        )
    
    def get_config(self, endpoint: str) -> Optional[AgentSettings]:
        """
        Get the configuration for a specific endpoint.
        
        Args:
            endpoint: The endpoint to get configuration for
            
        Returns:
            The agent settings or None if not found
        """
        return self.configs.get(endpoint)
    
    def get_all_configs(self) -> Dict[str, AgentSettings]:
        """
        Get all configurations.
        
        Returns:
            Dictionary of all endpoint configurations
        """
        return self.configs
    
    def add_or_update_config(
        self, 
        endpoint: str, 
        agent_id: str, 
        instructions: str, 
        model: str = "claude-3-5-sonnet", 
        temperature: float = 0.7
    ) -> AgentSettings:
        """
        Add or update configuration for an endpoint.
        
        Args:
            endpoint: The endpoint to configure
            agent_id: Identifier for the agent
            instructions: Instructions for the agent
            model: The model to use (default: "claude-3-5-sonnet")
            temperature: The temperature parameter (default: 0.7)
            
        Returns:
            The updated agent settings
        """
        # Create or update the configuration
        self.configs[endpoint] = AgentSettings(
            endpoint=endpoint,
            agent_id=agent_id,
            instructions=instructions,
            model=model,
            temperature=temperature
        )
        
        # Save the updated configurations
        self._save_configs()
        
        return self.configs[endpoint]
    
    def delete_config(self, endpoint: str) -> bool:
        """
        Delete the configuration for an endpoint.
        
        Args:
            endpoint: The endpoint to delete configuration for
            
        Returns:
            True if deleted, False if not found
        """
        if endpoint in self.configs:
            del self.configs[endpoint]
            self._save_configs()
            return True
        return False


# Example usage
if __name__ == "__main__":
    # Initialize the agent configuration
    config_manager = AgentConfig()
    
    # Get all configurations
    all_configs = config_manager.get_all_configs()
    
    # Print all configurations
    for endpoint, settings in all_configs.items():
        print(f"Endpoint: {endpoint}")
        print(f"  Agent ID: {settings.agent_id}")
        print(f"  Instructions: {settings.instructions}")
        print(f"  Model: {settings.model}")
        print(f"  Temperature: {settings.temperature}")
        print()