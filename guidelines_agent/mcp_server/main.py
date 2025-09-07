from fastapi import FastAPI, Body, UploadFile, File, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guidelines_agent.core.query_planner import generate_query_plan
from guidelines_agent.core.query import query_guidelines_api
from guidelines_agent.core.persist_guidelines import persist_guidelines_from_data
from guidelines_agent.core.summarize import generate_summary
from guidelines_agent.core.extract import extract_guidelines_from_pdf
from guidelines_agent.core.persistence import stamp_missing_embeddings
from guidelines_agent.agent.main import create_query_agent, create_ingestion_agent

# --- Pydantic Models for MCP ---

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

# --- FastAPI App ---

app = FastAPI(
    title="Agentic Guideline Extraction MCP Server",
    description="Exposes guideline extraction and analysis tools via MCP.",
    version="1.0.0",
)

# --- MCP Discovery Endpoint ---

@app.get("/mcp/", tags=["MCP Discovery"])
def discover_tools(request: Request):
    """
    MCP discovery endpoint that returns a manifest of available tools.
    """
    tool_manifest = {
        "name": "guideline_extraction_tools",
        "description": "A collection of tools for extracting, persisting, and querying investment guidelines.",
        "tools": []
    }
    
    # This is a simplified way to generate the manifest.
    # A more robust implementation might inspect the routes programmatically.
    base_url = str(request.base_url)
    
    tool_manifest["tools"].append({
        "name": "plan_query",
        "description": "Takes a user query and returns a structured query plan.",
        "endpoint": f"{base_url}mcp/plan_query",
        "method": "POST",
        "input_schema": PlanQueryInput.schema(),
        "output_schema": PlanQueryOutput.schema()
    })
    
    tool_manifest["tools"].append({
        "name": "query_guidelines",
        "description": "Executes a search query against the guidelines database.",
        "endpoint": f"{base_url}mcp/query_guidelines",
        "method": "POST",
        "input_schema": QueryInput.schema(),
        "output_schema": {"type": "array", "items": QueryOutput.schema()}
    })
    
    tool_manifest["tools"].append({
        "name": "summarize",
        "description": "Summarizes a list of text sources based on a question.",
        "endpoint": f"{base_url}mcp/summarize",
        "method": "POST",
        "input_schema": SummarizeInput.schema(),
        "output_schema": SummarizeOutput.schema()
    })
    
    tool_manifest["tools"].append({
        "name": "persist_guidelines",
        "description": "Persists a new set of guidelines from a JSON payload.",
        "endpoint": f"{base_url}mcp/persist_guidelines",
        "method": "POST",
        "input_schema": PersistGuidelinesInput.schema(),
        "output_schema": PersistGuidelinesOutput.schema()
    })
    
    tool_manifest["tools"].append({
        "name": "extract_guidelines",
        "description": "Extracts guidelines from an uploaded PDF file.",
        "endpoint": f"{base_url}mcp/extract_guidelines",
        "method": "POST",
        "input_schema": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}},
        "output_schema": ExtractGuidelinesOutput.schema()
    })
    
    tool_manifest["tools"].append({
        "name": "stamp_embedding",
        "description": "Generate and store embeddings for all guidelines missing them.",
        "endpoint": f"{base_url}mcp/stamp_embedding",
        "method": "POST",
        "input_schema": {},
        "output_schema": StampEmbeddingOutput.schema()
    })
    
    return tool_manifest

# --- MCP Tool Endpoints ---

@app.post("/mcp/plan_query", tags=["MCP Tools"])
def plan_query_mcp(input: PlanQueryInput = Body(...)) -> PlanQueryOutput:
    """MCP endpoint for the Query Planner tool."""
    result = generate_query_plan(input.user_query)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return PlanQueryOutput(**result)

@app.post("/mcp/query_guidelines", tags=["MCP Tools"])
def query_guidelines_mcp(input: QueryInput = Body(...)) -> List[QueryOutput]:
    """MCP endpoint for the Guideline Query tool."""
    results = query_guidelines_api(
        input.query_text, input.portfolio_id, input.top_k
    )
    formatted_results = [
        QueryOutput(
            rank=i + 1,
            similarity=result['similarity'],
            portfolio_name=result['portfolio_name'],
            guideline=result['guideline_text'],
            provenance=f"{result['provenance']} (Page: {result['page']})",
        )
        for i, result in enumerate(results)
    ]
    return formatted_results

@app.post("/mcp/summarize", tags=["MCP Tools"])
def summarize_mcp(input: SummarizeInput = Body(...)) -> SummarizeOutput:
    """MCP endpoint for the Summarization tool."""
    context_block = "\n---\n".join(input.sources)
    summary = generate_summary(input.question, context_block)
    return SummarizeOutput(summary=summary)

@app.post("/mcp/persist_guidelines", tags=["MCP Tools"])
def persist_guidelines_mcp(input: PersistGuidelinesInput = Body(...)) -> PersistGuidelinesOutput:
    """MCP endpoint for the Guideline Persistence tool."""
    result = persist_guidelines_from_data(input.data, input.human_readable_digest)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return PersistGuidelinesOutput(**result)

@app.post("/mcp/extract_guidelines", tags=["MCP Tools"])
async def extract_guidelines_mcp(file: UploadFile = File(...)) -> ExtractGuidelinesOutput:
    """MCP endpoint for the Guideline Extraction and Validation tool."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    temp_pdf_path = f"temp_{file.filename}"
    try:
        with open(temp_pdf_path, "wb") as buffer:
            buffer.write(await file.read())

        # This single function call now performs both extraction and validation
        extraction_result = extract_guidelines_from_pdf(temp_pdf_path)

        return ExtractGuidelinesOutput(**extraction_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

@app.post("/mcp/stamp_embedding", tags=["MCP Tools"])
def stamp_embedding_mcp() -> StampEmbeddingOutput:
    """MCP endpoint for the Embedding Stamper tool."""
    try:
        result = stamp_missing_embeddings()
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return StampEmbeddingOutput(
            status=result["status"],
            message=result.get("message", f"Processed {result.get('processed_count', 0)} guidelines."),
            updated_rows=result.get("processed_count", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Agent Endpoints ---

class AgentInvokeInput(BaseModel):
    input: str

query_agent = create_query_agent()
ingestion_agent = create_ingestion_agent()

@app.post("/agent/invoke", tags=["Agent"])
async def agent_invoke(input: AgentInvokeInput):
    """Invokes the query agent."""
    try:
        response = query_agent.invoke({"input": input.input})
        return {"output": response.get("output")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/ingest", tags=["Agent"])
async def agent_ingest(file: UploadFile = File(...)):
    """Invokes the ingestion agent."""
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        response = ingestion_agent.invoke({"file_path": temp_file_path})
        return {"output": response.get("output")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)