import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic } from 'lucide-react';
import { useChat } from '../context/ChatContext';

const InputArea: React.FC = () => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, isProcessing } = useChat();
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [selectedCollections, setSelectedCollections] = useState<string[]>([
    'best_practices',
    'policies',
    'data'
  ]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      sendMessage(input, selectedCollections);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const sendAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    formData.append('file', audioBlob, `${timestamp}.webm`);  // Changed 'audio' to 'file' to match FastAPI's expected field name

    try {
      const response = await fetch('/api/audio', {  // Changed to relative URL
        method: 'POST',
        credentials: 'include',  // Added credentials
        body: formData,
      });

      const transcript = await response.text();
      sendMessage(transcript, selectedCollections)
    } catch (error) {
      console.error('Error sending audio:', error);
    }
  };

  const handleMicClick = async () => {
    if (isRecording) {
      mediaRecorder?.stop();
      setIsRecording(false);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      alert('Audio recording not supported in this browser.');
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    setMediaRecorder(recorder);
    let localChunks: Blob[] = [];
    recorder.ondataavailable = (e) => {
      localChunks.push(e.data);
    };
    recorder.onstop = async () => {
      setIsRecording(false);
      if (localChunks.length > 0) {
        const audioBlob = new Blob(localChunks, { type: 'audio/webm' });
        sendAudio(audioBlob);
      } else {
        alert("No audio data was recorded.");
      }
      localChunks = [];
      stream.getTracks().forEach(track => track.stop());
    };
    recorder.start();
    setIsRecording(true);
  };

  const toggleCollection = (name: string) => {
    setSelectedCollections(prev =>
      prev.includes(name)
        ? prev.filter(c => c !== name)
        : [...prev, name]
    );
  };

  return (
    <div className="w-full px-4 pb-4">
      <div className="bg-white dark:bg-[#2a2a2a] rounded-xl shadow flex flex-col p-0 border border-neutral-300 dark:border-[#2a2a2a]">
        <form onSubmit={handleSubmit} className="flex flex-col">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message assistant..."
            rows={1}
            disabled={isProcessing}
            className="w-full p-4 rounded-t-xl bg-transparent text-neutral-900 dark:text-neutral-100 outline-none resize-none transition-all"
            style={{
              minHeight: '56px',
              maxHeight: '200px',
              minWidth: '2000px',
              maxWidth: '2000px',
              borderBottomLeftRadius: 0,
              borderBottomRightRadius: 0,
              borderBottom: 'none'
            }}
          />
          {/* Bar below textarea */}
          <div className="flex items-center justify-between px-2 py-2 bg-white dark:bg-[#2a2a2a] rounded-b-xl">
            {/* Left buttons */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => toggleCollection('best_practices')}
                className={`px-3 py-1 rounded-md border text-sm font-medium transition-colors
                  ${selectedCollections.includes('best_practices')
                    ? 'border-blue-500 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-200'
                    : 'border-neutral-300 dark:border-neutral-700 bg-white dark:bg-[#2a2a2a] text-gray-700 dark:text-gray-200 hover:bg-blue-100 dark:hover:bg-blue-900/30'
                  }`}
              >
                Best Practices
              </button>
              <button
                type="button"
                onClick={() => toggleCollection('policies')}
                className={`px-3 py-1 rounded-md border text-sm font-medium transition-colors
                  ${selectedCollections.includes('policies')
                    ? 'border-blue-500 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-200'
                    : 'border-neutral-300 dark:border-neutral-700 bg-white dark:bg-[#2a2a2a] text-gray-700 dark:text-gray-200 hover:bg-blue-100 dark:hover:bg-blue-900/30'
                  }`}
              >
                Policies
              </button>
              <button
                type="button"
                onClick={() => toggleCollection('data')}
                className={`px-3 py-1 rounded-md border text-sm font-medium transition-colors
                  ${selectedCollections.includes('data')
                    ? 'border-blue-500 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-200'
                    : 'border-neutral-300 dark:border-neutral-700 bg-white dark:bg-[#2a2a2a] text-gray-700 dark:text-gray-200 hover:bg-blue-100 dark:hover:bg-blue-900/30'
                  }`}
              >
                Data Profile
              </button>
            </div>
            {/* Right buttons */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleMicClick}
                disabled={isProcessing}
                className={`p-2 rounded-lg bg-white dark:bg-[#2a2a2a] transition-colors
                  ${isRecording
                    ? 'text-green-600 bg-green-100 dark:bg-green-900/30'
                    : 'text-blue-500 hover:bg-blue-100 dark:hover:bg-blue-900/30'
                  }`}
                aria-label="Record audio"
                style={{ minWidth: '16px', minHeight: '16px' }}
              >
                <Mic size={20} />
              </button>
              <button
                type="submit"
                disabled={!input.trim() || isProcessing}
                className={`p-2 rounded-lg bg-white dark:bg-[#2a2a2a] transition-colors
                  ${input.trim() && !isProcessing
                    ? 'text-blue-500 hover:bg-blue-100 dark:hover:bg-blue-900/30'
                    : 'text-neutral-400 cursor-not-allowed'
                  }`}
                aria-label="Send message"
                style={{ minWidth: '16px', minHeight: '16px' }}
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InputArea;