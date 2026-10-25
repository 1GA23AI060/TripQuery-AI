export interface DocumentItem {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  page_count: number;
  status: 'processing' | 'ready' | 'error';
  uploaded_at: string;
  chunk_count?: number;
}

export interface SourceItem {
  document_id: number;
  document_name: string;
  page_number: number;
  relevance_score: number;
  retrieved_text: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceItem[];
  question?: string;
  created_at?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  database: string;
  vector_store: string;
  documents_indexed: number;
  chunks_indexed: number;
}

export type UploadStep = 
  | 'idle'
  | 'uploading'
  | 'reading'
  | 'chunking'
  | 'indexing'
  | 'ready'
  | 'error';

export type QueryStep = 
  | 'idle'
  | 'searching'
  | 'finding'
  | 'preparing'
  | 'ready'
  | 'error';
