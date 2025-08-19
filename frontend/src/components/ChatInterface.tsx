"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, FileText, Clock, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiService } from "@/lib/api";
import { Message, ChatRequest, ChatResponse, ChatMessage } from "@/types";
import { generateId, formatTime } from "@/lib/utils";

interface ChatInterfaceProps {
  documentId?: string;
  documentName?: string;
  disabled?: boolean;
}

export function ChatInterface({
  documentId,
  documentName,
  disabled = false,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add welcome message when document is uploaded
  useEffect(() => {
    if (documentId && documentName && messages.length === 0) {
      const welcomeMessage: Message = {
        id: generateId(),
        content: `I've successfully processed "${documentName}". You can now ask me questions about its content!`,
        role: "assistant",
        timestamp: new Date(),
        sources: [],
        confidence: 1.0,
      };
      setMessages([welcomeMessage]);
    }
  }, [documentId, documentName, messages.length]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || disabled) return;

    const userMessage: Message = {
      id: generateId(),
      content: inputMessage,
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      // Build conversation history from messages (excluding welcome messages)
      const conversationHistory = messages
        .filter((msg) => msg.sources !== undefined || msg.role === "user") // Exclude welcome messages
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));

      const chatRequest: ChatRequest = {
        message: inputMessage,
        document_id: documentId,
        temperature: 0.7,
        max_tokens: 500,
        conversation_history: conversationHistory,
      };

      const response = await apiService.sendChatMessage(chatRequest);

      const assistantMessage: Message = {
        id: generateId(),
        content: response.response,
        role: "assistant",
        timestamp: new Date(),
        sources: response.sources || [],
        confidence: response.confidence || 0,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error("Chat error:", error);

      const errorMessage: Message = {
        id: generateId(),
        content:
          "I'm sorry, I encountered an error while processing your question. Please try again.",
        role: "assistant",
        timestamp: new Date(),
        sources: [],
        confidence: 0,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (disabled && !documentId) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Ready to Chat
        </h3>
        <p className="text-gray-500">
          Upload a PDF document to start asking questions about its content.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="border-b bg-gray-50 px-4 py-3 rounded-t-lg">
        <div className="flex items-center space-x-2">
          <Bot className="h-5 w-5 text-blue-600" />
          <h3 className="font-medium text-gray-900">PDF Assistant</h3>
          {documentName && (
            <div className="flex items-center space-x-1 text-sm text-gray-500">
              <FileText className="h-4 w-4" />
              <span>{documentName}</span>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-900"
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.role === "assistant" && (
                  <Bot className="h-5 w-5 mt-0.5 text-blue-600" />
                )}
                {message.role === "user" && (
                  <User className="h-5 w-5 mt-0.5 text-white" />
                )}
                <div className="flex-1">
                  <div className="whitespace-pre-wrap">{message.content}</div>

                  {/* Sources and confidence for assistant messages */}
                  {message.role === "assistant" &&
                    message.sources &&
                    message.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <div className="text-xs text-gray-500 space-y-1">
                          <div className="flex items-center space-x-1">
                            <FileText className="h-3 w-3" />
                            <span>Sources:</span>
                          </div>
                          {message.sources.map((source, index) => (
                            <div key={index} className="ml-4 text-xs">
                              • {source}
                            </div>
                          ))}
                          {message.confidence !== undefined && (
                            <div className="flex items-center space-x-1 mt-1">
                              <Target className="h-3 w-3" />
                              <span>
                                Confidence:{" "}
                                {(message.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                  <div
                    className={`text-xs mt-1 ${
                      message.role === "user"
                        ? "text-blue-200"
                        : "text-gray-400"
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
              <div className="flex items-center space-x-2">
                <Bot className="h-5 w-5 text-blue-600" />
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
                  <div
                    className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  />
                  <div
                    className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex space-x-2">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              documentId
                ? "Ask a question about the document..."
                : "Upload a document first to start chatting..."
            }
            disabled={disabled || isLoading || !documentId}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={
              disabled || isLoading || !inputMessage.trim() || !documentId
            }
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {documentId && (
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        )}
      </div>
    </div>
  );
}
