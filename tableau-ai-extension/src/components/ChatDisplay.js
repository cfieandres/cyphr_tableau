import React, { useState } from 'react';
import '../styles/ChatDisplay.css';

/**
 * ChatDisplay component for rendering AI responses with loading state
 * and question input capability
 * @param {Object} props - Component props
 * @param {string} props.response - LLM response text to display
 * @param {boolean} props.loading - Loading state indicator
 * @param {function} [props.onAskQuestion] - Function to call when a question is asked
 * @returns {JSX.Element} - Rendered component
 */
const ChatDisplay = ({ response, loading, onAskQuestion }) => {
  const [question, setQuestion] = useState('');
  
  // Format the response text to handle different content types
  const formatResponse = (text) => {
    if (!text) return null;
    
    // Check if response contains list items (starting with - or *)
    const containsList = /^[-*]\s.+/gm.test(text);
    
    // If the response contains a list, preserve formatting
    if (containsList) {
      return (
        <div className="formatted-response">
          {text.split('\n').map((line, i) => {
            // Check if line is a list item
            if (line.match(/^[-*]\s.+/)) {
              return (
                <div key={i} className="list-item">
                  {line}
                </div>
              );
            }
            // Otherwise, it's a regular paragraph
            return <p key={i}>{line}</p>;
          })}
        </div>
      );
    }
    
    // For regular text, just preserve line breaks
    return (
      <div className="formatted-response">
        {text.split('\n').map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
    );
  };

  /**
   * Handle form submission
   * @param {Event} e - Form submit event
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim() && onAskQuestion) {
      onAskQuestion(question);
      setQuestion('');
    }
  };

  return (
    <div className="chat-display">
      <div className="response-container">
        {loading ? (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>Processing your data...</p>
          </div>
        ) : response ? (
          <div className="response-text">
            {formatResponse(response)}
          </div>
        ) : (
          <div className="empty-state">
            <p>Click "Get Insights" to analyze all data in this dashboard</p>
          </div>
        )}
      </div>
      
      {onAskQuestion && (
        <div className="question-container">
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              className="question-input"
              placeholder="Ask a question about this data..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
            />
            <button 
              type="submit" 
              className="question-button"
              disabled={loading || !question.trim()}
            >
              Ask
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default ChatDisplay;