export type HourlyTrendData = {
  time_slot: string;
  count: number;
};

export type Message = { 
  sender: string; 
  content: string; 
  ts: number 
}

export type StreamMessage = { 
  id: string; 
  session_id: string; 
  sender: string; 
  content: string; 
  ts: string; 
  deleted?: string 
}

export type DeletedMessage = {
  content: string;
  deleted_at: number;  
  ts: number;          
  sender?: string;
  session_id?: string;
};


export type SessionId = string;