import type { GuidanceStep,  FormData  } from './types';

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

export const TABS = [
  { id: 'report' as const, label: 'Report Issue', icon: 'AlertCircle' },
  { id: 'guidance' as const, label: 'Guidance & Templates', icon: 'FileText' },
  { id: 'track' as const, label: 'Track Disputes', icon: 'Clock' }
] as const;

export const EVIDENCE_CHECKLIST = [
  'Bank statement showing the transaction',
  'SMS alerts from bank',
  'Transaction receipt/screenshot',
  'Card blocking confirmation',
  'Communication with merchant',
  'Police complaint (for fraud)',
  'Any other relevant documents'
] as const;

export const STATUS_COLORS = {
  submitted: 'bg-blue-100 text-blue-800',
  under_review: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
  escalated: 'bg-red-100 text-red-800'
} as const;

export const PRIORITY_COLORS = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-orange-100 text-orange-800',
  high: 'bg-red-100 text-red-800'
} as const;

// Utility function to determine priority based on amount
export const calculatePriority = (amount: number): 'low' | 'medium' | 'high' => {
  if (amount > 50000) return 'high';
  if (amount > 10000) return 'medium';
  return 'low';
};

// Generate guidance steps based on dispute type
export const generateGuidance = (type: string): GuidanceStep[] => {
  const baseSteps: GuidanceStep[] = [
    {
      step: 1,
      title: "Immediate Action",
      description: "Contact your bank immediately to report the issue",
      action: "Call bank customer care within 24 hours"
    },
    {
      step: 2,
      title: "Gather Evidence",
      description: "Collect all relevant documents and screenshots",
      action: "Take screenshots, save SMS alerts, transaction receipts"
    },
    {
      step: 3,
      title: "File Written Complaint",
      description: "Submit formal complaint to bank",
      template: "formal_complaint"
    }
  ];

  const specificSteps: { [key: string]: GuidanceStep[] } = {
    'Double Debit / Duplicate Charge': [
      ...baseSteps,
      {
        step: 4,
        title: "Request Transaction Reversal",
        description: "Ask for immediate reversal of duplicate charge",
        template: "reversal_request"
      },
      {
        step: 5,
        title: "Follow Up",
        description: "Bank should resolve within 7-10 working days",
        action: "Track complaint reference number"
      }
    ],
    'Unauthorized Transaction': [
      ...baseSteps,
      {
        step: 4,
        title: "Block Card Immediately",
        description: "Request immediate card blocking to prevent further fraud",
        action: "Call bank hotline to block card"
      },
      {
        step: 5,
        title: "File Police Complaint",
        description: "For amounts above ₹25,000, file FIR",
        template: "police_complaint"
      },
      {
        step: 6,
        title: "Chargeback Request",
        description: "Request chargeback from bank",
        template: "chargeback_request"
      }
    ],
    'Missing Refund': [
      ...baseSteps,
      {
        step: 4,
        title: "Contact Merchant",
        description: "First contact the merchant for refund status",
        template: "merchant_query"
      },
      {
        step: 5,
        title: "Bank Refund Request",
        description: "If merchant doesn't respond in 7 days",
        template: "refund_request"
      }
    ]
  };

  return specificSteps[type] || baseSteps;
};

// Generate email templates
export const getTemplate = (templateType: string, disputeType: string, formData: FormData): string => {
  const templates: { [key: string]: string } = {
    formal_complaint: `Subject: Formal Complaint - ${disputeType}

Dear Sir/Madam,

I am writing to file a formal complaint regarding a ${disputeType.toLowerCase()} on my account.

Transaction Details:
- Date: ${formData.date}
- Amount: ₹${formData.amount}
- Card ending: xxxx${formData.cardLast4}
- Description: ${formData.description}

I request immediate investigation and resolution of this matter within the stipulated timeframe as per RBI guidelines.

Please provide a complaint reference number for tracking.

Regards,
[Your Name]
[Account Number]
[Contact Details]`,

    chargeback_request: `Subject: Chargeback Request - Unauthorized Transaction

Dear Chargeback Team,

I request a chargeback for the following unauthorized transaction:

Transaction Details:
- Date: ${formData.date}
- Amount: ₹${formData.amount}
- Merchant: [Merchant Name]
- Card: xxxx${formData.cardLast4}

Reason: Unauthorized transaction - I did not authorize this payment.

Evidence Attached:
- Bank statement
- Card blocking confirmation
- Police complaint (if applicable)

Please process this chargeback under Visa/Mastercard dispute resolution.

Thank you,
[Your Name]`,

    reversal_request: `Subject: Request for Transaction Reversal - Duplicate Charge

Dear Team,

I request immediate reversal of a duplicate charge on my account:

Original Transaction: ₹${formData.amount} on ${formData.date}
Duplicate Transaction: ₹${formData.amount} on ${formData.date}

Total Amount to be Reversed: ₹${formData.amount}

This appears to be a system error resulting in double billing.

Please reverse the duplicate amount immediately.

Regards,
[Your Name]`
  };

  return templates[templateType] || '';
};

// Local storage utilities
export const saveDisputes = (disputes: any[]) => {
  localStorage.setItem('banking-disputes', JSON.stringify(disputes));
};

export const loadDisputes = () => {
  const savedDisputes = localStorage.getItem('banking-disputes');
  return savedDisputes ? JSON.parse(savedDisputes) : [];
};
