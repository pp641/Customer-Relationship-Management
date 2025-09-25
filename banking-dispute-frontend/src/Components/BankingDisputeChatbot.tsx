import React, { useState, useEffect } from 'react';
import { Building2 } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { useChat } from '../hooks/useChat';
import { useDisputeForm } from '../hooks/useDisputeForm';
import { DISPUTE_TYPES, BANKS, EMERGENCY_CONTACTS, MAIN_MENU_OPTIONS } from '../Constants/index';
import { 
  isValidAmount, 
  isValidDate, 
  isValidCardDigits, 
  isDisputeType, 
  isBank, 
  formatCurrency 
} from '../utils/chatHelpers';

const BankingDisputeChatbot: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [shouldCreateDispute, setShouldCreateDispute] = useState(false);

  const {
    messages,
    currentStep,
    isTyping,
    messagesEndRef,
    setCurrentStep,
    addMessage,
    simulateTyping
  } = useChat();

  const {
    disputeForm,
    isLoading,
    updateForm,
    createDispute,
    getDisputeById
  } = useDisputeForm();

  // Handle dispute creation when form is complete
  useEffect(() => {
    if (shouldCreateDispute && disputeForm.cardlastfour) {
      handleCreateDispute();
      setShouldCreateDispute(false);
    }
  }, [disputeForm.cardlastfour, shouldCreateDispute]);

  const handleCreateDispute = async () => {
    try {
      const disputeId = await createDispute();
      setCurrentStep('dispute_created');
      
      addMessage(
        `✅ **Dispute Created Successfully!**\n\n` +
        `**Dispute ID**: ${disputeId}\n` +
        `**Type**: ${disputeForm.type}\n` +
        `**Bank**: ${disputeForm.bank}\n` +
        `**Amount**: ${formatCurrency(disputeForm.amount!)}\n` +
        `**Priority**: ${disputeForm.priority?.toUpperCase()}\n\n` +
        `**Next Steps:**\n` +
        `1. Bank will acknowledge within 24 hours\n` +
        `2. Investigation starts within 3 business days\n` +
        `3. You'll receive SMS updates\n\n` +
        `**Important:** Keep all transaction receipts and screenshots safe.`,
        'bot',
        ['Download Summary', 'Get Guidance', 'Track This Dispute', 'Report Another Issue'],
        'confirmation'
      );
    } catch (error) {
      addMessage(
        "Sorry, there was an error creating your dispute. Please try again or contact support.",
        'bot',
        ['Try Again', 'Contact Support', 'Back to Main Menu']
      );
    }
  };

  const handleTrackDispute = async (input: string) => {
    if (input.length < 6) {
      addMessage("Please provide a valid dispute ID (at least 6 characters)", 'bot');
      return;
    }
  
    try {
      addMessage(`🔎 Searching for dispute ID: ${input.toUpperCase()}...`, 'bot');
      const disputeresponse = await getDisputeById(input.toUpperCase());
  
      if (!disputeresponse) {
        addMessage(
          `❌ No dispute found with ID: ${input.toUpperCase()}.`,
          'bot',
          ['Try Again', 'Report New Issue', 'Back to Main Menu']
        );
        return;
      }
       const  {dispute} = disputeresponse
      addMessage(
        `📄 **Dispute Details:**\n\n` +
        `**Dispute ID**: ${dispute.id}\n` +
        `**Type**: ${dispute.type}\n` +
        `**Bank**: ${dispute.bank}\n` +
        `**Amount**: ${formatCurrency(dispute.amount)}\n` +
        `**Status**: ${dispute.status || 'Under Review'}\n` +
        `**Priority**: ${dispute.priority?.toUpperCase() || 'Not Set'}\n` +
        `**Last Updated**: ${dispute.createdAt || 'Recently'}\n\n` +
        `You'll continue to receive SMS/email updates.`,
        'bot',
        ['Report New Issue', 'Get Updates', 'Speak to Agent']
      );
  
    } catch (error) {
      addMessage(
        "⚠️ Sorry, I couldn’t fetch the dispute details. Please try again later or contact support.",
        'bot',
        ['Try Again', 'Contact Support', 'Back to Main Menu']
      );
    }
  };
  



  


  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    addMessage(inputText, 'user');
    const userInput = inputText.toLowerCase();
    setInputText('');
    
    await simulateTyping(800);
    await processUserInput(userInput);
  };

  const handleOptionClick = async (option: string) => {
    addMessage(option, 'user');
    await simulateTyping(600);
    
    // Handle main menu options
    if (MAIN_MENU_OPTIONS.includes(option as any)) {
      await handleMainMenuOption(option);
      return;
    }

    if (isDisputeType(option)) {
      await handleDisputeTypeSelection(option);
      return;
    }

    if (isBank(option)) {
      await handleBankSelection(option);
      return;
    }

    // Handle other options
    await processUserInput(option.toLowerCase());
  };

  const handleMainMenuOption = async (option: string) => {
    switch (option) {
      case 'Report a Dispute':
        setCurrentStep('select_dispute_type');
        addMessage(
          "I'll help you report a dispute. First, what type of issue are you experiencing?",
          'bot',
          [...DISPUTE_TYPES],
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
          "Here are some helpful resources:\n\n" +
          "• Always contact your bank within 24 hours\n" +
          "• Gather all transaction evidence\n" +
          "• File a written complaint\n" +
          "• Keep records of all communications\n\n" +
          "Would you like detailed guidance for a specific issue type?",
          'bot',
          ['Yes, specific guidance', 'General tips', 'Back to main menu']
        );
        break;
        
      case 'Emergency Help':
        const emergencyText = "For urgent issues:\n\n" +
          "🚨 **Immediate Actions:**\n" +
          "• Block your card: Call your bank's 24/7 helpline\n" +
          "• Report fraud immediately\n" +
          "• File police complaint for criminal activities\n\n" +
          Object.entries(EMERGENCY_CONTACTS)
            .map(([bank, number]) => `**${bank}**: ${number}`)
            .join('\n') +
          "\n\nDo you need help with a specific bank?";
        
        addMessage(emergencyText, 'bot', [...BANKS]);
        break;
    }
  };

  const handleDisputeTypeSelection = async (disputeType: string) => {
    updateForm('type', disputeType);
    setCurrentStep('select_bank');
    
    await simulateTyping(500);
    addMessage(
      `You've selected: ${disputeType}\n\nWhich bank is involved in this dispute?`,
      'bot',
      [...BANKS],
      'selection'
    );
  };

  const handleBankSelection = async (bank: string) => {
    updateForm('bank', bank);
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
        await handleGreeting(input);
        break;

      case 'get_amount':
        await handleAmountInput(input);
        break;

      case 'get_date':
        await handleDateInput(input);
        break;

      case 'get_description':
        await handleDescriptionInput(input);
        break;

      case 'get_card_details':
        await handleCardDetailsInput(input);
        break;

      case 'track_dispute':
        await handleTrackDispute(input);
        break;

      default:
        addMessage(
          "I'm not sure how to help with that. Let me show you the available options:",
          'bot',
          [...MAIN_MENU_OPTIONS]
        );
        setCurrentStep('greeting');
    }
  };

  const handleGreeting = async (input: string) => {
    if (input.includes('hello') || input.includes('hi') || input.includes('help')) {
      addMessage(
        "Great! I can help you with various banking dispute issues. What would you like to do?",
        'bot',
        [...MAIN_MENU_OPTIONS]
      );
    } else {
      addMessage(
        "I can help you with banking disputes, tracking cases, and providing guidance. How can I assist you today?",
        'bot',
        [...MAIN_MENU_OPTIONS]
      );
    }
  };

  const handleAmountInput = async (input: string) => {
    if (!isValidAmount(input)) {
      addMessage("Please enter a valid amount in numbers (e.g., 5000)", 'bot');
      return;
    }

    const amount = parseFloat(input.replace(/[₹,]/g, ''));
    updateForm('amount', amount);
    setCurrentStep('get_date');
    addMessage(
      `Amount: ${formatCurrency(amount)}\n\nWhen did this transaction occur? (DD/MM/YYYY)`,
      'bot'
    );
  };

  const handleDateInput = async (input: string) => {
    if (!isValidDate(input)) {
      addMessage("Please enter the date in DD/MM/YYYY format (e.g., 25/12/2023)", 'bot');
      return;
    }

    updateForm('date', input);
    setCurrentStep('get_description');
    addMessage(
      `Transaction date: ${input}\n\nPlease provide a brief description of what happened:`,
      'bot'
    );
  };

  const handleDescriptionInput = async (input: string) => {
    updateForm('description', input);
    setCurrentStep('get_card_details');
    addMessage(
      `Description recorded.\n\nWhat are the last 4 digits of the card involved? (e.g., 1234)`,
      'bot'
    );
  };

  const handleCardDetailsInput = async (input: string) => {
    if (!isValidCardDigits(input)) {
      addMessage("Please enter exactly 4 digits (e.g., 1234)", 'bot');
      return;
    }

    updateForm('cardlastfour', input);
    setShouldCreateDispute(true);
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
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onOptionClick={handleOptionClick}
          />
        ))}
        
        {(isTyping || isLoading) && (
          <TypingIndicator
            isLoading={isLoading}
            loadingText="Creating your dispute..."
          />
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <ChatInput
        inputText={inputText}
        setInputText={setInputText}
        onSendMessage={handleSendMessage}
        isDisabled={isLoading}
      />
    </div>
  );
};

export default BankingDisputeChatbot;