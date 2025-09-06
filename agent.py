import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from tools import query_planner, guideline_search, summarizer
import typer
from rich.console import Console

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AGENT_MODEL = "gemini-1.5-pro-latest"
console = Console()

# --- LangChain Agent Setup ---

def create_agent():
    """Creates and returns a LangChain agent executor."""
    
    # 1. Define the tools the agent can use
    tools = [query_planner, guideline_search, summarizer]
    
    # 2. Create the prompt template
    # This template instructs the agent on how to behave and use the tools.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that answers questions about investment guidelines."),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # 3. Initialize the LLM
    llm = ChatGoogleGenerativeAI(model=AGENT_MODEL, google_api_key=GEMINI_API_KEY)
    
    # 4. Create the agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 5. Create the agent executor
    # The executor is what actually runs the agent and executes the tools.
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor

def run_agent(user_goal: str):
    """
    Initializes and runs the LangChain agent with the user's goal.
    """
    if not GEMINI_API_KEY:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY environment variable not set.")
        return
        
    console.print(f"[bold cyan]Goal:[/bold cyan] {user_goal}")
    
    agent_executor = create_agent()
    
    console.print("\n[yellow]Invoking agent...[/yellow]\n")
    
    # The agent will automatically figure out which tools to call and in what order.
    response = agent_executor.invoke({"input": user_goal})
    
    console.print("\n[bold green]Final Answer:[/bold green]")
    console.print(response["output"])

if __name__ == "__main__":
    typer.run(run_agent)