# MultiDoc RAG Chat

MultiDoc RAG Chat is a FastAPI application that lets you upload documents, build a FAISS vector index, and ask questions over the uploaded content using a conversational RAG pipeline.

The app includes a small browser UI, JSON API endpoints, session-based chat history, LangChain LCEL chains, configurable LLM providers, and local FAISS persistence for each upload session.

## Features

- Upload multiple documents from the web UI or API.
- Index document chunks into a per-session FAISS vector store.
- Ask follow-up questions with chat history context.
- Use MMR retrieval to improve context diversity.
- Switch between configured LLM and embedding providers.
- Validate chat responses with Pydantic models.
- Run unit and integration tests with pytest.

## Tech Stack

- Python 3.12+
- FastAPI and Uvicorn
- LangChain
- FAISS
- Groq or Google Gemini for chat models
- Ollama or Google Gemini for embeddings
- Jinja2, HTML, CSS, and vanilla JavaScript for the UI

## Project Structure

```text
.
|-- main.py                         # FastAPI app, routes, and session handling
|-- multi_doc_chat/
|   |-- config/config.yml            # Provider and retriever configuration
|   |-- model/models.py              # Request/response schemas
|   |-- prompts/prompt_library.py    # RAG prompts
|   |-- src/document_ingestion/      # File loading, chunking, and FAISS indexing
|   |-- src/document_chat/           # Conversational RAG chain
|   `-- utils/                       # File, config, and model helpers
|-- templates/index.html             # Browser UI
|-- static/styles.css                # UI styles
|-- test/                            # Unit and integration tests
|-- pyproject.toml                   # Project metadata and dependencies
`-- uv.lock                          # Locked dependency versions for uv
```

## Supported Documents

The current document loading pipeline indexes:

- PDF files (`.pdf`)
- Word documents (`.docx`)
- Text files (`.txt`)

Uploaded files and generated FAISS indexes are runtime artifacts. They are written to `data/` and `faiss_index/`, and those folders are ignored by git.

## Setup

Clone the repository and install dependencies.

Using `uv`:

```bash
uv sync
```

Using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Environment Variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Fill in the required keys:

```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
LLM_PROVIDER=groq
EMBEDDING_PROVIDER=ollama
ENV=local
PORT=8000
```

The current startup code expects both `GROQ_API_KEY` and `GOOGLE_API_KEY` to be present. Provider selection is controlled with:

- `LLM_PROVIDER`: `groq` or `google`
- `EMBEDDING_PROVIDER`: `ollama` or `google`

When using the default Ollama embedding provider, install Ollama and pull the configured embedding model:

```bash
ollama pull nomic-embed-text
```

## Run the App

Using `uv`:

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Using an activated virtual environment:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

```text
http://localhost:8000
```

## API

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Upload Documents

```http
POST /upload
Content-Type: multipart/form-data
```

Form field:

- `files`: one or more files

Response:

```json
{
  "session_id": "20260530142305_36d8e85d",
  "indexed": true,
  "message": "Indexing Completed"
}
```

### Chat With Documents

```http
POST /chat
Content-Type: application/json
```

Request:

```json
{
  "session_id": "20260530142305_36d8e85d",
  "message": "Summarize the key points from the uploaded documents."
}
```

Response:

```json
{
  "answer": "..."
}
```

## Testing

Run the test suite:

```bash
uv run pytest
```

Or, with an activated virtual environment:

```bash
pytest
```

The tests use stubs for LLM and embedding dependencies, so they do not need real API calls.

## Runtime Files

The application creates local runtime files while you use it:

- `data/`: uploaded documents saved per session
- `faiss_index/`: generated FAISS indexes and metadata
- `logs/` and `multi_doc_chat/logs/`: local log output

These files are ignored by git because they are generated locally and may contain private document content.
