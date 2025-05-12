import React from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

const ChatContainer = () => {
  return (
    <div className="chat-container">
      <div className="message-list-wrapper">
        <MessageList />
      </div>
      <div className="chat-input-wrapper">
        <ChatInput />
      </div>
    </div>
  );
};

export default ChatContainer; 