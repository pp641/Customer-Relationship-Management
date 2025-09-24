export const BASE_URL = 'http://localhost:8000';

export const DISPUTE_TYPES = [
  'Double Debit / Duplicate Charge',
  'Unauthorized Transaction',
  'Missing Refund',
  'Wrong Balance/Amount',
  'Failed Transaction',
  'ATM Dispute',
  'Merchant Fraud',
  'Card Skimming',
  'Other'
] as const;

export const BANKS = [
  'State Bank of India',
  'HDFC Bank', 
  'ICICI Bank',
  'Axis Bank',
  'Punjab National Bank',
  'Bank of Baroda',
  'Canara Bank',
  'Other'
] as const;

export const EMERGENCY_CONTACTS = {
  'SBI': '1800 1111 109',
  'HDFC': '1800 2611 232',
  'ICICI': '1800 2000 888'
} as const;

export const MAIN_MENU_OPTIONS = [
  'Report a Dispute',
  'Track Existing Dispute',
  'Get Guidance',
  'Emergency Help'
] as const;