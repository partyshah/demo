import React from 'react';
import './App.css';
import ChatContainer from './components/Chat/ChatContainer';
import { ChatProvider } from './context/ChatContext';

function App() {
  return (
    <ChatProvider>
      <div className="App">
        <header className="app-header">
          <h1 className="app-title">Claude Chat</h1>
        </header>
        <main className="app-main">
          <ChatContainer />
        </main>
      </div>
    </ChatProvider>
  );
}

export default App;
