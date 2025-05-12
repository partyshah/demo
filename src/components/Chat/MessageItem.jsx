import React from 'react';

const MessageItem = ({ message }) => {
  const isUser = message?.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'user' : 'ai'}`}>
      <div className={`message-bubble ${isUser ? 'user-bubble' : 'ai-bubble'}`}>
        <p className="message-text">{message?.content}</p>
      </div>
    </div>
  );
};

export default MessageItem; 