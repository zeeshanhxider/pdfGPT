// Type definitions for the application

export interface PDFUploadResponse {
  success: boolean;
  message: string;
  document_id: string;
  filename: string;
  pages_processed: number;
  chunks_created: number;
}

export interface ChatRequest {
  message: string;
  document_id?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  sources: string[];
  confidence: number;
  processing_time: number;
}

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  sources?: string[];
  confidence?: number;
}

export interface Document {
  id: string;
  filename: string;
  upload_date: Date;
  pages_processed: number;
  chunks_created: number;
}

export interface UploadStatus {
  uploading: boolean;
  progress: number;
  filename: string;
  error?: string;
}
