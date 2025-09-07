import os
import typer
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

# --- Agent Definitions ---

def create_query_agent():
    """Creates an agent executor for answering questions."""
    tools = [query_planner, guideline_search, summarizer]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant that answers questions about investment guidelines. You must use the provided tools to first plan the query, then search for guidelines, and finally summarize the results to form an answer."),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    llm = ChatGoogleGenerativeAI(model=AGENT_MODEL, google_api_key=GEMINI_API_KEY)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def create_ingestion_agent():
    """Creates an agent executor for ingesting documents."""
    tools = [
        extract_and_validate_document,
        persist_guidelines,
        stamp_embeddings,
        generate_upload_summary,
    ]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant that ingests and validates investment guideline documents. Follow these steps:\n1. Extract and validate the document.\n2. If it is valid, persist the guidelines.\n3. After persisting, stamp the embeddings.\n4. Finally, generate a summary of the upload status."),
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
