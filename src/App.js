import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [conversation, setConversation] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const savedId = localStorage.getItem('conversationId');
    if (savedId) {
      setConversationId(savedId);
      fetchConversation(savedId);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  const fetchConversation = async (id) => {
    try {
      const response = await axios.get(`http://localhost:8000/conversation/${id}`);
      setConversation(response.data.messages);
    } catch (error) {
      console.error('Error fetching conversation:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    // Add user message immediately to conversation
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
      
      if (!conversationId) {
        setConversationId(response.data.conversation_id);
        localStorage.setItem('conversationId', response.data.conversation_id);
      }
      
      // Add bot response to conversation
      const botMessage = response.data.messages[0];
      setConversation(prev => [...prev, botMessage]);
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

  const clearConversation = () => {
    setConversation([]);
    setConversationId(null);
    localStorage.removeItem('conversationId');
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <h1>Assistant Hôtelier Tunisien</h1>
          <button onClick={clearConversation} className="clear-btn">
            Nouvelle Discussion
          </button>
        </div>
        
        <div className="messages">
          {conversation.length === 0 ? (
            <div className="welcome-message">
              <p>Bienvenue ! Posez-moi des questions sur les hôtels en Tunisie.</p>
              <p>Exemples :</p>
              <ul>
                <li>Quels hôtels 5 étoiles recommandez-vous à Tunis ?</li>
                <li>Quels sont les hôtels avec piscine à Sousse ?</li>
                <li>Donnez-moi des hôtels pas chers à Djerba</li>
              </ul>
            </div>
          ) : (
            conversation.map((msg) => (
              <div key={msg.id} className={`message ${msg.sender}`}>
                <div className="message-content">
                  {msg.content.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
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