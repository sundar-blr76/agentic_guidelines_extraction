import json
import os
import logging
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List

# --- Direct Core Imports ---
from guidelines_agent.core.query_planner import generate_query_plan
from guidelines_agent.core.query import query_guidelines_api
from guidelines_agent.core.summarize import generate_summary
from guidelines_agent.core.extract import extract_guidelines_from_pdf
from guidelines_agent.core.persist_guidelines import persist_guidelines_from_data
from guidelines_agent.core.persistence import stamp_missing_embeddings


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
    data: dict = Field(..., description="The JSON data containing portfolio and guideline information.")
    human_readable_digest: str = Field(..., description="The human-readable text digest of the guidelines.")

class UploadSummaryInput(BaseModel):
    file_name: str
    guideline_count: int
    persistence_status: str
    validation_summary: str

# --- LangChain Tools ---

@tool("query_planner", args_schema=PlanQueryInput)
def query_planner(user_query: str) -> dict:
    """Plans a query by breaking it down into a search query and summary instruction."""
    return generate_query_plan(user_query)

@tool("guideline_search", args_schema=GuidelineQueryInput)
def guideline_search(search_query: str, top_k: int) -> list:
    """Searches the guidelines database."""
    return query_guidelines_api(query=search_query, top_k=top_k)

@tool("summarizer", args_schema=SummarizeInput)
def summarizer(summary_instruction: str, search_results: list) -> str:
    """Summarizes search results to answer the user's query."""
    sources = [f"Guideline: {res.guideline} (Provenance: {res.provenance})" for res in search_results]
    context_block = "\n---\n".join(sources)
    return generate_summary(summary_instruction, context_block)

@tool("extract_and_validate_document", args_schema=ExtractAndValidateInput)
def extract_and_validate_document(file_path: str) -> dict:
    """Extracts, validates, and digests a PDF document."""
    logger = logging.getLogger(__name__)
    logger.info(f"Extracting and validating document at path: {file_path}")
    result = extract_guidelines_from_pdf(file_path)
    logger.info(f"Extraction result: {result}")
    return result

@tool("persist_guidelines", args_schema=PersistInput)
def persist_guidelines(data: dict, human_readable_digest: str) -> dict:
    """Persists the extracted guidelines to the database."""
    return persist_guidelines_from_data(data, human_readable_digest)

@tool("stamp_embeddings")
def stamp_embeddings() -> dict:
    """Generates and stores embeddings for any new guidelines."""
    return stamp_missing_embeddings()

@tool("generate_upload_summary", args_schema=UploadSummaryInput)
def generate_upload_summary(file_name: str, validation_summary: str, guideline_count: int, persistence_status: str) -> str:
    """Generates a coherent, human-readable summary of the upload status."""
    # This tool can be implemented with a direct LLM call or a simple f-string
    # for now, a simple formatted string is efficient.
    if persistence_status == "success":
        return f"Successfully ingested '{file_name}'. {validation_summary} Found and saved {guideline_count} guidelines."
    else:
        return f"Failed to ingest '{file_name}'. Reason: {validation_summary}"
