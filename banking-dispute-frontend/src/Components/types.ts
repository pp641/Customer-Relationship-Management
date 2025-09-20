export interface DisputeData {
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
  
  export interface GuidanceStep {
    step: number;
    title: string;
    description: string;
    action?: string;
    template?: string;
    completed?: boolean;
  }
  
  export interface FormData {
    type: string;
    amount: string;
    date: string;
    description: string;
    bank: string;
    cardLast4: string;
    transactionId: string;
  }
  
  export type TabType = 'report' | 'guidance' | 'track';
  
  export type StatusType = 'submitted' | 'under_review' | 'resolved' | 'escalated';
  export type PriorityType = 'low' | 'medium' | 'high';
  