import React from 'react';
import { Bot, User } from 'lucide-react';
import type { Message } from '../types/index';

interface ChatMessageProps {
  message: Message;
  onOptionClick: (option: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onOptionClick }) => {
  return (
    <div className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-sm ${
          message.sender === 'user'
            ? 'bg-blue-600 text-white rounded-br-sm'
            : 'bg-white text-gray-800 rounded-bl-sm border border-gray-200'
        }`}
      >
        <div className="flex items-start space-x-2">
          {message.sender === 'bot' && (
            <Bot className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          )}
          <div className="flex-1">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.text}
            </p>
            
            {message.options && (
              <div className="mt-3 space-y-2">
                {message.options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => onOptionClick(option)}
                    className="block w-full text-left px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors duration-200 border border-blue-200"
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}
          </div>
          {message.sender === 'user' && (
            <User className="w-5 h-5 text-blue-100 mt-0.5 flex-shrink-0" />
          )}
        </div>
        
        <div className="mt-2 text-xs opacity-70">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};