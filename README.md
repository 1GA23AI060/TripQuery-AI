# ✈️ TripQuery AI

> **Intelligent RAG Travel Document Assistant**  
> *Upload a destination guide, itinerary, or tourism PDF and ask questions. TripQuery AI retrieves the relevant passages and generates answers grounded strictly in your documents.*

---

## 🌟 Overview & Architecture

TripQuery AI is a lightweight, full-stack Retrieval-Augmented Generation (RAG) web application tailored for **Travel & Destination Guides**. 

Designed for university hackathons, it follows a simple, transparent, and grounded 4-step workflow:
```
📄 UPLOAD → 🔍 ASK → 🤖 ANSWER → 📚 SOURCE
```

```
[ Travel Document (PDF / TXT / DOCX) ]
                 ↓
      [ Text & Page Extraction ]
                 ↓
     [ Chunking (500-800 words) ]
                 ↓
  [ Embeddings (all-MiniLM-L6-v2) ]
                 ↓
         [ FAISS Vector Store ]
                 ↕
  [ Question Embedding & Top-K Search ]
                 ↓
[ Grounded Context & System Prompt to LLM ]
                 ↓
  [ Answer + Page Citations + Relevance ]
```

---

## 🚀 Quick Start

### 1. Launch Everything with 1 Click
Double click:
```powershell
start_all.bat
```

Or run frontend and backend separately:

### Backend Setup & Run
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python run.py
```
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

### Frontend Setup & Run
```powershell
cd frontend
npm install
npm run dev
```
- **Frontend UI**: `http://localhost:5173`

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Vanilla CSS Design System, Lucide Icons |
| **Backend** | Python 3.14 / FastAPI, Uvicorn |
| **Database** | SQLite + SQLAlchemy (`backend/tripquery.db`) |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| **Vector Store** | FAISS / Optimized In-Memory Cosine Projection with Disk Persistence |
| **Document Parsers** | `pypdf`, `python-docx`, UTF-8/Latin-1 text parsers with page preservation |
| **LLM Provider** | OpenAI API compatible (with deterministic zero-hallucination extractive fallback) |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service and vector store connectivity health check |
| `POST` | `/api/documents/upload` | Upload PDF, TXT, or DOCX travel guides and index vectors |
| `GET` | `/api/documents` | List all uploaded travel guides and metadata |
| `GET` | `/api/documents/{id}` | Get document chunks and details |
| `DELETE` | `/api/documents/{id}` | Delete document, chunks, and remove vectors |
| `POST` | `/api/query` | RAG query endpoint returning grounded answer and source citations |

---

## 🧪 Sample Testing Guide

A rich 5-page sample travel guide is included in:
- `backend/data/demo/Bali_Travel_Guide.txt`
- `backend/data/demo/Bali_Travel_Guide.pdf`

You can test by clicking the **"⚡ Try with Demo Guide (Bali Travel Guide)"** button directly in the web UI or dragging & dropping any travel PDF.
