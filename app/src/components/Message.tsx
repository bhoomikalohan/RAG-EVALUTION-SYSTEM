import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Volume2 } from 'lucide-react';

interface MessageProps {
  role: 'user' | 'assistant';
  content: string;
  isStreaming: boolean;
}

const Message: React.FC<MessageProps> = ({ role, content, isStreaming }) => {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleTTS = async () => {
    if (isLoading) return;
    
    try {
      setIsLoading(true);
      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: content }),
      });

      if (!response.ok) {
        throw new Error('TTS request failed');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (error) {
      console.error('TTS error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4 px-4`}>
      <div className={`max-w-3xl rounded-lg p-6 ${
        role === 'user'
          ? 'text-gray-100'
          : 'bg-[#1a1a1d] text-gray-100'
      }`}>
        <div className={`prose prose-invert max-w-none ${isStreaming ? 'streaming-text' : ''}`}>
          <ReactMarkdown
            components={{
              p: ({ node, ...props }) => (
                <p {...props} className="whitespace-pre-wrap text-gray-100" />
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
        {role === 'assistant' && !isStreaming && (
          <div className="mt-4">
            {!audioUrl ? (
              <button
                onClick={handleTTS}
                disabled={isLoading}
                className="text-gray-400 hover:text-blue-500 transition-colors flex items-center gap-2"
                title="Listen to this message"
              >
                <Volume2 size={20} />
                {isLoading ? 'Generating audio...' : 'Listen'}
              </button>
            ) : (
              <audio controls src={audioUrl} className="w-full" />
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;