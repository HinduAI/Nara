import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { supabase } from './supabaseClient';
import LoginPage from './components/LoginPage';
import ReactMarkdown from 'react-markdown';
import AboutPage from './components/AboutPage';
// import naraIcon from './images/nara.png';  // Make sure the image is in your src folder
import Sidebar from './components/Sidebar';
import { FiShare2 } from 'react-icons/fi';
import Message from './components/Message';  // Add this import at the top
import DeleteModal from './components/DeleteModal';
import { apiGet, apiPost, apiPut, apiDelete, debugTokenStatus } from './utils/apiClient';

const BACKEND_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAbout, setShowAbout] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const messagesEndRef = useRef(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState(null);

  useEffect(() => {
    // Check active sessions and sets the user
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for changes on auth state (sign in, sign out, etc.)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Fetch initial data

  // Fetch conversations on login
  useEffect(() => {
    if (user) {
      console.log(user);
      
      fetchConversations();
    }
  }, [user]);

  // Add this new useEffect to fetch messages when activeConversationId changes
  useEffect(() => {
    if (activeConversationId) {
      fetchConversationMessages(activeConversationId);
    } else {
      setMessages([]);
    }
  }, [activeConversationId]);

  // Keep only this useEffect for handling clicks outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.user-section')) {
        setShowProfileDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Add debug function to window
  useEffect(() => {
    window.debugTokenStatus = debugTokenStatus;
  }, []);

  const fetchConversations = async () => {
    try {
      setIsLoadingConversations(true);
      
      const response = await apiGet('/api/conversations');
      const data = await response.json();
      
      setConversations(data);
      console.log('Conversations loaded:', data);
      
      // Set active conversation to the most recent one if none is selected
      if (!activeConversationId && data.length > 0) {
        setActiveConversationId(data[0].id);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
      setError(`Failed to load conversations: ${error.message}`);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  const createNewConversation = async (question) => {
    try {
      const response = await apiPost('/api/createnewconversation', { 
        question: question 
      });
      
      const data = await response.json();
      return data.id;
    } catch (error) {
      console.error('Error creating new conversation:', error);
      throw error;
    }
  };

  // Update the scrollToBottom function
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleLogout = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      
      // Clear local state
      setUser(null);
      setConversations([]);
      setMessages([]);
      setActiveConversationId(null);
      
      // Optional: Redirect to home or login page
      window.location.href = '/';
    } catch (error) {
      console.error('Error signing out:', error.message);
    }
  };
  
  // Update the handleAskQuestion function to include scrolling
  const handleAskQuestion = async () => {
    if (!question.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // If no active conversation, create a new one
      let currentConversationId = activeConversationId;
      if (!currentConversationId) {
        const newConv = await createNewConversation(question);
        currentConversationId = newConv;
        setActiveConversationId(newConv);
      }

      const body = {
        question,
        conversation_id: currentConversationId
      };

      const response = await apiPost('/api/ask', body);
      const data = await response.json();
      
      setResponse(data);
      setQuestion('');
      await fetchConversations();
      await fetchConversationMessages(currentConversationId);
    } catch (error) {
      console.error('Error asking question:', error);
      setError('Failed to get response. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAskQuestion();
    }
  };

  // Add this function to handle textarea auto-resize
  const handleTextareaChange = async (e) => {
    const textarea = e.target;
    const newQuestion = e.target.value;
    setQuestion(newQuestion);
    
    // Reset height to auto and then set to scrollHeight to get proper height
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';

    // Only update the title if we have an active conversation with default title
    if (activeConversationId && newQuestion.trim() && 
        conversations.find(conv => conv.id === activeConversationId)?.title === "New Chat") {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        await fetch(`${BACKEND_URL}/api/conversations/${activeConversationId}/title`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session.access_token}`
          },
          body: JSON.stringify({ 
            title: newQuestion.substring(0, 50) + (newQuestion.length > 50 ? '...' : '') 
          })
        });
        
        await fetchConversations();
      } catch (error) {
        console.error('Error updating conversation title:', error);
      }
    }
  };


  const handleNewChat = async () => {
    try {
      setIsLoading(true);
      setMessages([]);
      setResponse(null);
      setQuestion('');
      
      const response = await apiPost('/api/createnewconversation', {});
      const data = await response.json();
      
      setActiveConversationId(data.id);
      await fetchConversations();
    } catch (error) {
      console.error('Error creating new chat:', error);
      setError('Failed to create new chat. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (conversationId) => {
    try {
      await apiDelete(`/api/conversations/${conversationId}`);
      
      if (activeConversationId === conversationId) {
        setActiveConversationId(null);
        setMessages([]);
      }
      
      await fetchConversations();
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  // Update the fetchConversationMessages function to include scrolling
  const fetchConversationMessages = async (conversationId) => {
    if (!conversationId) {
      setMessages([]);
      return;
    }

    try {
      const response = await apiGet(`/api/conversations/${conversationId}/messages`);
      const data = await response.json();
      
      console.log('Raw message data from API:', data);
      
      const formattedMessages = data.map(msg => ({
        id: msg.id,
        user: msg.user,
        assistant: msg.assistant,
        response_liked: msg.response_liked
      }));
      
      console.log('Formatted messages:', formattedMessages);
      setMessages(formattedMessages);

      setTimeout(scrollToBottom, 100);
    } catch (error) {
      console.error('Error fetching messages:', error);
      setError('Failed to load messages. Please try again.');
    }
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };


  // Add these handler functions in your App component
  const handleRegenerate = async (messageId) => {
    // Implementation for regenerating response
    console.log('Regenerating response for message:', messageId);
    // Add your regeneration logic here
  };

  const handleFeedback = async (messageId, isPositive) => {
    try {
      const response = await apiPost(`/api/messages/${messageId}/feedback`, {
        response_liked: isPositive
      });
      
      // Update the message locally to show the feedback was recorded
      setMessages(prevMessages => 
        prevMessages.map(msg => 
          msg.id === messageId ? {
            ...msg,
            response_liked: isPositive
          } : msg
        )
      );
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setError('Failed to submit feedback. Please try again.');
    }
  };

  const confirmDelete = async () => {
    try {
      await handleDeleteConversation(conversationToDelete);
      setDeleteModalOpen(false);
      setConversationToDelete(null);
    } catch (error) {
      console.error('Error confirming delete:', error);
    }
  };

  const handleDeleteClick = (conversationId) => {
    setConversationToDelete(conversationId);
    setDeleteModalOpen(true);
  };

  // Early return for About page
  if (showAbout) {
    return (
      <div>
        <AboutPage user={user} />
      </div>
    );
  }

  // Show loading indicator while Auth0 is initializing
  if (loading) {
    return (
      <div className="loading-auth">
        <div className="spinner"></div>
        <p>Loading application...</p>
      </div>
    );
  }
  
  // Show login page if not authenticated
  if (!user) {
    return (
      <div>
        <LoginPage onAboutClick={() => setShowAbout(true)} />
      </div>
    );
  }

  return (
    <div className="app-container">
      <DeleteModal 
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setConversationToDelete(null);
        }}
        onConfirm={confirmDelete}
      />
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={handleNewChat}
        onSelectConversation={setActiveConversationId}
        onDeleteConversation={handleDeleteClick}
        isLoading={isLoadingConversations}
        isOpen={true}
        onAboutClick={() => setShowAbout(true)}
        onLogout={() => {}}
      >
        <div className="sidebar">
          <button className="new-chat-button" onClick={handleNewChat}>
            <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" height="16" width="16">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            New chat
          </button>

          <div className="history-section">
            <div className="history-header">Previous 7 days</div>
            {conversations.slice(0, 7).map((conv) => (
              <div 
                key={conv.id} 
                className={`conversation-item ${activeConversationId === conv.id ? 'active' : ''}`}
                onClick={() => setActiveConversationId(conv.id)}
              >
                <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" height="16" width="16">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span className="conversation-title">{conv.title || 'New Conversation'}</span>
                <button className="conversation-menu">⋯</button>
              </div>
            ))}
          </div>

          <div className="history-section">
            <div className="history-header">Previous 30 days</div>
            {conversations.slice(7).map((conv) => (
              <div 
                key={conv.id} 
                className={`conversation-item ${activeConversationId === conv.id ? 'active' : ''}`}
                onClick={() => setActiveConversationId(conv.id)}
              >
                <svg stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" height="16" width="16">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span className="conversation-title">{conv.title || 'New Conversation'}</span>
                <button className="conversation-menu">⋯</button>
              </div>
            ))}
          </div>
        </div>
      </Sidebar>

      <div className="main-content">
        <div className="top-bar">
          <div className="top-bar-left">
            <div className="app-title">
              {/* <img src={} alt=" Icon" /> */}
              Nara
            </div>
          </div>
          
          <div className="top-bar-right">
            <button className="about-button" onClick={() => setShowAbout(true)}>
              About
            </button>
            <div className="user-section">
              <button 
                className="user-button" 
                onClick={() => setShowProfileDropdown(!showProfileDropdown)}
              >
                <span className="user-initial">{user.email?.charAt(0).toUpperCase()}</span>
              </button>
              
              {showProfileDropdown && (
                <div className="user-dropdown">
                  <div className="user-info">
                    <div className="user-name">{user.email}</div>
                    <span className="user-email">{user.email}</span>
                  </div>
                  <button 
                    className="dropdown-item" 
                    onClick={handleLogout}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="chat-container">
          {(!messages.length || !activeConversationId) && !isLoading && (
            <div className="empty-state">
              <h1>Hindu AI</h1>
              <div className="empty-state-text">
                What would you like to know?
              </div>
            </div>
          )}

          <div className="messages-container">
            {messages.map((message, index) => (
              <Message
                key={index}
                message={message}
                onRegenerate={() => handleRegenerate(message.id)}
                onCopy={() => {}}
                onDownload={() => {}}
                onFeedback={(isPositive) => handleFeedback(message.id, isPositive)}
              />
            ))}
            
            {isLoading && (
              <div className="loading-section">
                <span className="om-symbol spinning">ॐ</span>
                <p>Thinking...</p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="input-area">
          <div className="input-container">
            <textarea
              value={question}
              onChange={handleTextareaChange}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question..."
              rows={1}
              className="message-input"
            />
            <button 
              className="send-button"
              disabled={isLoading || !question.trim()}
              onClick={handleAskQuestion}
            >
              <span className="om-symbol">ॐ</span>
            </button>
          </div>


          <div className="disclaimer">
            If you have any questions or feedback, email us at <a href="" className="email-link">hinduai@gmail.com</a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;