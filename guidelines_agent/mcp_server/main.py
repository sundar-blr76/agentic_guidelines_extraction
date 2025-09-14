import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os
import sys

# --- Add project root to Python path ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- Local Imports ---
from guidelines_agent.core.query_planner import generate_query_plan
from guidelines_agent.core.query import query_guidelines_api
from guidelines_agent.core.persist_guidelines import persist_guidelines_from_data
from guidelines_agent.core.summarize import generate_summary
from guidelines_agent.core.extract import extract_guidelines_from_pdf
from guidelines_agent.core.persistence import stamp_missing_embeddings
from guidelines_agent.agent.agent_main import create_query_agent, create_ingestion_agent
from guidelines_agent.core.custom_logging import ISTFormatter

logger = logging.getLogger(__name__)


# --- Pydantic Models ---
class PlanQueryInput(BaseModel):
    user_query: str = Field(..., description="The natural language user query.")

class PlanQueryOutput(BaseModel):
    search_query: str
    summary_instruction: str
    top_k: int

class QueryInput(BaseModel):
    query_text: str
    portfolio_id: Optional[str] = None
    top_k: int = 5

class QueryOutput(BaseModel):
    rank: int
    similarity: Optional[float] = None
    portfolio_name: str
    guideline: str
    provenance: str

class SummarizeInput(BaseModel):
    question: str
    sources: List[str]

class SummarizeOutput(BaseModel):
    summary: str

class PersistGuidelinesInput(BaseModel):
    data: Dict[str, Any]
    human_readable_digest: str = ""

class PersistGuidelinesOutput(BaseModel):
    status: str
    portfolio_id: str
    doc_id: str
    ingested_guidelines: int
    was_reingested: bool

class ExtractGuidelinesOutput(BaseModel):
    is_valid_document: bool
    validation_summary: str
    guidelines: Optional[List[Dict[str, Any]]] = None
    human_readable_digest: Optional[str] = None

class StampEmbeddingOutput(BaseModel):
    status: str
    message: str
    updated_rows: int

class AgentInvokeInput(BaseModel):
    input: str

# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server startup: Initializing AI agents...")
    try:
        app.state.query_agent = create_query_agent()
        app.state.ingestion_agent = create_ingestion_agent()
        logger.info("Server startup: AI agents initialized successfully.")
    except Exception:
        logger.error("Server startup: Failed to initialize AI agents.", exc_info=True)
        raise
    yield
    logger.info("Server shutdown: Cleaning up.")

# --- FastAPI App ---
app = FastAPI(
    title="Agentic Guideline Extraction MCP Server",
    description="Exposes guideline extraction and analysis tools via MCP.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.concurrency import run_in_threadpool

# ... (existing code)

# --- API Endpoints ---
@app.post("/agent/query", tags=["Agent"])
async def agent_query(request: Request, input: AgentInvokeInput):
    logger.info(f"Received query: {input.input}")
    try:
        # Run the synchronous, blocking agent code in a separate thread
        response = await run_in_threadpool(request.app.state.query_agent.invoke, {"input": input.input})
        logger.info(f"Agent response: {response.get('output')}")
        return {"output": response.get("output")}
    except Exception as e:
        logger.error(f"Error during query for input '{input.input}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/ingest", tags=["Agent"])
async def agent_ingest(request: Request, file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}, content type: {file.content_type}")
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            logger.info(f"Saved file to {temp_file_path}, size: {len(content)} bytes")
        
        # Run the synchronous, blocking agent code in a separate thread
        response = await run_in_threadpool(request.app.state.ingestion_agent.invoke, {"file_path": temp_file_path})
        
        logger.info(f"Agent response: {response}")
        # LangGraph returns the final state. Extract the summary.
        final_summary = response.get("final_summary", "Ingestion process completed, but no summary was generated.")
        return {"output": final_summary}
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Removed temporary file: {temp_file_path}")

if __name__ == "__main__":
    import uvicorn
    # Note: This block is for direct execution, not for production.
    # Uvicorn should be run from the command line as specified in the RUNBOOK.md.
    uvicorn.run(app, host="0.0.0.0", port=8000)