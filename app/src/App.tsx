import React, { useEffect, useState } from 'react';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import { ChatProvider } from './context/ChatContext';

interface ChatMeta {
  id: string;
  name: string;
}

function App() {
  const [chats, setChats] = useState<ChatMeta[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const getCookie = (name: string): string | null => {
    const cookies = document.cookie.split(';');
    const cookie = cookies.find(c => c.trim().startsWith(`${name}=`));
    return cookie ? cookie.split('=')[1] : null;
  };

  // Add effect to sync active chat ID with cookie
  useEffect(() => {
    if (activeChatId) {
      setSessionIdCookie(activeChatId);
    }
  }, [activeChatId]);

  const loadChats = async () => {
    try {
      setError(null);
      
      // Get stored session IDs from cookies
      const storedUserSessionId = getCookie('user_session_id');
      const storedSessionId = getCookie('session_id');
      
      const response = await fetch('/api/chats', {
        credentials: 'include'
      });
      
      if (!response.ok) {
        if (response.status === 403) {
          // Only create a new chat if we don't have a user session
          if (!storedUserSessionId) {
            await handleNewChat();
          }
          return;
        }
        throw new Error('Failed to load chats');
      }

      const data = await response.json();
      if (data.chats && data.chats.length > 0) {
        setChats(data.chats);
        
        // If we have a stored session ID and it exists in the chats, use it
        if (storedSessionId && data.chats.some((chat: ChatMeta) => chat.id === storedSessionId)) {
          setActiveChatId(storedSessionId);
        } else {
          // Otherwise use the most recent chat
          const mostRecentChatId = data.chats[0].id;
          setActiveChatId(mostRecentChatId);
          setSessionIdCookie(mostRecentChatId);
        }
      } else {
        // Only create a new chat if we don't have any existing sessions
        await handleNewChat();
      }
    } catch (error) {
      console.error('Error loading chats:', error);
      setError('Failed to load chats. Creating a new session...');
      handleNewChat();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadChats();
  }, []);

  const handleNewChat = async () => {
    try {
      setError(null);
      const response = await fetch('/api/new_chat', {
        method: 'POST',
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('Failed to create new chat');
      }
      
      const data = await response.json();
      if (!data.session_id) {
        throw new Error('Missing session ID');
      }
      
      // Set the new chat as active
      setActiveChatId(data.session_id);
      setSessionIdCookie(data.session_id);

      // Reload chat list to include new chat
      const chatsResponse = await fetch('/api/chats', {
        credentials: 'include'
      });
      if (!chatsResponse.ok) {
        throw new Error('Failed to load updated chat list');
      }
      const chatsData = await chatsResponse.json();
      if (chatsData.chats) {
        setChats(chatsData.chats);
      }
    } catch (error) {
      console.error('Error creating new chat:', error);
      setError('Failed to create new chat. Please try again.');
    }
  };

  const handleDeleteChat = async (id: string) => {
    try {
      setError(null);
      const response = await fetch(`/api/chat/${id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      const data = await response.json();
      if (response.ok) {
        // Update chats with the new list from server that has correct numbering
        setChats(data.chats);
        if (activeChatId === id) {
          const remaining = data.chats;
          if (remaining.length > 0) {
            setActiveChatId(remaining[0].id);
            setSessionIdCookie(remaining[0].id);
          } else {
            handleNewChat();
          }
        }
      } else if (response.status === 403) {
        setError('You do not have permission to delete this chat');
      } else {
        throw new Error('Failed to delete chat');
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
      setError('Failed to delete chat. Please try again.');
    }
  };

  const handleSelectChat = (id: string) => {
    setError(null);
    setActiveChatId(id);
    setSessionIdCookie(id);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f7f7f8] dark:bg-[#121212] text-black dark:text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#f7f7f8] dark:bg-[#121212] text-black dark:text-white">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onSelect={handleSelectChat}
        onNewChat={handleNewChat}
        onDelete={handleDeleteChat}
      />
      <div className="flex-1">
        {error && (
          <div className="p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">
            {error}
          </div>
        )}
        {chats.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <button 
              onClick={handleNewChat}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Start New Chat
            </button>
          </div>
        ) : (
          <ChatProvider chatId={activeChatId || ''} key={activeChatId}>
            <ChatInterface />
          </ChatProvider>
        )}
      </div>
    </div>
  );
}

function setSessionIdCookie(chatId: string) {
  document.cookie = `session_id=${chatId}; path=/; samesite=lax`;
}

export default App;