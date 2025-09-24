import React from 'react';
import { Send } from 'lucide-react';

interface ChatInputProps {
  inputText: string;
  setInputText: (text: string) => void;
  onSendMessage: () => void;
  isDisabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  inputText,
  setInputText,
  onSendMessage,
  isDisabled = false
}) => {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <div className="bg-white border-t border-gray-200 p-4">
      <div className="flex space-x-3">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isDisabled}
        />
        <button
          onClick={onSendMessage}
          disabled={!inputText.trim() || isDisabled}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white p-3 rounded-full transition-colors duration-200 shadow-lg"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      
      <div className="mt-2 text-center">
        <p className="text-xs text-gray-500">
          🔒 Your conversation is secure and confidential
        </p>
      </div>
    </div>
  );
};