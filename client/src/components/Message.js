import React from 'react';
import ReactMarkdown from 'react-markdown';
import '../styles/Message.css';  // We'll create this next

const Message = ({ 
  message, 
  onGetAnalysis, 
  onGetStrategy,
  isLoading,
  isLoadingStrategy,
  messagesWithAnalysis,
  onRegenerate,
  onCopy,
  onDownload,
  onFeedback 
}) => {
  console.log('Message component received:', message);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.assistant);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob([message.assistant], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = 'cicero-response.txt';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleFeedback = async (isPositive) => {
    try {
      await onFeedback(isPositive);
    } catch (err) {
      console.error('Error submitting feedback:', err);
    }
  };

  // Format the message content to separate different sections
  const formatMessageContent = (content) => {
    if (!content) return '';

    // Clean up the content first
    let cleanContent = content
      .replace(/\n{3,}/g, '\n\n') // Replace multiple newlines with double newlines
      .replace(/([0-9]+\.)\s*\n+/g, '$1 ') // Fix numbered list items that are split across lines
      .replace(/(\w+)-\s*\n(\w+)/g, '$1$2'); // Join hyphenated words that are split across lines

    console.log('Cleaned content:', cleanContent);

    // Split content into sections, but preserve formatting
    const sections = cleanContent.split(/(?=##\s*Legal Strategy|(?=\*\*In-Depth Legal Analysis:\*\*))/);
    
    return sections.map((section, index) => {
      // Handle Legal Strategy section
      if (section.match(/##\s*Legal Strategy/)) {
        const cleanedSection = section
          .replace(/##\s*Legal Strategy/, '')
          .trim();
        return (
          <div key={index} className="message-section strategy-section">
            <h2 className="section-title">Legal Strategy</h2>
            <ReactMarkdown>{cleanedSection}</ReactMarkdown>
          </div>
        );
      }
      
      // Handle References section
      else if (section.includes('References')) {
        const cleanedSection = section
          .replace(/References/, '')
          .trim();
        return (
          <div key={index} className="message-section references-section">
            <h3 className="section-title">Cicero</h3>
            <ReactMarkdown>{cleanedSection}</ReactMarkdown>
          </div>
        );
      }
      
      // Handle initial response
      else {
        const cleanedSection = section.trim();
        return (
          <div key={index} className="message-section initial-response">
            <ReactMarkdown components={{
              // Custom handling for list items to ensure proper formatting
              li: ({node, ...props}) => (
                <li className="custom-list-item" {...props} />
              ),
              // Ensure paragraphs are properly formatted
              p: ({node, ...props}) => (
                <p className="custom-paragraph" {...props} />
              )
            }}>
              {cleanedSection}
            </ReactMarkdown>
          </div>
        );
      }
    });
  };

  return (
    <div className="message-group">
      {/* User Message */}
      <div className="user-message">
        <div className="message-bubble">
          <strong>You:</strong> {message.user}
        </div>
      </div>

      {/* Assistant Message */}
      <div className="assistant-message">
        <div className="message-bubble">
          <div className="message-content">
            {formatMessageContent(message.assistant)}
          </div>
        </div>

        <div className="message-actions">
          <button className="action-button" title="Copy to clipboard" onClick={handleCopy}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" strokeWidth="2"/>
              <path d="M5 15H4C2.89543 15 2 14.1046 2 13V4C2 2.89543 2.89543 2 4 2H13C14.1046 2 15 2.89543 15 4V5" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>
          <button className="action-button" title="Download" onClick={handleDownload}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 4V16M12 16L7 11M12 16L17 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M4 20H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
          <button 
            className={`action-button ${message.response_liked === true ? 'active' : ''}`} 
            title="Like" 
            onClick={() => handleFeedback(true)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7 22H4C3.46957 22 2.96086 21.7893 2.58579 21.4142C2.21071 21.0391 2 20.5304 2 20V13C2 12.4696 2.21071 11.9609 2.58579 11.5858C2.96086 11.2107 3.46957 11 4 11H7M14 9V5C14 4.20435 13.6839 3.44129 13.1213 2.87868C12.5587 2.31607 11.7956 2 11 2L7 11V22H19.28C19.7623 22.0055 20.2304 21.8364 20.5979 21.524C20.9654 21.2116 21.2077 20.7769 21.28 20.3L22.66 11.3C22.7035 11.0134 22.6842 10.7207 22.6033 10.4423C22.5225 10.1638 22.3821 9.90629 22.1919 9.68751C22.0016 9.46873 21.7661 9.29393 21.5016 9.17522C21.2371 9.0565 20.9499 8.99672 20.66 9H14Z" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>
          <button 
            className={`action-button ${message.response_liked === false ? 'active' : ''}`} 
            title="Dislike" 
            onClick={() => handleFeedback(false)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M17 2H20C20.5304 2 21.0391 2.21071 21.4142 2.58579C21.7893 2.96086 22 3.46957 22 4V11C22 11.5304 21.7893 12.0391 21.4142 12.4142C21.0391 12.7893 20.5304 13 20 13H17M10 15V19C10 19.7956 10.3161 20.5587 10.8787 21.1213C11.4413 21.6839 12.2044 22 13 22L17 13V2H4.72C4.23772 1.99448 3.76969 2.16359 3.40209 2.47599C3.03449 2.78839 2.79219 3.22309 2.72 3.7L1.34 12.7C1.29651 12.9866 1.31583 13.2793 1.39666 13.5577C1.47749 13.8362 1.61791 14.0937 1.80814 14.3125C1.99837 14.5313 2.23392 14.7061 2.49837 14.8248C2.76282 14.9435 3.05007 15.0033 3.34 15H10Z" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Message;