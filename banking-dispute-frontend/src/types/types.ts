import { AlertCircle, Clock, FileText } from "lucide-react";

interface GuidanceStep {
    step: number;
    title: string;
    description: string;
    action?: string;
    template?: string;
    completed?: boolean;
  }
  
  interface DisputeData {
    id: string;
    type: string;
    amount: number;
    date: string;
    description: string;
    status: 'submitted' | 'under_review' | 'resolved' | 'escalated';
    priority: 'low' | 'medium' | 'high';
    bank: string;
    cardLast4: string;
    createdAt: string;
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


  const TABS = [
    { id: 'report', label: 'Report Issue', icon: AlertCircle },
    { id: 'guidance', label: 'Guidance & Templates', icon: FileText },
    { id: 'track', label: 'Track Disputes', icon: Clock },
  ]

  export type { GuidanceStep, DisputeData  };
  const banks = [
    'State Bank of India', 'HDFC Bank', 'ICICI Bank', 'Axis Bank', 
    'Punjab National Bank', 'Bank of Baroda', 'Canara Bank', 'Other'
  ];

  export const EVIDENCE_CHECKLIST = [
    'Bank statement showing the transaction',
    'SMS alerts from bank',
    'Transaction receipt/screenshot',
    'Card blocking confirmation',
    'Communication with merchant',
    'Police complaint (for fraud)',
    'Any other relevant documents'
  ]


  export  { disputeTypes , baseSteps , TABS , banks }