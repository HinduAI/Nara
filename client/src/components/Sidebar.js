import React, { useState, useEffect } from 'react';
import '../styles/Sidebar.css';
import { FaTrash } from 'react-icons/fa';

const Sidebar = ({ 
  conversations, 
  activeConversationId, 
  onNewChat, 
  onSelectConversation, 
  onDeleteConversation, 
  isLoading,
  onAboutClick,
  onLogout,
  user
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  // Get first letter of email
  const userInitial = user?.email?.charAt(0).toUpperCase() || 'U';

  // Group conversations by date
  const groupedConversations = conversations.reduce((groups, conv) => {
    const date = new Date(conv.created_at);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    let groupKey;
    if (date.toDateString() === today.toDateString()) {
      groupKey = 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      groupKey = 'Yesterday';
    } else if (date > new Date(today.setDate(today.getDate() - 7))) {
      groupKey = 'Past Week';
    } else if (date > new Date(today.setDate(today.getDate() - 30))) {
      groupKey = 'Past Month';
    } else {
      groupKey = 'Older';
    }

    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(conv);
    return groups;
  }, {});

  const filteredConversations = searchTerm
    ? conversations.filter(conv => 
        conv.title.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : conversations;

  const handleDeleteClick = (e, chatId) => {
    e.stopPropagation();
    onDeleteConversation(chatId);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="top-row">
          <div className="search-container">
            <div className="search-wrapper">
              <svg 
                className="search-icon"
                stroke="currentColor" 
                fill="none" 
                strokeWidth="2" 
                viewBox="0 0 24 24" 
                height="16" 
                width="16"
              >
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>
          </div>
          <button className="new-chat-button" onClick={onNewChat} disabled={isLoading}>
            <svg 
              stroke="currentColor" 
              fill="none" 
              strokeWidth="2" 
              viewBox="0 0 24 24" 
              height="16" 
              width="16"
            >
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
            </svg>
          </button>
        </div>
      </div>

      <div className="conversations-container">
        {searchTerm ? (
          <div className="conversation-group">
            {filteredConversations.map((conv) => (
              <ConversationItem 
                key={conv.id}
                conversation={conv}
                isActive={activeConversationId === conv.id}
                onSelect={onSelectConversation}
                onDelete={(e) => handleDeleteClick(e, conv.id)}
              />
            ))}
          </div>
        ) : (
          <>
            {isLoading && conversations.length === 0 && (
              <div className="loading">Loading conversations...</div>
            )}
            {Object.entries(groupedConversations).map(([group, convs]) => (
              <div key={group} className="conversation-group">
                <h3 className="group-header">{group}</h3>
                {convs.map((conv) => (
                  <ConversationItem 
                    key={conv.id}
                    conversation={conv}
                    isActive={activeConversationId === conv.id}
                    onSelect={onSelectConversation}
                    onDelete={(e) => handleDeleteClick(e, conv.id)}
                  />
                ))}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
};

// Helper component for conversation items
const ConversationItem = ({ conversation, isActive, onSelect, onDelete }) => (
  <div 
    className={`conversation-item ${isActive ? 'active' : ''}`}
  >
    <button 
      className="conversation-button"
      onClick={() => onSelect(conversation.id)}
    >
      <svg 
        stroke="currentColor" 
        fill="none" 
        strokeWidth="2" 
        viewBox="0 0 24 24" 
        height="16" 
        width="16"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <span className="conversation-title">{conversation.title || 'New Conversation'}</span>
    </button>
    <button 
      className="delete-button"
      onClick={(e) => onDelete(e)}
    >
      <FaTrash size={14} />
    </button>
  </div>
);

export default Sidebar; 