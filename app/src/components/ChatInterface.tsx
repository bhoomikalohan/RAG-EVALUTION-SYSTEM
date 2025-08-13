import React, { useState, useRef, useEffect } from 'react';
import Header from './Header';
import MessageList from './MessageList';
import InputArea from './InputArea';
import { useChat } from '../context/ChatContext';

const ChatInterface: React.FC = () => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages } = useChat();
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto py-4 md:py-8">
          <div className="max-w-3xl mx-auto px-4">
            <MessageList />
            <div ref={messagesEndRef} />
          </div>
        </div>
        <div className="max-w-3xl mx-auto px-4 py-4">
          <InputArea />
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;