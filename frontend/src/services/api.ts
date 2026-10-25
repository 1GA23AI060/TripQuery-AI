import type { DocumentItem, QueryResponse, HealthResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`);
  }
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
  }

  return res.json();
}

export async function getDocuments(): Promise<DocumentItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/documents`);
  if (!res.ok) {
    throw new Error(`Failed to fetch documents: ${res.status}`);
  }
  return res.json();
}

export async function deleteDocument(id: number): Promise<{ message: string; id: number }> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete document: ${res.status}`);
  }
  return res.json();
}

export async function askQuestion(
  question: string,
  documentIds?: number[]
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: question.trim(),
      document_ids: documentIds && documentIds.length > 0 ? documentIds : undefined,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Query failed with status ${res.status}`);
  }

  return res.json();
}

export async function loadDemoSampleFile(): Promise<File> {
  // Fetch Bali_Travel_Guide.pdf from public
  const res = await fetch('/Bali_Travel_Guide.pdf');
  if (!res.ok) {
    // Fallback to text file if pdf not served
    const txtRes = await fetch('/Bali_Travel_Guide.txt');
    const blob = await txtRes.blob();
    return new File([blob], 'Bali_Travel_Guide.txt', { type: 'text/plain' });
  }
  const blob = await res.blob();
  return new File([blob], 'Bali_Travel_Guide.pdf', { type: 'application/pdf' });
}
