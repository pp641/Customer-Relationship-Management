import React from 'react';
import { Bot } from 'lucide-react';

interface TypingIndicatorProps {
  isLoading?: boolean;
  loadingText?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ 
  isLoading, 
  loadingText = "Creating your dispute..." 
}) => {
  if (isLoading) {
    return (
      <div className="flex justify-start">
        <div className="bg-white px-4 py-3 rounded-2xl shadow-sm border border-gray-200">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
            <span className="text-sm text-gray-600">{loadingText}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="bg-white px-4 py-3 rounded-2xl rounded-bl-sm shadow-sm border border-gray-200">
        <div className="flex items-center space-x-2">
          <Bot className="w-5 h-5 text-blue-600" />
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};