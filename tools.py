import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List

# --- Configuration ---
MCP_SERVER_URL = "http://localhost:8000"

# --- Pydantic Models for Tool Inputs ---
# These models ensure that the inputs to our tools are validated.

class PlanQueryInput(BaseModel):
    user_query: str = Field(..., description="The user's complete, natural language query.")

class GuidelineQueryInput(BaseModel):
    search_query: str = Field(..., description="A concise, keyword-focused query for semantic search.")
    top_k: int = Field(..., description="The number of top results to retrieve.")

class SearchResultItem(BaseModel):
    """Defines the structure of a single item in the search results list."""
    rank: int
    similarity: float
    portfolio_name: str
    guideline: str
    provenance: str

class SummarizeInput(BaseModel):
    summary_instruction: str = Field(..., description="The original user query or a well-formed question for the summarizer.")
    search_results: List[SearchResultItem] = Field(..., description="The list of guidelines retrieved from the search.")

# --- LangChain Tools ---

@tool("query_planner", args_schema=PlanQueryInput)
def query_planner(user_query: str) -> dict:
    """
    Takes a user's natural language query and returns a structured plan for execution.
    """
    response = requests.post(
        f"{MCP_SERVER_URL}/mcp/plan_query",
        json={"user_query": user_query}
    )
    response.raise_for_status()
    return response.json()

@tool("guideline_search", args_schema=GuidelineQueryInput)
def guideline_search(search_query: str, top_k: int) -> list:
    """
    Searches the guidelines database with a keyword-focused query and returns the top_k results.
    """
    response = requests.post(
        f"{MCP_SERVER_URL}/mcp/query_guidelines",
        json={"query_text": search_query, "top_k": top_k}
    )
    response.raise_for_status()
    return response.json()

@tool("summarizer", args_schema=SummarizeInput)
def summarizer(summary_instruction: str, search_results: list) -> str:
    """
    Takes a summary instruction and a list of search results to generate a final answer.
    """
    sources_for_summary = [
        f"Guideline: {result.guideline} (Provenance: {result.provenance})"
        for result in search_results
    ]
    
    response = requests.post(
        f"{MCP_SERVER_URL}/mcp/summarize",
        json={
            "question": summary_instruction,
            "sources": sources_for_summary
        }
    )
    response.raise_for_status()
    return response.json()["summary"]
