import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setIsUploading(true);
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadedFiles(prev => [
        ...prev,
        ...response.data.documents.map(doc => doc.filename)
      ]);

      setMessages(prev => [
        ...prev,
        {
          role: 'system',
          content: `Successfully uploaded ${response.data.documents.length} document(s): ${response.data.documents.map(d => d.filename).join(', ')}`
        }
      ]);
    } catch (error) {
      console.error('Upload error:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'system',
          content: `Error uploading files: ${error.response?.data?.detail || error.message}`
        }
      ]);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');

    const newMessages = [
      ...messages,
      { role: 'user', content: userMessage }
    ];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const conversationHistory = newMessages
        .filter(msg => msg.role !== 'system')
        .map(msg => ({ role: msg.role, content: msg.content }));

      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        question: userMessage,
        conversation_history: conversationHistory.slice(-6)
      });

      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: response.data.answer,
          sources: response.data.sources
        }
      ]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message}`
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearDocuments = async () => {
    if (!window.confirm('Are you sure you want to clear all documents?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/documents`);
      setUploadedFiles([]);
      setMessages([
        {
          role: 'system',
          content: 'All documents have been cleared from the database.'
        }
      ]);
      setShowSidebar(false);
    } catch (error) {
      console.error('Clear error:', error);
      alert('Error clearing documents: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="app">
      <div className={`sidebar ${showSidebar ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-title">Documents</h2>
          <button className="close-btn" onClick={() => setShowSidebar(false)}>×</button>
        </div>
        <div className="sidebar-content">
          {uploadedFiles.length === 0 ? (
            <p className="empty-state">No documents uploaded yet</p>
          ) : (
            <>
              <div className="file-count">
                {uploadedFiles.length} {uploadedFiles.length === 1 ? 'document' : 'documents'}
              </div>
              <div className="file-list">
                {uploadedFiles.map((file, idx) => (
                  <div key={idx} className="file-item">
                    <svg className="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="file-name">{file}</span>
                  </div>
                ))}
              </div>
              <button onClick={clearDocuments} className="clear-btn">Clear All</button>
            </>
          )}
        </div>
      </div>

      {showSidebar && <div className="overlay" onClick={() => setShowSidebar(false)} />}

      <div className="main-content">
        <header className="header">
          <button className="menu-btn" onClick={() => setShowSidebar(true)}>
            <svg className="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 className="header-title">AI Document Assistant</h1>
        </header>

        <div className="messages-container">
          <div className="messages">
            {messages.length === 0 ? (
              <div className="welcome">
                <div className="welcome-content">
                  <svg className="welcome-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  <h2 className="welcome-title">Welcome</h2>
                  <p className="welcome-text">Upload documents and start asking questions about their content</p>
                  <div className="example-box">
                    <p className="example-title">Example prompts</p>
                    <div className="example-item">What is this document about?</div>
                    <div className="example-item">Summarize the main points</div>
                    <div className="example-item">What does it say about specific topics?</div>
                  </div>
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, idx) => (
                  <div key={idx} className="message-wrapper">
                    <div className={`message ${msg.role}`}>
                      {msg.role === 'assistant' && (
                        <div className="avatar">
                          <svg className="avatar-icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                            <circle cx="12" cy="12" r="3"/>
                          </svg>
                        </div>
                      )}
                      <div className="message-content">
                        <div className="message-bubble">{msg.content}</div>
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="sources">
                            <details>
                              <summary>View {msg.sources.length} {msg.sources.length === 1 ? 'source' : 'sources'}</summary>
                              <div className="sources-list">
                                {msg.sources.map((source, sidx) => (
                                  <div key={sidx} className="source-item">
                                    <div className="source-header">
                                      {source.filename} · Chunk {source.chunk_id + 1}
                                    </div>
                                    <div className="source-content">{source.content}</div>
                                  </div>
                                ))}
                              </div>
                            </details>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="message-wrapper">
                    <div className="message assistant">
                      <div className="avatar">
                        <svg className="avatar-icon" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                      </div>
                      <div className="message-content">
                        <div className="typing-indicator">
                          <span className="typing-dot"></span>
                          <span className="typing-dot"></span>
                          <span className="typing-dot"></span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </div>

        <div className="input-area">
          <div className="input-container">
            <form onSubmit={handleSubmit} className="input-form">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt"
                multiple
                onChange={handleFileUpload}
                disabled={isUploading}
                className="file-input"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="attach-btn"
              >
                <svg className="attach-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Message AI Document Assistant..."
                disabled={isLoading}
                className="text-input"
              />
              <button 
                type="submit" 
                disabled={isLoading || !inputValue.trim()} 
                className={`send-btn ${inputValue.trim() && !isLoading ? 'active' : ''}`}
              >
                <svg className="send-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;