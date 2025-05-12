import React from 'react';
import MessageItem from './MessageItem';
import { useChat } from '../../context/ChatContext';

const MessageList = () => {
  const { messages } = useChat();

  return (
    <div className="message-list">
      {messages.map((message, index) => (
        <MessageItem key={index} message={message} />
      ))}
    </div>
  );
};

export default MessageList; 