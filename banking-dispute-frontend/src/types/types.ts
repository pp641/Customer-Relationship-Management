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


export interface DisputeInterfaceResponse { 
  id : string;
  type : string;
  amount : number;
  date : string;
  description : string;
  status : string;
  priority : string;
  bank : string;
  cardlastfour : string;
  createdAt : string;

}

export interface DisputeTimeline {
  date : string;
  status : string;
  description : string;
}

export interface DisputeApiResponse {
  dispute : DisputeInterfaceResponse;
  timeline : DisputeTimeline[];
}

