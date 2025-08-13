import React, {useEffect} from 'react';
import Message from './Message';
import LoadingSpinner from './LoadingSpinner';
import { useChat } from '../context/ChatContext';
import WelcomeScreen from './WelcomeScreen';

const MessageList: React.FC = () => {
  const { messages, isProcessing, currentStreamedMessage } = useChat();

  useEffect(() => {
    console.log('Messages:', messages);
    console.log('Is Processing:', isProcessing);
    console.log('Current Streamed Message:', currentStreamedMessage);
  }, [messages, isProcessing, currentStreamedMessage]);

  if (messages.length === 0) {
    return <WelcomeScreen />;
  }
  
  return (
    <div className="flex-1 overflow-y-auto">
      {messages.map((message, index) => (
        <Message
          key={index}
          role={message.role}
          content={message.content}
          isStreaming={false}
        />
      ))}
      {isProcessing && !currentStreamedMessage && <LoadingSpinner />}
      {isProcessing && currentStreamedMessage && (
        <Message
          role="assistant"
          content={currentStreamedMessage}
          isStreaming={true}
        />
      )}
    </div>
  );
};

export default MessageList;