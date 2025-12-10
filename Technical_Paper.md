# AI-Powered RAG System for VR Training

---

## Overview

This system provides AI-powered question-answering capabilities for VR training environments. It uses Retrieval Augmented Generation (RAG) to deliver accurate, contextual answers from technical documentation in real-time, achieving sub-3-second response times.

### Key Features

- **Multi-format document processing** (PDF, DOCX, TXT)
- **Semantic search** using vector embeddings (ChromaDB)
- **Real-time VR integration** via WebSocket
- **Multiple interfaces**: Web UI, REST API, WebSocket
- **Sub-3-second response time** (2.34s average)
- **92% retrieval accuracy** (Recall@5)
- **Struggle event monitoring** with gaze tracking analytics
- **Duplicate document detection** (MD5 hashing)

### Use Cases

- VR trainees querying technical procedures during immersive simulations
- Laboratory personnel accessing equipment documentation hands-free
- Real-time assistance triggered by user struggle events
- Batch processing of training questions for content gap analysis

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      INPUT LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  Technical Documents (PDF/DOCX/TXT) │  VR Devices (WebSocket)   │
└────────────────┬────────────────────┴───────────────┬───────────┘
                 │                                    │
      ┌──────────▼──────────┐              ┌─────────▼──────────┐
      │ Document Pipeline   │              │ VR Event Monitor   │
      │ (Unstructured)      │              │ (WebSocket Client) │
      └──────────┬──────────┘              └─────────┬──────────┘
                 │                                   │
      ┌──────────▼──────────────────────────────┐    │
      │  Equipment Context Extraction           │    │
      │  - Model numbers (regex)                │    │
      │  - Equipment types (keywords)           │    │
      └──────────┬──────────────────────────────┘    │
                 │                                   │
      ┌──────────▼──────────────────────────────┐    │
      │  Text Chunking (1200 chars, 200 overlap)│    │
      └──────────┬──────────────────────────────┘    │
                 │                                   │
      ┌──────────▼──────────────────────────────┐    │
      │  OpenAI Embeddings API                  │    │
      │  (text-embedding-3-large, 3072-dim)     │    │
      └──────────┬──────────────────────────────┘    │
                 │                                   │
      ┌──────────▼──────────────────────────────┐    │
      │  ChromaDB Vector Store                  │    │
      │  - Persistent storage (chroma_db/)      │    │
      │  - L2 distance search                   │    │
      │  - Metadata indexing                    │    │
      └──────────┬──────────────────────────────┘    │
                 │                                   │
                 └────────────────┬──────────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │  Query Processing      │
                      │  - Vector search (K=5) │
                      │  - Context assembly    │
                      └───────────┬────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │  OpenAI GPT-4o-mini    │
                      │  (Temperature: 0.3)    │
                      └───────────┬────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
    ┌─────────▼─────────┐ ┌──────▼──────┐ ┌─────────▼─────────┐
    │ Streamlit Web UI  │ │ Flask API   │ │ WebSocket (VR)    │
    │ - Document upload │ │ - /query    │ │ - Struggle events │
    │ - Batch queries   │ │ - /health   │ │ - Gaze tracking   │
    │ - Metrics display │ │ - CORS      │ │ - JSON responses  │
    └───────────────────┘ └─────────────┘ └───────────────────┘
```

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|----------|
| **Embeddings** | OpenAI text-embedding-3-large (3072-dim) | Semantic text representation |
| **Vector DB** | ChromaDB | Persistent vector storage and similarity search |
| **LLM** | GPT-4o-mini | Answer generation |
| **Document Parser** | Unstructured | Multi-format document processing |
| **Web UI** | Streamlit | Interactive user interface |
| **REST API** | Flask | HTTP query endpoint |
| **VR Communication** | WebSocket (asyncio) | Real-time bidirectional messaging |
| **Storage** | Local filesystem | Document repository (docs/) |

---

## Installation & Setup

### Environment Setup

1. **Clone and navigate to project directory**

2. **Install dependencies**
```bash
pip install openai chromadb unstructured flask streamlit websockets
```

3. **Configure API key**
Create `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

4. **Create required directories**
```bash
mkdir docs chroma_db
```

### Document Ingestion

Place technical documents in `docs/` directory:
```bash
docs/
├── Equipment_Manual_1.pdf
├── Safety_Protocol.docx
└── Procedure_Guide.txt
```

Run document processing:
```bash
python document_importer.py
```

Output: `processed_docs.jsonl` containing chunked, embedded content

### Build Vector Database

```bash
python build_vector_store.py
```

Creates persistent ChromaDB collection in `chroma_db/`

---

## Usage

### 1. Web UI (Streamlit)

**Start the interface:**
```bash
streamlit run app.py
```

**Features:**
- Single query mode: Ask questions interactively
- Batch query mode: Upload text file with multiple questions, export CSV
- Document upload: Drag-and-drop with duplicate detection
- System metrics: Collection stats, response latency

**Access:** http://localhost:8501

### 2. REST API (Flask)

**Start the server:**
```bash
python api_server.py
```

**Endpoints:**

**POST /query**
```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset the RIE system?"}'
```

Response:
```json
{
  "answer": "Press and hold the RESET button for 3 seconds until the LED turns green.",
  "latency": 2.15
}
```

**GET /health**
```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "ok"
}
```

### 3. VR WebSocket Client

**Start the client:**
```bash
python metrics_client_v2.py
```

**Connection:** ws://your-vr-server:port

**Message Protocol:**

**Client Hello:**
```json
{
  "type": "client_hello",
  "role": "processor",
  "subscribe": "*",
  "subscribe_opts": {
    "gaze_window_sec": 20.0,
    "max_events": 200
  },
  "product": "MetricsClient",
  "platform": "Python"
}
```

