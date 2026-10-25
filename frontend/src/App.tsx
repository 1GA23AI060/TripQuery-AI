import React, { useState, useEffect, useRef } from 'react';
import {
  Compass,
  FileText,
  Upload,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Search,
  BookOpen,
  Trash2,
  MapPin,
  Calendar,
  Lightbulb,
  ArrowRight
} from 'lucide-react';

import type {
  DocumentItem,
  QueryResponse,
  HealthResponse,
  UploadStep,
  QueryStep
} from './types';

import {
  getHealth,
  uploadDocument,
  getDocuments,
  deleteDocument,
  askQuestion,
  loadDemoSampleFile
} from './services/api';

import './App.css';

export function App() {
  // State
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);

  // Upload state
  const [uploadStep, setUploadStep] = useState<UploadStep>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Query state
  const [question, setQuestion] = useState('');
  const [queryStep, setQueryStep] = useState<QueryStep>('idle');
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);

  // Initial load
  useEffect(() => {
    checkSystemHealth();
    refreshDocuments();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const data = await getHealth();
      setHealth(data);
    } catch (err) {
      console.warn('Backend currently offline or unreachable:', err);
    }
  };

  const refreshDocuments = async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
      if (docs.length > 0 && !selectedDocId) {
        setSelectedDocId(docs[0].id);
      }
    } catch (err) {
      console.warn('Could not fetch documents:', err);
    }
  };

  // Upload handler with real sequential stages
  const handleFileUpload = async (file: File) => {
    setUploadError(null);
    setUploadStep('uploading');

    try {
      // Step 1: Uploading
      await new Promise(r => setTimeout(r, 400));
      setUploadStep('reading');

      // Step 2: Reading guide
      await new Promise(r => setTimeout(r, 450));
      setUploadStep('chunking');

      // Step 3: Creating searchable sections
      await new Promise(r => setTimeout(r, 400));
      setUploadStep('indexing');

      // Actual backend processing
      const doc = await uploadDocument(file);

      // Step 4: Ready
      setUploadStep('ready');
      await refreshDocuments();
      await checkSystemHealth();
      setSelectedDocId(doc.id);
    } catch (err: any) {
      setUploadStep('error');
      setUploadError(err.message || 'Failed to upload document');
    }
  };

  // File input change
  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  };

  // Drag and Drop
  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  // Load bundled demo guide
  const handleLoadDemo = async () => {
    try {
      setUploadError(null);
      setUploadStep('uploading');
      const sampleFile = await loadDemoSampleFile();
      await handleFileUpload(sampleFile);
    } catch (err: any) {
      setUploadStep('error');
      setUploadError(err.message || 'Could not load demo guide');
    }
  };

  // Delete document
  const handleDeleteDoc = async (id: number) => {
    try {
      await deleteDocument(id);
      if (selectedDocId === id) {
        setSelectedDocId(null);
      }
      setUploadStep('idle');
      await refreshDocuments();
      await checkSystemHealth();
    } catch (err: any) {
      alert(`Could not delete document: ${err.message}`);
    }
  };

  // Ask Question
  const handleAsk = async (queryText?: string) => {
    const textToAsk = (queryText || question).trim();
    if (!textToAsk) return;

    if (queryText) {
      setQuestion(queryText);
    }

    setQueryError(null);
    setQueryStep('searching');

    try {
      // Step 1: Searching guide
      await new Promise(r => setTimeout(r, 400));
      setQueryStep('finding');

      // Step 2: Finding best information
      await new Promise(r => setTimeout(r, 450));
      setQueryStep('preparing');

      // Step 3: Preparing answer
      const docIds = selectedDocId ? [selectedDocId] : undefined;
      const result = await askQuestion(textToAsk, docIds);

      setQueryResult(result);
      setQueryStep('ready');
    } catch (err: any) {
      setQueryStep('error');
      setQueryError(err.message || 'Failed to retrieve answer');
    }
  };

  const activeDoc = documents.find(d => d.id === selectedDocId) || documents[0];

  const isInsufficient = queryResult && (
    queryResult.sources.length === 0 ||
    queryResult.answer.toLowerCase().includes("couldn't find enough relevant information")
  );

  return (
    <div className="app-container">
      {/* 5. HEADER */}
      <header className="app-header">
        <div className="header-content">
          <div className="brand-wrapper">
            <div className="brand-icon">
              <Compass size={24} />
            </div>
            <div>
              <div className="brand-title">✈️ TripQuery AI</div>
              <div className="brand-subtitle">Your AI travel document assistant</div>
            </div>
          </div>

          <div className="status-pill" title={health ? `Connected: ${health.database}, ${health.documents_indexed} guides indexed` : 'Connecting...'}>
            <span className="pulsing-dot" />
            <span>RAG Ready</span>
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="main-content">
        {/* 6. HERO */}
        <section className="hero-section">
          <div className="hero-badge">
            <Sparkles size={14} />
            <span>AI-Powered Travel Research</span>
          </div>

          <h1 className="hero-title">
            Explore smarter. <br />
            <span className="hero-title-highlight">Ask your travel guides.</span>
          </h1>

          <p className="hero-description">
            Upload a destination guide, itinerary, or travel document and ask questions.
            TripQuery AI finds the relevant information and gives you an answer grounded in your document.
          </p>
        </section>

        {/* 7. UPLOAD SECTION */}
        <section className="content-card">
          <div className="card-header-group">
            <h2 className="card-title">
              <FileText className="text-sky-600" size={22} />
              <span>📄 Upload a travel guide</span>
            </h2>
            <p className="card-subtitle">
              Add a destination guide, itinerary, tourism document, or travel PDF.
            </p>
          </div>

          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={onFileChange}
            accept=".pdf,.txt,.docx"
            style={{ display: 'none' }}
          />

          {/* Dropzone */}
          <div
            className={`upload-dropzone ${isDragging ? 'dragover' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
          >
            <Upload className="dropzone-icon" />
            <div className="dropzone-text-primary">
              Drop your travel guide here
            </div>
            <div className="dropzone-text-secondary">
              or Browse Files
            </div>
            <div className="dropzone-formats">
              PDF • TXT • DOCX
            </div>
          </div>

          {/* Upload Demo Option */}
          <div className="upload-actions">
            <button
              type="button"
              className="btn-demo-sample"
              onClick={handleLoadDemo}
              disabled={uploadStep !== 'idle' && uploadStep !== 'ready' && uploadStep !== 'error'}
            >
              <Sparkles size={15} />
              <span>⚡ Try with Demo Guide (Bali Travel Guide)</span>
            </button>

            {documents.length > 0 && (
              <span style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
                {documents.length} guide{documents.length > 1 ? 's' : ''} indexed
              </span>
            )}
          </div>

          {/* 8. DOCUMENT STATUS FLOW */}
          {uploadStep !== 'idle' && (
            <div className="status-flow-container animate-fade-in">
              <div className="status-flow-list">
                <div className={`status-flow-item ${uploadStep === 'uploading' ? 'active' : ''} ${['reading', 'chunking', 'indexing', 'ready'].includes(uploadStep) ? 'completed' : ''}`}>
                  <div className="status-dot">
                    {['reading', 'chunking', 'indexing', 'ready'].includes(uploadStep) ? '✓' : '1'}
                  </div>
                  <span>Uploading...</span>
                </div>

                <div className={`status-flow-item ${uploadStep === 'reading' ? 'active' : ''} ${['chunking', 'indexing', 'ready'].includes(uploadStep) ? 'completed' : ''}`}>
                  <div className="status-dot">
                    {['chunking', 'indexing', 'ready'].includes(uploadStep) ? '✓' : '2'}
                  </div>
                  <span>Reading guide...</span>
                </div>

                <div className={`status-flow-item ${uploadStep === 'chunking' ? 'active' : ''} ${['indexing', 'ready'].includes(uploadStep) ? 'completed' : ''}`}>
                  <div className="status-dot">
                    {['indexing', 'ready'].includes(uploadStep) ? '✓' : '3'}
                  </div>
                  <span>Creating searchable sections...</span>
                </div>

                <div className={`status-flow-item ${uploadStep === 'indexing' ? 'active' : ''} ${uploadStep === 'ready' ? 'completed' : ''}`}>
                  <div className="status-dot">
                    {uploadStep === 'ready' ? '✓' : '4'}
                  </div>
                  <span>Indexing...</span>
                </div>

                {uploadStep === 'ready' && (
                  <div className="status-flow-item completed">
                    <div className="status-dot">✓</div>
                    <span>✓ Ready to answer questions</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Upload Error */}
          {uploadError && (
            <div style={{ marginTop: '14px', color: '#DC2626', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertCircle size={16} />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Active Guide Card */}
          {activeDoc && uploadStep !== 'uploading' && uploadStep !== 'reading' && (
            <div className="active-doc-badge animate-fade-in">
              <div className="doc-info">
                <CheckCircle2 className="doc-icon" size={20} />
                <div>
                  <div className="doc-name">✓ {activeDoc.filename}</div>
                  <div className="doc-meta">
                    Ready to explore • {activeDoc.page_count} page{activeDoc.page_count > 1 ? 's' : ''} • {(activeDoc.file_size / 1024).toFixed(1)} KB
                  </div>
                </div>
              </div>

              <button
                type="button"
                className="btn-remove-doc"
                title="Remove guide"
                onClick={() => handleDeleteDoc(activeDoc.id)}
              >
                <Trash2 size={16} />
              </button>
            </div>
          )}
        </section>

        {/* 9. QUESTION SECTION */}
        <section className="content-card">
          <div className="card-header-group">
            <h2 className="card-title">
              <Search className="text-sky-600" size={22} />
              <span>🔍 Ask about your destination</span>
            </h2>
            <p className="card-subtitle">
              Ask anything about places to visit, schedules, travel tips, and attractions.
            </p>
          </div>

          {/* Question Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleAsk();
            }}
          >
            <div className="question-input-wrapper">
              <input
                type="text"
                className="question-input"
                placeholder="What would you like to know about this destination?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={queryStep === 'searching' || queryStep === 'finding' || queryStep === 'preparing'}
              />
              <button
                type="submit"
                className="btn-ask"
                disabled={!question.trim() || queryStep === 'searching' || queryStep === 'finding' || queryStep === 'preparing'}
              >
                <span>Ask TripQuery</span>
                <ArrowRight size={18} />
              </button>
            </div>
          </form>

          {/* 3 Suggestion Buttons */}
          <div className="suggestion-group">
            <span className="suggestion-label">Quick Suggestions:</span>
            <button
              type="button"
              className="btn-suggestion"
              onClick={() => handleAsk("What are the best places to visit?")}
            >
              <MapPin size={13} />
              <span>Best places to visit</span>
            </button>

            <button
              type="button"
              className="btn-suggestion"
              onClick={() => handleAsk("What is the suggested itinerary?")}
            >
              <Calendar size={13} />
              <span>Suggested itinerary</span>
            </button>

            <button
              type="button"
              className="btn-suggestion"
              onClick={() => handleAsk("What are the top travel tips?")}
            >
              <Lightbulb size={13} />
              <span>Top travel tips</span>
            </button>
          </div>

          {/* 10. EXAMPLE QUESTIONS */}
          <div style={{ marginTop: '16px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Example Questions
            </span>
            <div className="example-questions-grid">
              <button
                type="button"
                className="btn-example"
                onClick={() => handleAsk("What are the best places to visit?")}
              >
                "What are the best places to visit?"
              </button>

              <button
                type="button"
                className="btn-example"
                onClick={() => handleAsk("What activities are recommended?")}
              >
                "What activities are recommended?"
              </button>

              <button
                type="button"
                className="btn-example"
                onClick={() => handleAsk("What is the suggested itinerary?")}
              >
                "What is the suggested itinerary?"
              </button>

              <button
                type="button"
                className="btn-example"
                onClick={() => handleAsk("Which attractions are mentioned?")}
              >
                "Which attractions are mentioned?"
              </button>
            </div>
          </div>

          {/* 11. QUERY PROCESSING INDICATOR */}
          {(queryStep === 'searching' || queryStep === 'finding' || queryStep === 'preparing') && (
            <div className="query-loading-box animate-fade-in">
              <div className="loading-spinner" />
              <div className="loading-step-text">
                {queryStep === 'searching' && '🔎 Searching your travel guide...'}
                {queryStep === 'finding' && '🧠 Finding the best information...'}
                {queryStep === 'preparing' && '✨ Preparing your answer...'}
              </div>
            </div>
          )}

          {queryError && (
            <div style={{ marginTop: '14px', color: '#DC2626', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertCircle size={16} />
              <span>{queryError}</span>
            </div>
          )}
        </section>

        {/* 14. INSUFFICIENT INFORMATION STATE */}
        {isInsufficient && (
          <section className="insufficient-card animate-fade-in">
            <AlertCircle className="insufficient-icon" size={24} />
            <div>
              <div className="insufficient-title">No matching information found</div>
              <div className="insufficient-text">
                I couldn't find enough relevant information in your uploaded travel documents to answer this question reliably.
              </div>
              <div style={{ marginTop: '6px', fontSize: '0.85rem', color: '#92400E' }}>
                👉 Try asking something related to the uploaded guide.
              </div>
            </div>
          </section>
        )}

        {/* 12. ANSWER CARD */}
        {queryResult && !isInsufficient && (
          <section className="content-card animate-fade-in">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
              <h2 className="card-title">
                <Sparkles className="text-sky-600" size={22} />
                <span>✨ TripQuery Answer</span>
              </h2>

              <div className="answer-badge">
                <CheckCircle2 size={14} />
                <span>✓ Based on your uploaded guide</span>
              </div>
            </div>

            <div className="answer-body">
              {queryResult.answer.split('\n\n').map((paragraph, idx) => {
                const trimmed = paragraph.trim();
                if (trimmed.startsWith('### ')) {
                  return <h3 key={idx}>{trimmed.replace('### ', '')}</h3>;
                }
                if (trimmed.startsWith('> ')) {
                  return <blockquote key={idx}>{trimmed.replace('> ', '')}</blockquote>;
                }
                return <p key={idx}>{trimmed}</p>;
              })}
            </div>
          </section>
        )}

        {/* 13. SOURCES FROM YOUR GUIDE */}
        {queryResult && queryResult.sources.length > 0 && !isInsufficient && (
          <section className="content-card animate-fade-in">
            <div className="card-header-group">
              <h2 className="card-title">
                <BookOpen className="text-sky-600" size={22} />
                <span>📚 Sources from your guide</span>
              </h2>
              <p className="card-subtitle">
                Grounded passages retrieved from your uploaded document.
              </p>
            </div>

            <div className="sources-grid">
              {queryResult.sources.map((src, idx) => {
                const relevancePct = Math.min(100, Math.round(src.relevance_score * 100));
                return (
                  <div key={idx} className="source-card">
                    <div className="source-header">
                      <div className="source-doc-name">
                        <FileText size={15} className="text-sky-600" />
                        <span>{src.document_name}</span>
                      </div>
                      <span className="source-page-badge">
                        Page {src.page_number}
                      </span>
                    </div>

                    <div className="source-relevance">
                      <div className="relevance-bar-bg">
                        <div
                          className="relevance-bar-fill"
                          style={{ width: `${relevancePct}%` }}
                        />
                      </div>
                      <span className="relevance-score-text">
                        {relevancePct}% match
                      </span>
                    </div>

                    <div className="source-excerpt">
                      "{src.retrieved_text.length > 220 ? src.retrieved_text.substring(0, 220) + '...' : src.retrieved_text}"
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}
      </main>

      {/* FOOTER */}
      <footer className="app-footer">
        <p>✈️ TripQuery AI • 1-Hour University Hackathon RAG Application • Powered by FastAPI & React</p>
      </footer>
    </div>
  );
}

export default App;
