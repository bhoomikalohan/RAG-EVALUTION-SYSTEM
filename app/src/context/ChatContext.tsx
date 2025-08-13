import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatContextType {
  messages: Message[];
  isProcessing: boolean;
  currentStreamedMessage: string;
  sendMessage: (message: string, selectedCollections: string[]) => Promise<void>;
  resetChat: () => void;
  loadChatHistory: () => Promise<void>;
  error: string | null;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider: React.FC<{ chatId: string; children: React.ReactNode }> = ({ chatId, children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStreamedMessage, setCurrentStreamedMessage] = useState('');
  const [error, setError] = useState<string | null>(null);

  const loadChatHistory = async () => {
    if (!chatId) return;
    try {
      setError(null);
      const response = await fetch(`/api/chat_history/${chatId}`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        if (response.status === 403) {
          setError('Unauthorized access to chat');
          setMessages([]);
          return;
        }
        throw new Error('Failed to load chat history');
      }
      
      const data = await response.json();
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Error loading chat history:', error);
      setError('Failed to load chat history');
    }
  };

  // Load messages when chatId changes
  useEffect(() => {
    if (!chatId) {
      setMessages([]);
      return;
    }
    
    // Update the session cookie and load messages for the new chat
    document.cookie = `session_id=${chatId}; path=/; samesite=lax`;
    loadChatHistory();
  }, [chatId]);

  const sendMessage = async (message: string, selectedCollections: string[]) => {
    // Verify we have an active chat
    if (!chatId) {
      setError('No active chat session');
      return;
    }

    setMessages(prev => [...prev, { role: 'user', content: message }]);
    setIsProcessing(true);
    setCurrentStreamedMessage('');
    setError(null);

    try {
      // Ensure session cookie is set correctly before sending
      document.cookie = `session_id=${chatId}; path=/; samesite=lax`;
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          text: message,
          collections: selectedCollections,
        }),
      });

      if (!response.ok) {
        if (response.status === 403) {
          setError('Unauthorized access to chat');
          return;
        }
        throw new Error('Failed to send message');
      }

      if (!response.body) {
        throw new Error('No response from server');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let accumulated = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const content = JSON.parse(line.slice(6));
              accumulated += content;
              setCurrentStreamedMessage(accumulated);
            } catch (e) {
              console.error('Error parsing SSE message:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message');
    } finally {
      setIsProcessing(false);
      setCurrentStreamedMessage('');
      if (!error) {
        // Only reload history if there was no error
        await loadChatHistory();
      }
    }
  };

  const resetChat = () => {
    setMessages([]);
    setIsProcessing(false);
    setCurrentStreamedMessage('');
    setError(null);
  };

  return (
    <ChatContext.Provider value={{ 
      messages, 
      isProcessing, 
      currentStreamedMessage, 
      sendMessage, 
      resetChat, 
      loadChatHistory,
      error 
    }}>
      {children}
    </ChatContext.Provider>
  );
};