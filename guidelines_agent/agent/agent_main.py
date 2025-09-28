import os
import typer
import logging
from rich.console import Console
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
import json

from guidelines_agent.tools.guideline_tools import (
    query_planner,
    guideline_search,
    summarizer,
    extract_and_validate_document,
    persist_guidelines,
    stamp_embeddings,
    generate_upload_summary,
)
from guidelines_agent.core.custom_logging import CustomCallbackHandler
from guidelines_agent.core.session_store import session_store
from guidelines_agent.core.config import GENERATIVE_MODEL

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AGENT_MODEL = GENERATIVE_MODEL
console = Console()
app = typer.Typer()
logger = logging.getLogger(__name__)

# --- Agent Definitions ---

def create_query_agent():
    """Creates a LangChain agent executor for answering questions."""
    logger.info("Creating query agent...")
    tools = [query_planner, guideline_search, summarizer]
    logger.info(f"Tools loaded: {[tool.name for tool in tools]}")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an assistant that answers questions about investment guidelines. You must use the provided tools to first plan the query, then search for guidelines, and finally summarize the results to form an answer.

When conversation history is available, use it to:
1. Reference previous discussions and maintain context
2. Build upon earlier questions and answers
3. Avoid repeating information already established
4. Provide more personalized responses

Current conversation history:
{conversation_history}

Active session context:
{session_context}"""),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    logger.info("Prompt template created.")
    
    llm = ChatGoogleGenerativeAI(model=AGENT_MODEL, google_api_key=GEMINI_API_KEY)
    logger.info(f"LLM initialized with model: {AGENT_MODEL}")
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    logger.info("Tool calling agent created.")
    
    callback_handler = CustomCallbackHandler()
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        callbacks=[callback_handler]
    )
    logger.info("AgentExecutor created with custom callback handler. Query agent is ready.")
    
    return agent_executor

def create_stateful_query_agent(session_id: str = None):
    """Creates a query agent with session context and conversation history."""
    logger.info(f"Creating stateful query agent for session: {session_id}")
    
    # Get session info
    conversation_history = ""
    session_context = {}
    
    if session_id:
        conversation_history = session_store.get_conversation_history(session_id)
        session_context = session_store.get_context(session_id)
        logger.info(f"Loaded session context: {len(session_context)} items, history: {len(conversation_history)} chars")
    
    tools = [query_planner, guideline_search, summarizer]
    logger.info(f"Tools loaded: {[tool.name for tool in tools]}")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an assistant that answers questions about investment guidelines. You must use the provided tools to first plan the query, then search for guidelines, and finally summarize the results to form an answer.

When conversation history is available, use it to:
1. Reference previous discussions and maintain context
2. Build upon earlier questions and answers  
3. Avoid repeating information already established
4. Provide more personalized responses

Current conversation history:
{conversation_history}

Active session context:
{session_context}"""),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    llm = ChatGoogleGenerativeAI(model=AGENT_MODEL, google_api_key=GEMINI_API_KEY)
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    callback_handler = CustomCallbackHandler()
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        callbacks=[callback_handler]
    )
    
    # Store session context in agent for later access
    agent_executor._session_id = session_id
    agent_executor._conversation_history = conversation_history
    agent_executor._session_context = session_context
    
    logger.info("Stateful query agent created successfully.")
    return agent_executor

# --- LangGraph Ingestion Workflow ---

class IngestionState(TypedDict):
    """Defines the state for the ingestion graph."""
    file_path: str
    file_name: str
    extraction_result: dict
    persistence_result: dict
    final_summary: str

def extract_node(state: IngestionState) -> IngestionState:
    """Node to extract and validate the document."""
    logger.info(f"--- Starting Extraction for {state['file_path']} ---")
    file_path = state['file_path']
    result = extract_and_validate_document.invoke({"file_path": file_path})
    return {
        "file_name": os.path.basename(file_path),
        "extraction_result": result
    }

def persist_node(state: IngestionState) -> IngestionState:
    """Node to persist the extracted guidelines."""
    logger.info("--- Starting Persistence ---")
    extraction_data = state['extraction_result']
    result = persist_guidelines.invoke({
        "data": extraction_data,
        "human_readable_digest": extraction_data.get("human_readable_digest", "")
    })
    # After persisting, stamp the embeddings
    stamp_embeddings.invoke({})
    return {"persistence_result": result}

def summarize_node(state: IngestionState) -> IngestionState:
    """Node to generate a final summary of the ingestion process."""
    logger.info("--- Generating Summary ---")
    extraction_result = state['extraction_result']
    persistence_result = state.get('persistence_result', {})  # May not exist if validation failed

    is_valid = extraction_result.get('is_valid_document', False)
    persistence_status = persistence_result.get('status', 'skipped')

    summary = generate_upload_summary.invoke({
        "doc_name": extraction_result.get('doc_name', 'Unknown Document'),
        "portfolio_name": extraction_result.get('portfolio_name', 'Unknown Portfolio'),
        "is_valid_document": is_valid,
        "validation_summary": extraction_result.get('validation_summary', 'No validation summary available.'),
        "guideline_count": len(extraction_result.get('guidelines', []) or []),
        "persistence_status": persistence_status,
        "persistence_message": persistence_result.get('message', 'An unknown error occurred.')
    })
    return {"final_summary": summary}

def should_persist(state: IngestionState) -> str:
    """Conditional edge to decide whether to persist the data."""
    logger.info("--- Checking Document Validity ---")
    if state['extraction_result'].get('is_valid_document', False):
        logger.info("--- Document is valid. Proceeding to persistence. ---")
        return "persist"
    else:
        logger.info("--- Document is invalid. Skipping persistence. ---")
        return "summarize"

def create_ingestion_agent():
    """Creates a LangGraph agent for ingesting documents."""
    logger.info("Creating ingestion graph...")
    workflow = StateGraph(IngestionState)

    workflow.add_node("extract", extract_node)
    workflow.add_node("persist", persist_node)
    workflow.add_node("summarize", summarize_node)

    workflow.set_entry_point("extract")
    workflow.add_conditional_edges(
        "extract",
        should_persist,
        {
            "persist": "persist",
            "summarize": "summarize",
        }
    )
    workflow.add_edge("persist", "summarize")
    workflow.add_edge("summarize", END)

    graph = workflow.compile()
    logger.info("Ingestion graph compiled successfully.")
    return graph

# --- CLI Commands ---

@app.command("query")
def run_query_agent(user_goal: str):
    """Answers a question using the query agent."""
    if not GEMINI_API_KEY:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY environment variable not set.")
        return
    
    console.print(f"[bold cyan]Goal:[/bold cyan] {user_goal}")
    agent_executor = create_query_agent()
    console.print("\n[yellow]Invoking Query Agent...[/yellow]\n")
    response = agent_executor.invoke({"input": user_goal})
    console.print("\n[bold green]Final Answer:[/bold green]")
    console.print(response["output"])

@app.command("ingest")
def run_ingestion_agent(file_path: str):
    """Ingests a document using the ingestion agent."""
    if not GEMINI_API_KEY:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY environment variable not set.")
        return
        
    console.print(f"[bold cyan]Goal:[/bold cyan] Ingest document at {file_path}")
    agent_executor = create_ingestion_agent()
    console.print("\n[yellow]Invoking Ingestion Agent...[/yellow]\n")
    response = agent_executor.invoke({"file_path": file_path})
    console.print("\n[bold green]Final Status:[/bold green]")
    console.print(response.get("final_summary", "No summary generated."))

if __name__ == "__main__":
    app()