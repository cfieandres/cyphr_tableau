/**
 * Tableau extensions embedding script
 * This script initializes the ChatDisplay component within Tableau
 * using the Extensions API
 */
import React from 'react';
import ReactDOM from 'react-dom';
import ChatDisplay from './components/ChatDisplay';

// Initialize the Tableau Extensions API
function initializeExtension() {
  try {
    // Wait for the Tableau Extensions API to be initialized
    tableau.extensions.initializeAsync().then(() => {
      console.log('Extension initialized');
      
      // Set up a sample response for testing
      const sampleResponse = "This is a sample response from the AI assistant. " +
        "It demonstrates how the chat display will appear when embedded in Tableau.";
      
      // Render the ChatDisplay component
      const container = document.getElementById('root');
      ReactDOM.render(
        <ChatDisplay response={sampleResponse} />,
        container
      );
      
      // Add event listener for dashboard changes if needed
      // tableau.extensions.dashboardContent.dashboard.worksheets.forEach((worksheet) => {
      //   worksheet.addEventListener(tableau.TableauEventType.FilterChanged, handleDataUpdate);
      // });
    });
  } catch (error) {
    console.error('Error initializing extension:', error);
  }
}

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', initializeExtension);

/**
 * Example function to handle data updates (not implemented yet)
 */
// function handleDataUpdate() {
//   // Get data from Tableau and update the response
//   // This will be implemented in later milestones
// }

export default initializeExtension;