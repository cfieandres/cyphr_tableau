import React, { useState, useEffect } from 'react';
import ChatDisplay from './components/ChatDisplay';
import { getWorksheetData, getAllWorksheets } from './utils/tableauUtils';
import { processData, checkApiHealth, getApiEndpoints } from './utils/apiUtils';
import { API_BASE_URL } from './utils/apiUtils';
import './styles/ChatDisplay.css';
import './App.css';

/**
 * Main application component for the claire Tableau Extension
 * Manages API calls, data processing, and UI state
 */
function App() {
  // State management
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tableauData, setTableauData] = useState(null);
  const [worksheets, setWorksheets] = useState([]);
  const [apiConnected, setApiConnected] = useState(false);
  const [showQuestionInput, setShowQuestionInput] = useState(false);
  const [username, setUsername] = useState('');
  const [availableEndpoints, setAvailableEndpoints] = useState([]);
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [lastQuestion, setLastQuestion] = useState('');
  
  // Conversation history state
  const [conversationHistory, setConversationHistory] = useState([]);
  
  // Session state for maintaining conversation history
  const [sessionId, setSessionId] = useState(null);

  // Initialize Tableau Extension API and create a session
  useEffect(() => {
    initializeTableauExtension();
    checkApiConnection();
    
    // Create a conversation session if we don't have one yet
    if (!sessionId) {
      createSession();
    }
  }, []);
  
  // Load conversation history when sessionId changes
  useEffect(() => {
    if (sessionId) {
      loadSessionConversation(sessionId);
    }
  }, [sessionId]);

  // Enable question input by default
  useEffect(() => {
    setShowQuestionInput(true);
  }, []);

  /**
   * Check if the API server is connected and get available endpoints
   */
  const checkApiConnection = async () => {
    try {
      const isHealthy = await checkApiHealth();
      setApiConnected(isHealthy);
      
      if (isHealthy) {
        // Fetch available endpoints from the API
        try {
          const endpoints = await getApiEndpoints();
          setAvailableEndpoints(endpoints);
          console.log('Available endpoints:', endpoints);
        } catch (endpointError) {
          console.error('Error fetching endpoints:', endpointError);
        }
      } else {
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
      
      // Get current username if available
      try {
        if (window.tableau.extensions.environment && window.tableau.extensions.environment.currentUser) {
          setUsername(window.tableau.extensions.environment.currentUser.username || '');
        }
      } catch (userError) {
        console.log('Could not get username:', userError);
      }
      
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
        processingNotes: ['All geographical data and map visualizations have been excluded from analysis'],
        excludedWorksheets: [],
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
      
      // Add results to the combined data, handling excluded map worksheets
      worksheetResults.forEach(result => {
        if (!result.data) return;
        
        // Check if this worksheet was excluded (map visualization)
        if (result.data.excluded) {
          // Add to the excluded list
          combinedData.excludedWorksheets.push({
            name: result.name,
            reason: result.data.note || "Geographical data excluded"
          });
          console.log(`Excluded worksheet from payload: ${result.name}`);
        } else {
          // Add to the regular worksheets
          combinedData.worksheets.push({
            name: result.name,
            data: result.data
          });
        }
      });
      
      // Check if we got any usable data 
      if (combinedData.worksheets.length === 0) {
        // Check if we have excluded worksheets but no regular worksheets
        if (combinedData.excludedWorksheets && combinedData.excludedWorksheets.length > 0) {
          // All worksheets were excluded due to geographical data
          throw new Error('All worksheets contain geographical data and were excluded from analysis');
        } else {
          throw new Error('Could not fetch data from any worksheet');
        }
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
   * Create a new session for conversation history
   */
  const createSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        console.log(`Created new conversation session: ${data.session_id}`);
        
        // Clear conversation history for the new session
        setConversationHistory([]);
      } else {
        console.error('Failed to create session');
      }
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };
  
  /**
   * Load conversation history for a session
   * @param {string} sessionId - The session ID to load history for
   */
  const loadSessionConversation = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log(`Loaded session with ${data.message_count} messages`);
        
        // Convert the message format for our UI
        const messages = data.messages.map(msg => ({
          id: new Date(msg.timestamp).getTime().toString(),
          content: msg.content,
          sender: msg.role === 'user' ? 'user' : 'assistant',
          timestamp: new Date(msg.timestamp)
        }));
        
        setConversationHistory(messages);
      } else if (response.status === 404) {
        // Session not found, create a new one
        console.log('Session not found, creating new session');
        await createSession();
      } else {
        console.error('Failed to load session messages');
      }
    } catch (error) {
      console.error('Error loading session messages:', error);
    }
  };

  /**
   * Process the data with AI
   * @param {string} taskType - Type of task (analyze, summarize, general)
   * @param {Object} data - Data to process
   * @param {string} [question] - Optional question for 'general' task type
   * @returns {Object} - The API response
   */
  const processDataWithAI = async (taskType, data, question = null) => {
    if (!data) {
      setError('No data available to process');
      return null;
    }
    
    if (!apiConnected) {
      await checkApiConnection();
      if (!apiConnected) {
        return null;
      }
    }
    
    // Ensure we have a session ID for conversation history
    if (!sessionId && question) {
      await createSession();
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Call the API to process the data, passing the question and session ID if provided
      const result = await processData(taskType, data, 'auto', question, sessionId);
      
      // Update the response
      setResponse(result.response);
      
      // Update the selected endpoint if it was returned
      if (result.selected_endpoint) {
        setSelectedEndpoint(result.selected_endpoint);
        console.log(`Server selected endpoint: ${result.selected_endpoint}`);
      } else {
        setSelectedEndpoint(null);
      }
      
      // Update session ID if it was returned
      if (result.session_id && result.session_id !== sessionId) {
        setSessionId(result.session_id);
        console.log(`Updated session ID: ${result.session_id}`);
      }
      
      return result;
    } catch (error) {
      console.error('Error processing data with AI:', error);
      setError(`Failed to process data: ${error.message}`);
      return null;
    } finally {
      setLoading(false);
    }
  };


  /**
   * Handle button click to process data
   */
  const handleProcessClick = async () => {
    const data = await fetchTableauData();
    if (data) {
      // Let the backend determine the task type based on dashboard data
      const result = await processDataWithAI('auto', data);
      
      if (result && result.response) {
        // Add the system-generated response to conversation history
        const newMessage = {
          id: Date.now().toString(),
          content: result.response,
          sender: 'assistant',
          timestamp: new Date()
        };
        
        // If this is the first message (initial insights), create a synthetic system message
        if (conversationHistory.length === 0) {
          const systemPrompt = {
            id: (Date.now() - 1).toString(),
            content: 'Get insights from this dashboard',
            sender: 'system',
            timestamp: new Date()
          };
          setConversationHistory(prev => [...prev, systemPrompt, newMessage]);
        } else {
          setConversationHistory(prev => [...prev, newMessage]);
        }
      }
    }
  };

  /**
   * Handle user question submission
   * @param {string} question - The question asked by the user
   */
  const handleAskQuestion = async (question) => {
    // Validate the question
    if (!question || question.trim() === '') {
      console.error('Empty question submitted');
      setError('Please enter a question before submitting');
      return;
    }
    
    console.log(`User asked: "${question}"`);
    
    // Save the question for display
    setLastQuestion(question);
    
    // Clear any previous errors and set loading state
    setError(null);
    
    // Add user question to conversation history immediately
    const userMessage = {
      id: Date.now().toString(),
      content: question,
      sender: 'user',
      timestamp: new Date()
    };
    
    setConversationHistory(prev => [...prev, userMessage]);
    
    // Get data if needed
    const data = tableauData || await fetchTableauData();
    if (data) {
      // Pass question but let backend determine task type
      // The 'auto' task type should trigger question handling on the backend
      const result = await processDataWithAI('auto', data, question);
      
      if (result && result.response) {
        // Add the assistant's response to conversation history
        const assistantMessage = {
          id: (Date.now() + 100).toString(), // Ensure unique ID
          content: result.response,
          sender: 'assistant',
          timestamp: new Date()
        };
        
        setConversationHistory(prev => [...prev, assistantMessage]);
      }
    } else {
      setError('Unable to fetch data to answer your question');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>claire</h1>
        <div className="subtitle">AI-powered insights for Tableau</div>
        {username && <div className="username">Hi, {username} 👋</div>}
      </header>
      
      <main>
        <div className="controls">          
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
          onAskQuestion={handleAskQuestion}
          conversationHistory={conversationHistory}
        />
      </main>
      
      <footer className="App-footer">
        <div className="status-indicator">
          <span className={`status-dot ${apiConnected ? 'connected' : 'disconnected'}`}></span>
          <span className="status-text">
            {apiConnected ? 'Connected to AI server' : 'Not connected to AI server'}
          </span>
          {selectedEndpoint && (
            <span className="endpoint-indicator">
              Using: {selectedEndpoint}
            </span>
          )}
          {sessionId && (
            <span className="session-indicator">
              Session Active
            </span>
          )}
          {lastQuestion && selectedEndpoint === 'general' && (
            <span className="question-indicator">
              Q: "{lastQuestion.length > 30 ? lastQuestion.substring(0, 30) + '...' : lastQuestion}"
            </span>
          )}
        </div>
      </footer>
    </div>
  );
}

export default App;