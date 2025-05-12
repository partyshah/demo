import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';

const ChatInput = () => {
  const [message, setMessage] = useState('');
  const { sendMessage, isLoading } = useChat();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    await sendMessage({ role: 'user', content: message });
    setMessage('');
  };

  return (
    <form onSubmit={handleSubmit} className="chat-input-form">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message..."
        className="chat-input"
        disabled={isLoading}
      />
      <button
        type="submit"
        className="send-button"
        disabled={isLoading}
      >
        {isLoading ? 'Sending...' : 'Send'}
      </button>
    </form>
  );
};

export default ChatInput; 