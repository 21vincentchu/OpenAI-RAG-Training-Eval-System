# OpenAI RAG Q&A System

A document question-answering system using RAG (Retrieval Augmented Generation) with ChromaDB vector storage and OpenAI embeddings. Includes a Flask API server for integration with VR applications.

## Features

- Document processing pipeline (PDF, DOCX, etc.) using Unstructured library
- ChromaDB vector store for semantic search
- OpenAI embeddings (text-embedding-3-large) and GPT-4o-mini for responses
- Flask API server with CORS support
- Query response time < 3 seconds
- Equipment context extraction for technical documentation

## Setup

### Prerequisites

- Python 3.8+
- macOS with Homebrew (for optimal functionality)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   cd /path/to/openAIAPITest
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

   Get your API key from: https://platform.openai.com/api-keys

4. **Verify directory structure**
   ```
   openAIAPITest/
   ├── docs/           # Place your source documents here
   ├── processed/      # Auto-generated JSONL files
   ├── chroma_db/      # ChromaDB vector store
   └── .env            # Your API key
   ```

## How to Upload Your Own Documents

### Step 1: Add Your Documents

Place your documents in the `docs/` directory:

```bash
# Copy documents to the docs folder
cp /path/to/your/document.pdf docs/
cp /path/to/your/manual.docx docs/
```

**Supported formats:**
- PDF (.pdf)
- Word Documents (.docx, .doc)
- Text files (.txt)
- And more (see Unstructured library documentation)

### Step 2: Process Documents

Run the data pipeline to convert documents to JSONL and create vector embeddings:

```bash
python Unstructured_data_pipeline.py
```

This will:
1. Parse all documents in `docs/` folder
2. Chunk content with overlap for better retrieval
3. Extract equipment/model context from headers
4. Save processed chunks to `processed/` as JSONL files
5. Generate embeddings and store in ChromaDB (`chroma_db/` folder)

**Note:** Processing time depends on the number and size of documents. Each document requires API calls to generate embeddings.

### Step 3: Verify Processing

Check that your documents were processed successfully:

```bash
python chroma_vector_store.py info
```

This displays the collection name, document count, and storage location.

## How to Use

### Option 1: Command Line Query

**Single question:**
```bash
python chroma_vector_store.py "What is the operating temperature range?"

import the functions from vectorStore and then just call
```

**Batch questions from file:**

Create a text file with questions (one per line):
```bash
# questions.txt
What safety precautions should I follow?
How do I calibrate the equipment?
What is the maintenance schedule?
```

Run batch query:
```bash
python chroma_vector_store.py test_questions1.txt
```

Results are saved to `chroma_query_results.csv`.

### Option 2: Flask API Server

Start the API server:

```bash
python api_server.py
```

The server runs on `http://localhost:5000`

**API Endpoints:**

- `POST /query` - Submit a question
  ```bash
  curl -X POST http://localhost:5000/query \
    -H "Content-Type: application/json" \
    -d '{"question": "How do I operate the fume hood?"}'
  ```

  Response:
  ```json
  {
    "answer": "The answer based on your documents...",
    "latency": 1.234
  }
  ```

- `GET /health` - Check server status
  ```bash
  curl http://localhost:5000/health
  ```

### Option 3: Python Script Integration

```python
from chroma_vector_store import query_with_context

question = "What are the safety requirements?"
answer, latency = query_with_context(question)

print(f"Answer: {answer}")
print(f"Response time: {latency:.2f}s")
```

## Configuration

Edit these constants in the respective files:

**Unstructured_data_pipeline.py:**
```python
CHUNK_SIZE = 1200          # Characters per chunk
CHUNK_OVERLAP = 200        # Overlap between chunks
```

**chroma_vector_store.py:**
```python
EMBEDDING_MODEL = "text-embedding-3-large"  # OpenAI embedding model
TOP_K = 5                                   # Number of results to retrieve
```

## Troubleshooting

**"Collection not found" error:**
- Run `python Unstructured_data_pipeline.py` to create the vector store

**"No documents found" error:**
- Ensure documents are in the `docs/` folder
- Check that documents are in supported formats

**Slow processing:**
- Reduce `CHUNK_SIZE` to create fewer chunks
- Process documents in smaller batches

**API key issues:**
- Verify `.env` file exists with `OPENAI_API_KEY=your_key`
- Check that the key is valid at https://platform.openai.com/api-keys

## Security Notes

- **Never commit `.env` file** - contains your API key
- **Never commit `docs/` folder** - may contain proprietary documents
- Use `.gitignore` to exclude sensitive files
- API keys and documents should remain offline

## File Overview

- `Unstructured_data_pipeline.py` - Document processing pipeline
- `chroma_vector_store.py` - Vector store operations and queries
- `api_server.py` - Flask REST API server
- `rag_eval.py` - RAG evaluation metrics (optional)
