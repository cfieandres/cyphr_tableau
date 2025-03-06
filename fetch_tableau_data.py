import requests
import json
import os
import logging
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)

class TableauDataFetcher:
    """Handles data retrieval from Tableau's REST API."""
    
    def __init__(self):
        """Initialize the TableauDataFetcher."""
        # Get base URL and remove trailing slashes if present
        self.base_url = os.getenv("TABLEAU_API_BASE_URL", "").rstrip('/')
        
        # If the base URL already includes the API version, extract it
        if '/api/' in self.base_url:
            # Extract API version from the URL
            parts = self.base_url.split('/api/')
            if len(parts) > 1 and parts[1]:
                self.api_version = parts[1].split('/')[0]
                # Trim the API version from the base URL
                self.base_url = parts[0]
            else:
                self.api_version = "3.20"  # Default API version
        else:
            self.api_version = "3.20"  # Default API version
        
        logger.debug(f"Using Tableau API base URL: {self.base_url}")
        logger.debug(f"Using Tableau API version: {self.api_version}")
        
        self.auth_token = None
        self.site_id = os.getenv("TABLEAU_SITE_ID", "")
    
    def get_token(self, username: Optional[str] = None, password: Optional[str] = None,
                  token_name: Optional[str] = None, token_value: Optional[str] = None) -> str:
        """
        Authenticate with Tableau Server and get an auth token.
        
        This method supports two authentication methods:
        1. Personal Access Token (PAT) - preferred method
        2. Username and password - fallback method
        
        Args:
            username: Tableau Server username. If None, uses environment variable.
            password: Tableau Server password. If None, uses environment variable.
            token_name: Tableau PAT name. If None, uses environment variable.
            token_value: Tableau PAT value. If None, uses environment variable.
            
        Returns:
            Authentication token for API calls
        """
        # Endpoint for authentication
        auth_url = f"{self.base_url}/api/{self.api_version}/auth/signin"
        
        # Headers for the request
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Determine authentication method - prefer PAT
        if not token_name:
            token_name = os.getenv("TABLEAU_API_TOKEN_NAME", "")
        
        if not token_value:
            token_value = os.getenv("TABLEAU_API_TOKEN_VALUE", "")
        
        # Check if we have PAT credentials
        use_pat = token_name and token_value
        
        if use_pat:
            # Use Personal Access Token
            payload = {
                "credentials": {
                    "personalAccessTokenName": token_name,
                    "personalAccessTokenSecret": token_value,
                    "site": {"contentUrl": self.site_id}
                }
            }
            logger.info(f"Authenticating with Personal Access Token: {token_name}")
        else:
            # Fallback to username/password
            if not username:
                username = os.getenv("TABLEAU_USERNAME", "")
            
            if not password:
                password = os.getenv("TABLEAU_PASSWORD", "")
            
            if not username or not password:
                logger.error("No authentication credentials provided")
                return ""
            
            payload = {
                "credentials": {
                    "name": username,
                    "password": password,
                    "site": {"contentUrl": self.site_id}
                }
            }
            logger.info(f"Authenticating with username: {username}")
        
        try:
            # Make the authentication request
            response = requests.post(auth_url, json=payload, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Parse the response
            auth_data = response.json()
            
            # Extract token and site id
            self.auth_token = auth_data["credentials"]["token"]
            self.site_id = auth_data["credentials"]["site"]["id"]
            
            # Print success message in debug mode
            if os.getenv("DEBUG", "false").lower() == "true":
                auth_method = "PAT" if use_pat else "username"
                logger.info(f"Successfully authenticated with {auth_method} to site {self.site_id}")
            
            return self.auth_token
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication error: {e}")
            return ""
    
    def _ensure_authenticated(self):
        """
        Ensure that we have a valid authentication token.
        If not, get a new token.
        """
        # If we don't have a token, get one
        if not self.auth_token:
            self.get_token()
            return
        
        # If we have a token, check if it's still valid
        try:
            # Make a simple request to check if the token is still valid
            # For example, get the current user's info
            headers = {
                "X-Tableau-Auth": self.auth_token,
                "Accept": "application/json"
            }
            
            user_url = f"{self.base_url}/api/{self.api_version}/sites/{self.site_id}/users/current"
            response = requests.get(user_url, headers=headers)
            
            # If the request was successful, the token is still valid
            if response.status_code == 200:
                return
            
            # If we get here, the token is invalid, so get a new one
            self.get_token()
            
        except requests.exceptions.RequestException:
            # If there was an error, get a new token
            self.get_token()
    
    def fetch_view_data(self, view_id: str) -> Dict[str, Any]:
        """
        Fetch data from a Tableau view.
        
        Args:
            view_id: The ID of the Tableau view to fetch data from
            
        Returns:
            Dictionary containing the data from the view
        """
        # Ensure we have a valid auth token
        self._ensure_authenticated()
        
        # Endpoint for view data
        data_url = f"{self.base_url}/api/{self.api_version}/sites/{self.site_id}/views/{view_id}/data"
        
        # Headers for the request
        headers = {
            "X-Tableau-Auth": self.auth_token,
            "Accept": "application/json"
        }
        
        try:
            # Make the request
            response = requests.get(data_url, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Parse the response
            return response.json()
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching view data: {e}"
            print(error_msg)
            
            # Check if it's an authentication error (401)
            if hasattr(e, 'response') and e.response and e.response.status_code == 401:
                # Try to get a new token and retry once
                self.auth_token = None  # Clear the token
                self._ensure_authenticated()  # Get a new token
                
                try:
                    # Retry the request with the new token
                    response = requests.get(data_url, headers={
                        "X-Tableau-Auth": self.auth_token,
                        "Accept": "application/json"
                    })
                    response.raise_for_status()
                    
                    # Parse the response
                    return response.json()
                except requests.exceptions.RequestException as retry_error:
                    print(f"Error retrying fetch view data: {retry_error}")
                    return {"error": str(retry_error)}
            
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Initialize the data fetcher
    fetcher = TableauDataFetcher()
    
    # Get auth token
    token = fetcher.get_token()
    
    if token:
        # Fetch data from a view (using a sample view ID)
        view_id = "sample-view-id"
        data = fetcher.fetch_view_data(view_id)
        
        # Print the data
        print(json.dumps(data, indent=2))