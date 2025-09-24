import { useState, useRef, useEffect } from 'react';
import type { Message, ChatStep } from '../types/index';
import  {MAIN_MENU_OPTIONS}  from '../Constants/index';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hello! I'm your Banking Dispute Assistant. How can I help you today?",
      sender: 'bot',
      timestamp: new Date(),
      options: [...MAIN_MENU_OPTIONS]
    }
  ]);

  const [currentStep, setCurrentStep] = useState<ChatStep>('greeting');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (
    text: string, 
    sender: 'user' | 'bot', 
    options?: string[], 
    type: 'text' | 'selection' | 'confirmation' = 'text'
  ) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      text,
      sender,
      timestamp: new Date(),
      options,
      type
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const simulateTyping = async (duration: number = 1000): Promise<void> => {
    setIsTyping(true);
    await new Promise(resolve => setTimeout(resolve, duration));
    setIsTyping(false);
  };

  return {
    messages,
    currentStep,
    isTyping,
    messagesEndRef,
    setCurrentStep,
    addMessage,
    simulateTyping
  };
};