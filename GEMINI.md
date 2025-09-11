# Gemini Agent Context: Guideline Extraction and Querying Engine

This document provides a comprehensive overview of the project for the Gemini AI agent.

## Project Overview

This project is a sophisticated AI-powered application designed to extract, process, and query investment guidelines from PDF documents. It combines a powerful Python backend with a modern React-based frontend to provide a seamless user experience.

### Core Functionality

-   **Guideline Extraction:** Leverages AI to parse PDF documents and extract structured investment guidelines.
-   **Data Persistence:** Stores the extracted guidelines and their vector embeddings in a database for efficient retrieval.
-   **Natural Language Querying:** Allows users to ask questions in natural language to query the stored guidelines.
-   **AI Agentic Workflow:** Utilizes a multi-agent system (powered by LangChain and Google's Gemini models) to handle complex tasks like document ingestion and query planning.

### Architecture & Technologies

-   **Backend:**
    -   **Framework:** FastAPI (Python)
    -   **AI/ML:** `google-generativeai`, `langchain`, `langchain-google-genai`
    -   **Database:** PostgreSQL (inferred from `psycopg2-binary`)
    -   **CLI:** Typer
    -   **Linting:** Ruff
    -   **Testing:** Pytest
-   **Frontend:**
    -   **Framework:** React (Create React App)
    -   **Language:** TypeScript
    -   **UI Components:** Material-UI (`@mui/material`)
    -   **API Communication:** Axios

The backend exposes a REST API that the frontend consumes. It also hosts internal "tool" endpoints that the AI agents use to perform their tasks.

## Building and Running

### 1. Backend Server

The backend is a FastAPI application run with `uvicorn`. It's configured to log to `logs/api_server.log`.

# Gemini Agent Context: Guideline Extraction and Querying Engine

This document provides a comprehensive overview of the project for the Gemini AI agent.

## Project Overview

This project is a sophisticated AI-powered application designed to extract, process, and query investment guidelines from PDF documents. It combines a Python FastAPI backend with a React frontend to provide a seamless user experience.

### Core Functionality

- Guideline Extraction: AI parses PDF documents and extracts structured investment guidelines.
- Data Persistence: Stores extracted guidelines and vector embeddings in PostgreSQL for efficient retrieval.
- Natural Language Querying: Users can query stored guidelines in plain English.
- Agentic Workflow: LangChain + Google models orchestrate document ingestion and query planning.

### Architecture & Technologies

- Backend: FastAPI, google-genai (Gemini), LangChain, PostgreSQL
- CLI: Typer
- Frontend: React + TypeScript
- Dev & Test: ruff, pytest

## API Endpoints

This project exposes two logical groups of endpoints:

- Public agent endpoints (used by the UI and external callers): prefix `/agent`
- Internal machine tool endpoints (used by the agent to perform sub-tasks): prefix `/mcp`

### Agent endpoints (external)

- POST /agent/invoke
    - Purpose: High-level invocation that runs an agent workflow (query, ingest, or other user goals).
    - Example JSON body: {"action": "ingest", "pdf_path": "/tmp/doc.pdf", "portfolio_id": "fund-123"}

- POST /agent/query
    - Purpose: Submit a user natural-language query and get a composed answer.
    - Example JSON body: {"query": "What are the rebalancing rules for Fund X?", "portfolio_id": "fund-123"}

- POST /agent/ingest
    - Purpose: Ingest a document (PDF) and persist extracted guidelines + embeddings.
    - Example JSON body: {"pdf_path": "/path/to/OAS Retirement 2025.pdf", "portfolio_id": "fund-123", "doc_name": "OAS Retirement 2025"}

These endpoints are intended for the UI or trusted external callers. CORS is enabled for the frontend origin in development.

### MCP endpoints (internal tool endpoints)

The agent uses these internal endpoints to break down tasks and call fine-grained tools. They are mounted under `/mcp` and are primarily called from the backend agent code (server-to-itself requests).

- POST /mcp/plan_query
    - Purpose: Turn a complex user query into a step-by-step plan the agent can execute.
    - Example JSON body: {"query": "Compare rebalancing rules across funds A and B", "portfolio_ids": ["A","B"]}

- POST /mcp/extract_guidelines
    - Purpose: Extract structured guidelines from an uploaded PDF (calls `extract.py`).
    - Example JSON body: {"pdf_bytes_base64": "...", "doc_name": "OAS Retirement"}

- POST /mcp/query_guidelines
    - Purpose: Run a deterministic SQL or semantic retrieval against stored guidelines.
    - Example JSON body: {"query": "rebalancing", "portfolio_id": "fund-123"}

- POST /mcp/stamp_embedding
    - Purpose: Generate embeddings for guideline records that lack them (calls `embedding.py`).
    - Example JSON body: {"doc_id": "doc-123"}

Notes:

- MCP endpoints are designed for local server-to-server calls; treat them as internal and secure them accordingly in production (e.g., internal network, auth).
- Each MCP endpoint returns JSON with structured results and provenance to support audits.

## Building and Running (quick)

1. Create and activate a virtualenv, then install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Start the backend:

```bash
venv/bin/python -m uvicorn guidelines_agent.mcp_server.main:app --host 0.0.0.0 --port 8000 --log-config logging.yaml
```

3. Start the frontend (if working locally):

```bash
./start_frontend.sh
```

## CLI Usage (summary)

- `extract-guidelines <pdf_path>` — Extract guidelines and save JSON/MD.
- `persist-guidelines <json_path>` — Ingest JSON guidelines into the DB.
- `stamp-embedding` — Generate embeddings for guidelines missing vectors.
- `query <query_text>` — Natural language query against the system.

For full developer notes see `RUNBOOK.md` and `context.md`.
