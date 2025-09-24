import { DISPUTE_TYPES, BANKS } from '../Constants/index';

export const generateDisputeId = (): string => {
  return `DSP${Date.now().toString().slice(-6)}`;
};

export const calculatePriority = (amount?: number): 'low' | 'medium' | 'high' => {
  if (!amount) return 'medium';
  if (amount > 50000) return 'high';
  if (amount > 10000) return 'medium';
  return 'low';
};

export const isValidAmount = (input: string): boolean => {
  const amount = parseFloat(input.replace(/[₹,]/g, ''));
  return !isNaN(amount) && amount > 0;
};

export const isValidDate = (input: string): boolean => {
  const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;
  return dateRegex.test(input);
};

export const isValidCardDigits = (input: string): boolean => {
  const cardRegex = /^\d{4}$/;
  return cardRegex.test(input);
};

export const isDisputeType = (option: string): boolean => {
  return DISPUTE_TYPES.includes(option as any);
};

export const isBank = (option: string): boolean => {
  return BANKS.includes(option as any);
};

export const formatCurrency = (amount: number): string => {
  return `₹${amount.toLocaleString()}`;
};