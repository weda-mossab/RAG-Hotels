import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [conversation, setConversation] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [conversationsList, setConversationsList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => localStorage.getItem('userId') || String(Math.random().toString(36).substring(2, 15)));
  const messagesEndRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('userId', userId);
    fetchConversations();
  }, [userId]);

  useEffect(() => {
    if (conversationId) {
      fetchConversation(conversationId);
      localStorage.setItem('currentConversationId', conversationId);
    }
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/conversations/${userId}`);
      setConversationsList(response.data.conversations);
      
      // Load last conversation if none is selected
      if (!conversationId && response.data.conversations.length > 0) {
        const lastConvId = response.data.conversations[0].id;
        setConversationId(lastConvId);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const fetchConversation = async (id) => {
    try {
      const response = await axios.get(`http://localhost:8000/conversation/${id}`);
      setConversation(response.data.messages);
    } catch (error) {
      console.error('Error fetching conversation:', error);
    }
  };

  const startNewConversation = async () => {
    try {
      const response = await axios.post('http://localhost:8000/new-conversation', {
        user_id: userId
      });
      setConversationId(response.data.conversation_id);
      fetchConversations();
    } catch (error) {
      console.error('Error creating new conversation:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    const userMessage = {
      id: Date.now().toString(),
      content: input,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    
    setConversation(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      const response = await axios.post('http://localhost:8000/ask', {
        question: input,
        conversation_id: conversationId
      });
      
      setConversation(prev => [...prev, ...response.data.messages]);
      fetchConversations(); // Refresh conversation list
    } catch (error) {
      console.error('Error:', error);
      setConversation(prev => [...prev, {
        id: Date.now().toString(),
        content: 'Désolé, une erreur est survenue lors du traitement de votre question.',
        sender: 'bot',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="sidebar">
        <button onClick={startNewConversation} className="new-chat-btn">
          + Nouvelle discussion
        </button>
        <div className="conversations-list">
          {conversationsList.map(conv => (
            <div 
              key={conv.id} 
              className={`conversation-item ${conv.id === conversationId ? 'active' : ''}`}
              onClick={() => setConversationId(conv.id)}
            >
              <div className="conversation-preview">
                {conv.preview.length > 30 ? conv.preview.substring(0, 30) + '...' : conv.preview}
              </div>
              <div className="conversation-date">
                {new Date(conv.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="chat-container">
        <div className="chat-header">
          <h1>Assistant Hôtelier</h1>
        </div>
        
        <div className="messages">
          {conversation.length === 0 ? (
            <div className="welcome-message">
              <p>Bienvenue ! Posez-moi des questions sur les hôtels en Tunisie.</p>
            </div>
          ) : (
            conversation.map((msg) => (
              <div key={msg.id} className={`message ${msg.sender}`}>
                <div className="message-content">
                  {msg.content}
                </div>
                <div className="message-timestamp">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
          {isLoading && (
            <div className="message bot">
              <div className="message-content">Réfléchis...</div>
            </div>
          )}
        </div>
        
        <form onSubmit={handleSubmit} className="input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Tapez votre question ici..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            Envoyer
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;