export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: "text" | "data";
  sql?: string;
  data?: Record<string, unknown>[];
  columns?: string[];
  rowCount?: number;
  executionTime?: number;
  suggestions?: string[];
}

export interface ChatResponse {
  type: "data" | "text";
  sql?: string;
  data?: Record<string, unknown>[];
  columns?: string[];
  row_count?: number;
  execution_time?: number;
  analysis: string;
  suggestions?: string[];
  error?: string;
}
