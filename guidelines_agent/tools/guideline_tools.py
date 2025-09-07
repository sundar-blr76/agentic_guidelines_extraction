import json
import os
import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# --- Configuration ---
MCP_SERVER_URL = "http://localhost:8000"

# --- Pydantic Models for Tool Inputs ---

class PlanQueryInput(BaseModel):
    user_query: str = Field(..., description="The user's complete, natural language query.")

class GuidelineQueryInput(BaseModel):
    search_query: str = Field(..., description="A concise, keyword-focused query for semantic search.")
    top_k: int = Field(..., description="The number of top results to retrieve.")

class SearchResultItem(BaseModel):
    rank: int
    similarity: float
    portfolio_name: str
    guideline: str
    provenance: str

class SummarizeInput(BaseModel):
    summary_instruction: str = Field(..., description="The original user query for the summarizer.")
    search_results: List[SearchResultItem] = Field(..., description="The list of guidelines from the search.")

class ExtractAndValidateInput(BaseModel):
    file_path: str = Field(..., description="The local path to the PDF file to be processed.")

class PersistInput(BaseModel):
    data: str = Field(..., description="The JSON data containing portfolio and guideline information.")
    human_readable_digest: str = Field(..., description="The human-readable text digest of the guidelines.")

class UploadSummaryInput(BaseModel):
    file_name: str
    extraction_status: str
    guideline_count: int
    persistence_status: str
    was_reingested: bool
    validation_summary: str

# --- LangChain Tools ---

@tool("query_planner", args_schema=PlanQueryInput)
def query_planner(user_query: str) -> dict:
    """Plans a query by breaking it down into a search query and summary instruction."""
    response = requests.post(f"{MCP_SERVER_URL}/mcp/plan_query", json={"user_query": user_query})
    response.raise_for_status()
    return response.json()

@tool("guideline_search", args_schema=GuidelineQueryInput)
def guideline_search(search_query: str, top_k: int) -> list:
    """Searches the guidelines database."""
    response = requests.post(f"{MCP_SERVER_URL}/mcp/query_guidelines", json={"query_text": search_query, "top_k": top_k})
    response.raise_for_status()
    return response.json()

@tool("summarizer", args_schema=SummarizeInput)
def summarizer(summary_instruction: str, search_results: list) -> str:
    """Summarizes search results to answer the user's query."""
    sources = [f"Guideline: {res.guideline} (Provenance: {res.provenance})" for res in search_results]
    response = requests.post(f"{MCP_SERVER_URL}/mcp/summarize", json={"question": summary_instruction, "sources": sources})
    response.raise_for_status()
    return response.json()["summary"]

@tool("extract_and_validate_document", args_schema=ExtractAndValidateInput)
def extract_and_validate_document(file_path: str) -> dict:
    """Extracts, validates, and digests a PDF document."""
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/pdf")}
            response = requests.post(f"{MCP_SERVER_URL}/mcp/extract_guidelines", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": e.response.json()["detail"]}

@tool("persist_guidelines", args_schema=PersistInput)
def persist_guidelines(data: str, human_readable_digest: str) -> dict:
    """Persists the extracted guidelines to the database."""
    data = json.loads(data)
    payload = {"data": data, "human_readable_digest": human_readable_digest}
    response = requests.post(f"{MCP_SERVER_URL}/mcp/persist_guidelines", json=payload)
    response.raise_for_status()
    return response.json()

@tool("stamp_embeddings")
def stamp_embeddings() -> dict:
    """Generates and stores embeddings for any new guidelines."""
    response = requests.post(f"{MCP_SERVER_URL}/mcp/stamp_embedding")
    response.raise_for_status()
    return response.json()

@tool("generate_upload_summary", args_schema=UploadSummaryInput)
def generate_upload_summary(file_name: str, validation_summary: str, guideline_count: int, persistence_status: str) -> str:
    """Generates a coherent, human-readable summary of the upload status."""
    # This tool can be implemented with a direct LLM call or a simple f-string
    # for now, a simple formatted string is efficient.
    if persistence_status == "success":
        return f"Successfully ingested '{file_name}'. {validation_summary} Found and saved {guideline_count} guidelines."
    else:
        return f"Failed to ingest '{file_name}'. Reason: {validation_summary}"