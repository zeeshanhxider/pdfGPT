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
          content: `✅ Successfully uploaded ${response.data.documents.length} document(s): ${response.data.documents.map(d => d.filename).join(', ')}`
        }
      ]);
    } catch (error) {
      console.error('Upload error:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'system',
          content: `❌ Error uploading files: ${error.response?.data?.detail || error.message}`
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

    // Add user message to chat
    const newMessages = [
      ...messages,
      { role: 'user', content: userMessage }
    ];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      // Prepare conversation history (excluding system messages)
      const conversationHistory = newMessages
        .filter(msg => msg.role !== 'system')
        .map(msg => ({ role: msg.role, content: msg.content }));

      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        question: userMessage,
        conversation_history: conversationHistory.slice(-6) // Last 3 exchanges
      });

      // Add AI response to chat
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
          content: '🗑️ All documents have been cleared from the database.'
        }
      ]);
    } catch (error) {
      console.error('Clear error:', error);
      alert('Error clearing documents: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 AI Document Chatbot</h1>
        <p className="subtitle">Upload documents and ask questions about their content</p>
      </header>

      <div className="main-container">
        <div className="sidebar">
          <div className="upload-section">
            <h3>📁 Upload Documents</h3>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt"
              multiple
              onChange={handleFileUpload}
              disabled={isUploading}
              id="file-input"
              className="file-input"
            />
            <label htmlFor="file-input" className="upload-button">
              {isUploading ? 'Uploading...' : 'Choose Files'}
            </label>
            <p className="upload-hint">PDF or TXT files</p>
          </div>

          {uploadedFiles.length > 0 && (
            <div className="uploaded-files">
              <h3>📚 Uploaded Files ({uploadedFiles.length})</h3>
              <div className="file-list">
                {uploadedFiles.map((file, idx) => (
                  <div key={idx} className="file-item">
                    {file}
                  </div>
                ))}
              </div>
              <button onClick={clearDocuments} className="clear-button">
                Clear All Documents
              </button>
            </div>
          )}
        </div>

        <div className="chat-container">
          <div className="messages">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h2>👋 Welcome!</h2>
                <p>Upload one or more documents using the sidebar, then ask questions about their content.</p>
                <div className="example-questions">
                  <p><strong>Example questions:</strong></p>
                  <ul>
                    <li>What is this document about?</li>
                    <li>Summarize the main points</li>
                    <li>What does it say about [topic]?</li>
                  </ul>
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role}`}>
                  <div className="message-content">
                    {msg.content}
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources">
                      <details>
                        <summary>📎 Sources ({msg.sources.length})</summary>
                        <div className="source-list">
                          {msg.sources.map((source, sidx) => (
                            <div key={sidx} className="source-item">
                              <strong>{source.filename}</strong> (Chunk {source.chunk_id + 1})
                              <p className="source-preview">{source.content}</p>
                            </div>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              ))
            )}
            {isLoading && (
              <div className="message assistant">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="input-form">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={isLoading}
              className="message-input"
            />
            <button type="submit" disabled={isLoading || !inputValue.trim()} className="send-button">
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;