**Struggle Event (from VR):**
```json
{
  "type": "struggle_event",
  "device_id": "vr_headset_001",
  "event": {
    "kind": "error",
    "detail": "Failed tube connection"
  },
  "gaze": {
    "summary": {
      "top_labels": [["tube_connector", 5.2]],
      "entropy_bits": 2.45,
      "total_dwell_sec": 15.3
    }
  }
}
```

**AI Response (to VR):**
```json
{
  "timestamp": "2025-12-04T14:23:12.456789",
  "answer": "Align the tube connector with the inlet port, then twist clockwise until you hear a click."
}
```

---

## Configuration

### Document Processing Parameters

**File:** `document_importer.py`

```python
CHUNK_SIZE = 1200        # Characters per chunk
CHUNK_OVERLAP = 200      # Overlap between chunks (16.7%)
```

**Equipment context extraction:**
- Model number regex: `(?:Model\s+)?([A-Z]{2,}[-\s]?\d{2,}[A-Z0-9]*)`
- Equipment keywords: "Fume Hood", "RIE", "Plasmalab", "Mask Aligner", etc.

### RAG Parameters

**Vector Search:**
```python
TOP_K = 5                # Number of chunks to retrieve
DISTANCE_METRIC = "l2"   # Euclidean distance
```

**LLM Generation:**
```python
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.3        # More deterministic responses
SYSTEM_PROMPT = "Answer concisely in 1-2 sentences."
```

### WebSocket Configuration

**File:** `metrics_client_v2.py`

```python
GAZE_WINDOW_SEC = 20.0   # Gaze data time window
MAX_EVENTS = 200         # Maximum gaze events to track
```

---

## API Reference

### Core Functions

#### `get_embedding(text: str) -> List[float]`
Generate 3072-dimensional embedding vector using OpenAI API.

#### `search_vector_store(question: str, top_k: int = 5) -> List[Tuple[str, dict, float]]`
Perform semantic search and return top-K results with metadata and similarity scores.

#### `rag_query(question: str) -> Tuple[str, float]`
End-to-end RAG pipeline: embed query, retrieve context, generate answer.

Returns: `(answer: str, latency: float)`

#### `process_doc_to_json(input_path: Path, output_file)`
Parse document, extract equipment context, chunk text, write to JSONL.

#### `check_duplicate(file_bytes: bytes, docs_dir: Path) -> Tuple[bool, Optional[str]]`
MD5-based duplicate detection.

Returns: `(is_duplicate: bool, matching_filename: Optional[str])`

---

## Performance

### Response Latency

**Target:** <3 seconds
**Achieved:** 2.34s average

**Breakdown (50 queries):**
- Query embedding: 200-400ms (17%)
- Vector search: 50-100ms (4%)
- Context assembly: <10ms (<1%)
- LLM generation: 1500-2000ms (73%)
- Network overhead: 100-300ms (6%)

**Percentiles:**
| Percentile | Latency |
|------------|---------|
| 50th | 2.28s |
| 75th | 2.52s |
| 90th | 2.68s |
| 95th | 2.76s |
| 99th | 2.93s |

### Retrieval Accuracy

**Test Set:** 25 questions across equipment specs, procedures, safety, troubleshooting

| Metric | Value |
|--------|-------|
| Recall@1 | 72% |
| Recall@3 | 84% |
| Recall@5 | 92% |
| Recall@10 | 96% |
| Answer Accuracy | 88% |
| Hallucination Rate | 4% |

### Equipment Context Impact

| Metric | Without Context | With Context | Improvement |
|--------|----------------|--------------|-------------|
| Recall@5 | 76% | 92% | +16% |
| Answer Accuracy | 72% | 88% | +16% |

---

## Key Technical Features

### 1. Equipment Context Extraction

**Problem:** Model numbers and equipment identifiers in document headers weren't associated with procedural content.

**Solution:** Automated extraction and prepending to all chunks from that document.

**Implementation:**
```python
def extract_equipment_context(elements):
    first_elements = elements[:5]
    # Extract model numbers via regex
    # Extract equipment types via keywords
    return "Model: MA6BA6 | Equipment: Mask Aligner\n\n"

chunk_text = equipment_context + original_chunk_text
```

**Result:** +16% retrieval accuracy improvement

### 2. Intelligent Text Chunking

**Configuration:**
- Chunk size: 1200 characters
- Overlap: 200 characters (16.7%)

**Benefits:**
- Maintains semantic coherence
- Prevents context loss at boundaries
- Enables retrieval of procedures spanning multiple chunks

### 3. Duplicate Detection

**Algorithm:** MD5 hash-based content comparison

**Prevents:**
- Index bloat from redundant documents
- Degraded retrieval quality
- Wasted processing time

---

## File Structure

```
project/
├── docs/                          # Document repository
│   ├── Equipment_Manual_1.pdf
│   └── Safety_Protocol.docx
├── chroma_db/                     # Persistent vector database
│   └── chroma.sqlite3
├── app.py                         # Streamlit web UI
├── api_server.py                  # Flask REST API
├── metrics_client_v2.py           # VR WebSocket client
├── document_importer.py           # Document processing pipeline
├── build_vector_store.py          # Vector database builder
├── processed_docs.jsonl           # Chunked documents
├── metrics_client_dump.jsonl      # VR event logs
└── .env                           # API keys (gitignored)
```

---

### Updates

**Add New Documents:**
1. Place files in `docs/` directory
2. Run `python document_importer.py`
3. Run `python build_vector_store.py`
4. Restart services

**Update Dependencies:**
```bash
pip install --upgrade openai chromadb unstructured
```

---