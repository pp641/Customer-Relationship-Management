import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User,  Building2 } from 'lucide-react';
import axios from 'axios'
const BASE_URL = 'http://localhost:8000'

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  options?: string[];
  type?: 'text' | 'selection' | 'confirmation';
}

interface DisputeForm {
  type?: string;
  bank?: string;
  amount?: number;
  date?: string;
  description?: string;
  cardlastfour?: string;
  priority?: 'low' | 'medium' | 'high';
}

const disputeTypes = [
  'Double Debit / Duplicate Charge',
  'Unauthorized Transaction',
  'Missing Refund',
  'Wrong Balance/Amount',
  'Failed Transaction',
  'ATM Dispute',
  'Merchant Fraud',
  'Card Skimming',
  'Other'
];

const banks = [
  'State Bank of India',
  'HDFC Bank', 
  'ICICI Bank',
  'Axis Bank',
  'Punjab National Bank',
  'Bank of Baroda',
  'Canara Bank',
  'Other'
];

const BankingDisputeChatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hello! I'm your Banking Dispute Assistant. How can I help you today?",
      sender: 'bot',
      timestamp: new Date(),
      options: [
        'Report a Dispute',
        'Track Existing Dispute',
        'Get Guidance',
        'Emergency Help'
      ]
    }
  ]);
  const [shouldCreateDispute, setShouldCreateDispute] = useState(false);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentStep, setCurrentStep] = useState('greeting');
  const [disputeForm, setDisputeForm] = useState<DisputeForm>({});
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  useEffect(() => {
    if (shouldCreateDispute && disputeForm.cardlastfour) {
      createDispute();
      setShouldCreateDispute(false);
    }
  }, [disputeForm.cardlastfour, shouldCreateDispute]);
  

  const addMessage = (text: string, sender: 'user' | 'bot', options?: string[], type: 'text' | 'selection' | 'confirmation' = 'text') => {
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

  const simulateTyping = async (duration: number = 1000) => {
    setIsTyping(true);
    await new Promise(resolve => setTimeout(resolve, duration));
    setIsTyping(false);
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    addMessage(inputText, 'user');
    const userInput = inputText.toLowerCase();
    setInputText('');
    
    await simulateTyping(800);
    processUserInput(userInput);
  };

  const handleOptionClick = async (option: string) => {
    addMessage(option, 'user');
    await simulateTyping(600);
    
    switch (option) {
      case 'Report a Dispute':
        setCurrentStep('select_dispute_type');
        addMessage(
          "I'll help you report a dispute. First, what type of issue are you experiencing?",
          'bot',
          disputeTypes,
          'selection'
        );
        break;
        
      case 'Track Existing Dispute':
        addMessage(
          "Please provide your dispute ID or reference number to track your case.",
          'bot'
        );
        setCurrentStep('track_dispute');
        break;
        
      case 'Get Guidance':
        addMessage(
          "Here are some helpful resources:\n\n• Always contact your bank within 24 hours\n• Gather all transaction evidence\n• File a written complaint\n• Keep records of all communications\n\nWould you like detailed guidance for a specific issue type?",
          'bot',
          ['Yes, specific guidance', 'General tips', 'Back to main menu']
        );
        break;
        
      case 'Emergency Help':
        addMessage(
          "For urgent issues:\n\n🚨 **Immediate Actions:**\n• Block your card: Call your bank's 24/7 helpline\n• Report fraud immediately\n• File police complaint for criminal activities\n\n**SBI**: 1800 1111 109\n**HDFC**: 1800 2611 232\n**ICICI**: 1800 2000 888\n\nDo you need help with a specific bank?",
          'bot',
          banks
        );
        break;
        
      default:
        if (disputeTypes.includes(option)) {
          handleDisputeTypeSelection(option);
        } else if (banks.includes(option)) {
          handleBankSelection(option);
        } else {
          processUserInput(option.toLowerCase());
        }
    }
  };

  const handleDisputeTypeSelection = async (disputeType: string) => {
    setDisputeForm(prev => ({ ...prev, type: disputeType }));
    setCurrentStep('select_bank');
    
    await simulateTyping(500);
    addMessage(
      `You've selected: ${disputeType}\n\nWhich bank is involved in this dispute?`,
      'bot',
      banks,
      'selection'
    );
  };

  const handleBankSelection = async (bank: string) => {
    setDisputeForm(prev => ({ ...prev, bank }));
    setCurrentStep('get_amount');
    
    await simulateTyping(500);
    addMessage(
      `Bank selected: ${bank}\n\nWhat is the disputed amount? (Enter the amount in ₹)`,
      'bot'
    );
  };

  const processUserInput = async (input: string) => {
    switch (currentStep) {
      case 'greeting':
        if (input.includes('hello') || input.includes('hi') || input.includes('help')) {
          addMessage(
            "Great! I can help you with various banking dispute issues. What would you like to do?",
            'bot',
            [
              'Report a Dispute',
              'Track Existing Dispute', 
              'Get Guidance',
              'Emergency Help'
            ]
          );
        } else {
          addMessage(
            "I can help you with banking disputes, tracking cases, and providing guidance. How can I assist you today?",
            'bot',
            [
              'Report a Dispute',
              'Track Existing Dispute',
              'Get Guidance', 
              'Emergency Help'
            ]
          );
        }
        break;

      case 'get_amount':
        const amount = parseFloat(input.replace(/[₹,]/g, ''));
        if (isNaN(amount)) {
          addMessage("Please enter a valid amount in numbers (e.g., 5000)", 'bot');
        } else {
          setDisputeForm(prev => ({ ...prev, amount }));
          setCurrentStep('get_date');
          addMessage(
            `Amount: ₹${amount}\n\nWhen did this transaction occur? (DD/MM/YYYY)`,
            'bot'
          );
        }
        break;

      case 'get_date':
        const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;
        if (!dateRegex.test(input)) {
          addMessage("Please enter the date in DD/MM/YYYY format (e.g., 25/12/2023)", 'bot');
        } else {
          setDisputeForm(prev => ({ ...prev, date: input }));
          setCurrentStep('get_description');
          addMessage(
            `Transaction date: ${input}\n\nPlease provide a brief description of what happened:`,
            'bot'
          );
        }
        break;

      case 'get_description':
        setDisputeForm(prev => ({ ...prev, description: input }));
        setCurrentStep('get_card_details');
        addMessage(
          `Description recorded.\n\nWhat are the last 4 digits of the card involved? (e.g., 1234)`,
          'bot'
        );
        break;

      case 'get_card_details':
        const cardRegex = /^\d{4}$/;
        if (!cardRegex.test(input)) {
          addMessage("Please enter exactly 4 digits (e.g., 1234)", 'bot');
        } else {
          setDisputeForm(prev => ({ ...prev, cardlastfour: input }));
          setShouldCreateDispute(true)
        }
        break;

      case 'track_dispute':
        if (input.length >= 6) {
          addMessage(
            `Searching for dispute ID: ${input.toUpperCase()}\n\n**Status**: Under Review\n**Priority**: Medium\n**Last Updated**: 2 days ago\n**Next Action**: Bank investigation in progress\n\nYou'll receive an SMS update within 3-5 business days.`,
            'bot',
            ['Report New Issue', 'Get Updates', 'Speak to Agent']
          );
        } else {
          addMessage("Please provide a valid dispute ID (at least 6 characters)", 'bot');
        }
        break;

      default:
        addMessage(
          "I'm not sure how to help with that. Let me show you the available options:",
          'bot',
          [
            'Report a Dispute',
            'Track Existing Dispute',
            'Get Guidance',
            'Emergency Help'
          ]
        );
        setCurrentStep('greeting');
    }
  };

  const createDispute = async () => {
    setIsLoading(true);
    await simulateTyping(2000);
    
    const disputeId = `DSP${Date.now().toString().slice(-6)}`;
    const priority = disputeForm.amount && disputeForm.amount > 10000 ? 'high' : 'medium';
    

    const disputePayload : DisputeForm = {
      type: disputeForm.type,
      bank: disputeForm.bank,
      amount: disputeForm.amount,
      date: disputeForm.date,
      description: disputeForm.description,
      cardlastfour: disputeForm.cardlastfour,
    };

    const response  = await axios.post<DisputeForm>(
      `${BASE_URL}/dispute`, 
      disputePayload,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 5000, 
      }
    );

    const apiResponse = response.data;
    console.log("oktest", apiResponse)
    setDisputeForm(prev => ({ ...prev, priority }));
    setCurrentStep('dispute_created');
    addMessage(
      `✅ **Dispute Created Successfully!**\n\n**Dispute ID**: ${disputeId}\n**Type**: ${disputeForm.type}\n**Bank**: ${disputeForm.bank}\n**Amount**: ₹${disputeForm.amount}\n**Priority**: ${priority.toUpperCase()}\n\n**Next Steps:**\n1. Bank will acknowledge within 24 hours\n2. Investigation starts within 3 business days\n3. You'll receive SMS updates\n\n**Important:** Keep all transaction receipts and screenshots safe.`,
      'bot',
      ['Download Summary', 'Get Guidance', 'Track This Dispute', 'Report Another Issue'],
      'confirmation'
    );

    setIsLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-lg border-b border-blue-200 p-4">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-600 p-2 rounded-full">
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-800">Banking Dispute Assistant</h1>
            <p className="text-sm text-gray-600">Secure • Confidential • 24/7 Available</p>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
      >
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
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
                          onClick={() => handleOptionClick(option)}
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
        ))}
        
        {isTyping && (
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
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white px-4 py-3 rounded-2xl shadow-sm border border-gray-200">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                <span className="text-sm text-gray-600">Creating your dispute...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex space-x-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
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
    </div>
  );
};

export default BankingDisputeChatbot;