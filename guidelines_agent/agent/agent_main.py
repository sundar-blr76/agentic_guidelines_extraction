import os
import typer
import logging
from rich.console import Console
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from guidelines_agent.tools.guideline_tools import (
    query_planner,
    guideline_search,
    summarizer,
    extract_and_validate_document,
    persist_guidelines,
    stamp_embeddings,
    generate_upload_summary,
)

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AGENT_MODEL = "gemini-1.5-pro-latest"
console = Console()
app = typer.Typer()

import logging

from guidelines_agent.core.custom_logging import CustomCallbackHandler

# --- Agent Definitions ---

def create_query_agent():
    """Creates an agent executor for answering questions."""
    logger = logging.getLogger(__name__)
    logger.info("Creating query agent...")
    
    tools = [query_planner, guideline_search, summarizer]
    logger.info(f"Tools loaded: {[tool.name for tool in tools]}")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant that answers questions about investment guidelines. You must use the provided tools to first plan the query, then search for guidelines, and finally summarize the results to form an answer."),
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

def create_ingestion_agent():
    """Creates an agent executor for ingesting documents."""
    tools = [
        extract_and_validate_document,
        persist_guidelines,
        stamp_embeddings,
        generate_upload_summary,
    ]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant that ingests and validates investment guideline documents. Your final output must be a human-readable summary. Follow these steps:\n1. Use the `extract_and_validate_document` tool on the file path.\n2. **Check the `is_valid_document` field in the output. If it is `False`, you must stop immediately and use the `validation_summary` as your final answer.**\n3. If the document is valid, take the entire JSON output from the extraction tool (which includes metadata and the guidelines list). Pass this complete JSON object as the `data` argument to the `persist_guidelines` tool. Also pass the `human_readable_digest` to the corresponding argument.\n4. After persisting, call the `stamp_embeddings` tool.\n5. Finally, use the outputs from the previous steps to call `generate_upload_summary` and use its output as your final answer."),
        ("user", "Please ingest this file: {file_path}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    llm = ChatGoogleGenerativeAI(model=AGENT_MODEL, google_api_key=GEMINI_API_KEY)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)



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
    console.print(response["output"])

if __name__ == "__main__":
    app()
