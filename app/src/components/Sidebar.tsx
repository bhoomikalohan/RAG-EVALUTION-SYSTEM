import React from 'react';
import { Trash2, Plus } from 'lucide-react';

interface SidebarProps {
  chats: { id: string; name: string }[];
  activeChatId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ chats, activeChatId, onSelect, onNewChat, onDelete }) => (
  <div className="w-64 bg-white dark:bg-neutral-900 border-r border-gray-200 dark:border-gray-800 flex flex-col h-screen">
    <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800 h-14">
      <span className="font-bold text-lg">Chats</span>
      <button
        onClick={onNewChat}
        className="p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30"
        title="New Chat"
      >
        <Plus size={20} />
      </button>
    </div>
    <div className="flex-1 overflow-y-auto">
      {chats.map(chat => (
        <div
          key={chat.id}
          className={`flex items-center justify-between px-4 py-2 cursor-pointer transition-colors ${
            chat.id === activeChatId
              ? 'bg-blue-100 dark:bg-blue-900/30 font-semibold'
              : 'hover:bg-gray-100 dark:hover:bg-gray-800'
          }`}
          onClick={() => onSelect(chat.id)}
        >
          <span className="truncate">{chat.name}</span>
          <button
            onClick={e => {
              e.stopPropagation();
              onDelete(chat.id);
            }}
            className="ml-2 p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30"
            title="Delete Chat"
          >
            <Trash2 size={16} className="text-red-500" />
          </button>
        </div>
      ))}
    </div>
  </div>
);

export default Sidebar;