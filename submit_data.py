from fetch_tableau_data import TableauDataFetcher
from typing import Dict, Any, Optional
import json

class DataSubmitter:
    """
    Handles the submission of data from Tableau to the AI processing endpoints.
    This class is responsible for fetching data from Tableau and preparing it for AI processing.
    """
    
    def __init__(self):
        """Initialize the DataSubmitter with a TableauDataFetcher."""
        self.data_fetcher = TableauDataFetcher()
    
    def fetch_and_prepare_data(self, view_id: str) -> str:
        """
        Fetch data from a Tableau view and prepare it for AI processing.
        
        Args:
            view_id: The ID of the Tableau view to fetch data from
            
        Returns:
            A string representation of the data suitable for AI processing
        """
        # Fetch the data from Tableau
        raw_data = self.data_fetcher.fetch_view_data(view_id)
        
        # Check if there was an error
        if "error" in raw_data:
            return f"Error fetching data: {raw_data['error']}"
        
        # Extract and format the data
        # This is a simplified example - in a real application, you would
        # need to handle the specific structure of your Tableau data
        formatted_data = self._extract_value_fields(raw_data)
        
        # Convert to a string representation
        if isinstance(formatted_data, dict) or isinstance(formatted_data, list):
            return json.dumps(formatted_data, indent=2)
        else:
            return str(formatted_data)
    
    def _extract_value_fields(self, data: Dict[str, Any]) -> Any:
        """
        Extract the 'value' fields from the data.
        
        Args:
            data: The data to extract values from
            
        Returns:
            The extracted values, which could be a dictionary, list, or string
        """
        # This is a simplified example - you would need to adapt this to
        # your specific Tableau data structure
        
        # Check if data has a 'data' field
        if 'data' in data:
            return data['data']
        
        # Check if data has a 'values' field
        if 'values' in data:
            return data['values']
        
        # If no specific field is found, return the data as is
        return data


def submit_for_processing(view_id: str) -> str:
    """
    Fetch data from Tableau and prepare it for AI processing.
    
    Args:
        view_id: The ID of the Tableau view to fetch data from
        
    Returns:
        A string representation of the data suitable for AI processing
    """
    submitter = DataSubmitter()
    return submitter.fetch_and_prepare_data(view_id)


# Example usage
if __name__ == "__main__":
    # Example view ID - would be replaced with a real ID in production
    example_view_id = "sample-view-id"
    
    # Submit the data
    data_string = submit_for_processing(example_view_id)
    
    # Print the result
    print(f"Prepared data for AI processing:\n{data_string}")