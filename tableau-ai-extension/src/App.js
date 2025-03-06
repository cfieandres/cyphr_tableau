import React, { useState, useEffect } from 'react';
import ChatDisplay from './components/ChatDisplay';
import { getWorksheetData, getAllWorksheets } from './utils/tableauUtils';
import { processData, checkApiHealth } from './utils/apiUtils';
import './App.css';

/**
 * Main application component for the cyphr Tableau Extension
 * Manages API calls, data processing, and UI state
 */
function App() {
  // State management
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tableauData, setTableauData] = useState(null);
  const [worksheets, setWorksheets] = useState([]);
  const [selectedTaskType, setSelectedTaskType] = useState('analyze');
  const [apiConnected, setApiConnected] = useState(false);
  const [showQuestionInput, setShowQuestionInput] = useState(false);

  // Initialize Tableau Extension API
  useEffect(() => {
    initializeTableauExtension();
    checkApiConnection();
  }, []);

  // Show question input when task type is 'general'
  useEffect(() => {
    setShowQuestionInput(selectedTaskType === 'general');
  }, [selectedTaskType]);

  /**
   * Check if the API server is connected
   */
  const checkApiConnection = async () => {
    try {
      const isHealthy = await checkApiHealth();
      setApiConnected(isHealthy);
      
      if (!isHealthy) {
        setError('Cannot connect to the AI API server. Please check that the server is running.');
      }
    } catch (error) {
      console.error('API connection check failed:', error);
      setApiConnected(false);
      setError('Cannot connect to the AI API server. Please check that the server is running.');
    }
  };

  /**
   * Initialize the Tableau Extensions API
   */
  const initializeTableauExtension = async () => {
    try {
      // Wait for the Tableau Extensions API to be initialized
      await window.tableau.extensions.initializeAsync();
      console.log('Extension initialized');
      
      // Get list of worksheets
      const worksheetsList = getAllWorksheets();
      
      setWorksheets(worksheetsList);
      
      // Set up event listeners for filtering and selection changes
      worksheetsList.forEach(worksheet => {
        worksheet.addEventListener(
          window.tableau.TableauEventType.FilterChanged, 
          handleDataUpdate
        );
        worksheet.addEventListener(
          window.tableau.TableauEventType.MarkSelectionChanged, 
          handleDataUpdate
        );
      });
    } catch (error) {
      console.error('Error initializing extension:', error);
      setError('Failed to initialize Tableau extension. Please reload.');
    }
  };

  /**
   * Handle data updates from Tableau (filter changes, selection changes)
   */
  const handleDataUpdate = async () => {
    try {
      console.log('Data update triggered');
      // Automatically refresh data when user interacts with dashboard
      await fetchTableauData();
    } catch (error) {
      console.error('Error handling data update:', error);
    }
  };

  /**
   * Fetch data from all worksheets in the dashboard
   */
  const fetchTableauData = async () => {
    if (worksheets.length === 0) {
      setError('No worksheets available in this dashboard');
      return null;
    }
    
    try {
      setLoading(true);
      
      // Create a combined data object
      const combinedData = {
        dashboardName: window.tableau.extensions.dashboardContent.dashboard.name,
        worksheets: []
      };
      
      // Fetch data from all worksheets in parallel
      const worksheetDataPromises = worksheets.map(async (worksheet) => {
        try {
          const data = await getWorksheetData(worksheet, true);
          return {
            name: worksheet.name,
            data: data
          };
        } catch (error) {
          console.error(`Error fetching data from worksheet ${worksheet.name}:`, error);
          return {
            name: worksheet.name,
            error: `Failed to fetch data: ${error.message}`
          };
        }
      });
      
      // Wait for all data to be fetched
      const worksheetResults = await Promise.all(worksheetDataPromises);
      
      // Add successful results to the combined data
      worksheetResults.forEach(result => {
        if (result.data) {
          combinedData.worksheets.push({
            name: result.name,
            data: result.data
          });
        }
      });
      
      // Check if we got any data
      if (combinedData.worksheets.length === 0) {
        throw new Error('Could not fetch data from any worksheet');
      }
      
      setTableauData(combinedData);
      console.log('Combined Tableau data loaded:', combinedData);
      
      return combinedData;
    } catch (error) {
      console.error('Error fetching Tableau data:', error);
      setError('Failed to fetch data from worksheets');
      return null;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Process the data with AI
   * @param {string} taskType - Type of task (analyze, summarize, general)
   * @param {Object} data - Data to process
   * @param {string} [question] - Optional question for 'general' task type
   */
  const processDataWithAI = async (taskType, data, question = null) => {
    if (!data) {
      setError('No data available to process');
      return;
    }
    
    if (!apiConnected) {
      await checkApiConnection();
      if (!apiConnected) {
        return;
      }
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Call the API to process the data, passing the question if provided
      const result = await processData(taskType, data, 'auto', question);
      
      // Update the response
      setResponse(result.response);
    } catch (error) {
      console.error('Error processing data with AI:', error);
      setError(`Failed to process data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };


  /**
   * Handle task type selection change
   * @param {Object} event - Change event
   */
  const handleTaskTypeChange = (event) => {
    setSelectedTaskType(event.target.value);
    // Clear previous results when changing task type
    setResponse('');
  };

  /**
   * Handle button click to process data
   */
  const handleProcessClick = async () => {
    const data = await fetchTableauData();
    if (data) {
      await processDataWithAI(selectedTaskType, data);
    }
  };

  /**
   * Handle user question submission
   * @param {string} question - The question asked by the user
   */
  const handleAskQuestion = async (question) => {
    const data = tableauData || await fetchTableauData();
    if (data) {
      await processDataWithAI('general', data, question);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>cyphr</h1>
        <div className="subtitle">AI-powered insights for Tableau</div>
      </header>
      
      <main>
        <div className="controls">
          <div className="control-group">
            <label htmlFor="taskType">Task:</label>
            <select 
              id="taskType"
              value={selectedTaskType}
              onChange={handleTaskTypeChange}
            >
              <option value="analyze">Analyze Data</option>
              <option value="summarize">Summarize Data</option>
              <option value="general">Ask Question</option>
            </select>
          </div>
          
          <button 
            className="process-button"
            onClick={handleProcessClick}
            disabled={loading || worksheets.length === 0 || !apiConnected}
          >
            {loading ? 'Processing...' : 'Get Insights'}
          </button>
        </div>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        {!apiConnected && !error && (
          <div className="error-message">
            Cannot connect to the AI API server. Please check that the server is running.
          </div>
        )}
        
        <ChatDisplay 
          response={response} 
          loading={loading}
          onAskQuestion={showQuestionInput ? handleAskQuestion : null}
        />
      </main>
      
      <footer className="App-footer">
        <div className="status-indicator">
          <span className={`status-dot ${apiConnected ? 'connected' : 'disconnected'}`}></span>
          <span className="status-text">
            {apiConnected ? 'Connected to AI server' : 'Not connected to AI server'}
          </span>
        </div>
      </footer>
    </div>
  );
}

export default App;