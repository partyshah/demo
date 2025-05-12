import React, { createContext, useContext, useState } from 'react';
import { sendMessageToBackend } from '../services/chatApi';

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const addMessage = (message) => {
    setMessages((prev) => [...prev, message]);
  };

  const updateSystemPrompt = (newPrompt) => {
    setSystemPrompt(newPrompt);
  };

  // Send user message, call backend, and add assistant response
  const sendMessage = async (userMessage) => {
    setIsLoading(true);
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    try {
      const assistantMessage = await sendMessageToBackend(newMessages);
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error: Could not get response from backend.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        systemPrompt,
        isLoading,
        addMessage,
        updateSystemPrompt,
        setIsLoading,
        sendMessage,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}; 