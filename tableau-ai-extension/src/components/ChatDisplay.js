import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import '../styles/ChatDisplay.css';

/**
 * ChatDisplay component for rendering AI responses with loading state
 * and question input capability
 * @param {Object} props - Component props
 * @param {string} props.response - LLM response text to display (legacy support)
 * @param {boolean} props.loading - Loading state indicator
 * @param {function} [props.onAskQuestion] - Function to call when a question is asked
 * @param {Array} [props.conversationHistory] - Array of message objects for conversation history
 * @returns {JSX.Element} - Rendered component
 */
const ChatDisplay = ({ 
  response, 
  loading, 
  onAskQuestion,
  conversationHistory = []
}) => {
  const [question, setQuestion] = useState('');
  
  // Format the response text using markdown parsing
  const formatResponse = (text) => {
    if (!text) return null;
    
    // Clean up extra newlines that might create unnecessary spacing
    const cleanText = text.replace(/\n\n\n+/g, '\n\n');
    
    return (
      <div className="formatted-response">
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={{
            // Style paragraphs with compact spacing
            p({node, children, ...props}) {
              // Check if paragraph is empty or just whitespace
              const childrenArray = React.Children.toArray(children);
              const isEmpty = childrenArray.length === 0 || 
                (childrenArray.length === 1 && typeof childrenArray[0] === 'string' && childrenArray[0].trim() === '');
              
              // Don't render empty paragraphs
              if (isEmpty) return null;
              
              return <p {...props}>{children}</p>;
            },
            
            // Style code blocks appropriately
            code({node, inline, className, children, ...props}) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline ? (
                <pre className="code-block">
                  <code className={className} {...props}>
                    {children}
                  </code>
                </pre>
              ) : (
                <code className="inline-code" {...props}>
                  {children}
                </code>
              );
            },
            
            // Style tables properly
            table({node, children, ...props}) {
              return (
                <div className="table-container">
                  <table {...props}>{children}</table>
                </div>
              );
            },
            
            // Make links open in a new tab
            a({node, href, children, ...props}) {
              return (
                <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                  {children}
                </a>
              );
            }
          }}
        >
          {cleanText}
        </ReactMarkdown>
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

  // Renders individual conversation messages
  const renderConversationMessage = (message) => {
    const isUser = message.sender === 'user';
    const isSystem = message.sender === 'system';
    
    const messageClasses = `message ${isUser ? 'user-message' : isSystem ? 'system-message' : 'assistant-message'}`;
    
    return (
      <div key={message.id} className={messageClasses}>
        {isSystem ? (
          <div className="message-content system-content">
            <em>{message.content}</em>
          </div>
        ) : (
          <div className="message-content">
            {message.sender === 'user' ? 
              <p>{message.content}</p> : 
              formatResponse(message.content)
            }
          </div>
        )}
      </div>
    );
  };
  
  // Create a ref for auto-scrolling
  const messagesEndRef = React.useRef(null);
  
  // Effect for scrolling to bottom of messages
  React.useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversationHistory]);
  
  return (
    <div className="chat-display">
      <div className="response-container">
        {loading ? (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>Processing your data...</p>
            <p className="loading-detail">Map visualizations and geographical data are excluded from analysis.</p>
          </div>
        ) : conversationHistory && conversationHistory.length > 0 ? (
          <div className="conversation-container">
            {conversationHistory.map(message => renderConversationMessage(message))}
            <div ref={messagesEndRef} />
          </div>
        ) : response ? (
          // Legacy support for direct response display
          <div className="response-text">
            {formatResponse(response)}
          </div>
        ) : (
          <div className="empty-state">
            <p>Click "Get Insights" to analyze this dashboard</p>
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