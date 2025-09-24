export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
    options?: string[];
    type?: 'text' | 'selection' | 'confirmation';
  }
  
  export interface DisputeForm {
    type?: string;
    bank?: string;
    amount?: number;
    date?: string;
    description?: string;
    cardlastfour?: string;
    priority?: 'low' | 'medium' | 'high';
  }
  
  export type ChatStep = 
    | 'greeting' 
    | 'select_dispute_type' 
    | 'select_bank' 
    | 'get_amount' 
    | 'get_date' 
    | 'get_description' 
    | 'get_card_details' 
    | 'track_dispute' 
    | 'dispute_created';