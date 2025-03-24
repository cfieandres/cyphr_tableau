/**
 * Utility functions for working with the AI Server API
 */

/**
 * Base URL for API requests, defaulting to localhost:8000 if not specified
 */
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Fetch conversation history for a specific session
 * @param {string} sessionId - The session ID to fetch messages for
 * @returns {Promise<Array>} - Array of message objects
 */
export const fetchSessionMessages = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data.messages || [];
  } catch (error) {
    console.error('Error fetching session messages:', error);
    return [];
  }
};

/**
 * Process data through the routing endpoint
 * @param {string} taskType - Type of analysis to perform (analyze, summarize, general)
 * @param {Object} data - Data to be processed
 * @param {string} formatType - Response format type (auto, bullet, paragraph, json, raw)
 * @param {string} [question] - Optional question for general task type
 * @param {string} [sessionId] - Optional session ID for conversation context
 * @returns {Promise<Object>} - API response
 */
export const processData = async (taskType, data, formatType = 'auto', question = null, sessionId = null) => {
  try {
    // Format data as needed (convert to JSON string if it's an object)
    const dataString = typeof data === 'string' ? data : JSON.stringify(data);
    
    // Prepare request body
    const requestBody = {
      data: dataString,
      task_type: taskType,
      format_type: formatType
    };
    
    // Add question if provided
    if (question) {
      requestBody.question = question;
    }
    
    // Add session ID if provided
    if (sessionId) {
      requestBody.session_id = sessionId;
    }
    
    // Make the API request
    const response = await fetch(`${API_BASE_URL}/route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error processing data with AI:', error);
    throw error;
  }
};

/**
 * Send data directly to a specific endpoint
 * @param {string} endpoint - Endpoint to call (analytics, summarization, general)
 * @param {Object} data - Data to be processed
 * @param {string} formatType - Response format type (auto, bullet, paragraph, json, raw)
 * @returns {Promise<Object>} - API response
 */
export const callDirectEndpoint = async (endpoint, data, formatType = 'auto') => {
  try {
    // Format data as needed (convert to JSON string if it's an object)
    const dataString = typeof data === 'string' ? data : JSON.stringify(data);
    
    // Make the API request
    const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data: dataString,
        format_type: formatType
      }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`Error calling ${endpoint} endpoint:`, error);
    throw error;
  }
};

/**
 * Check if the API server is healthy
 * @returns {Promise<boolean>} - True if API server is healthy
 */
export const checkApiHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      return false;
    }
    
    const data = await response.json();
    return data.status === 'healthy';
  } catch (error) {
    console.error('Error checking API health:', error);
    return false;
  }
};

/**
 * Get information about available API endpoints
 * @returns {Promise<Array>} - Array of endpoint objects with metadata
 */
export const getApiEndpoints = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/endpoints`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data.endpoints || [];
  } catch (error) {
    console.error('Error fetching API endpoints:', error);
    // Return empty array as fallback
    return [];
  }
};