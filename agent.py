import requests
import json
import typer
from rich.console import Console

# --- Configuration ---
MCP_SERVER_URL = "http://0.0.0.0:8000"
console = Console()

def execute_agent_workflow(user_goal: str):
    """
    Orchestrates a workflow to answer a user's goal by calling the MCP server.
    """
    console.print(f"[bold cyan]Goal:[/bold cyan] {user_goal}")

    # 1. Plan the query
    console.print("\n[yellow]Step 1: Planning the query...[/yellow]")
    try:
        plan_response = requests.post(
            f"{MCP_SERVER_URL}/mcp/plan_query",
            json={"user_query": user_goal}
        )
        plan_response.raise_for_status()
        plan = plan_response.json()
        console.print(f"  - [green]Success:[/green] Plan created.")
        console.print(f"    - Search Query: '{plan['search_query']}'")
        console.print(f"    - Top K: {plan['top_k']}")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] Could not create a plan. {e}")
        return

    # 2. Execute the search query
    console.print("\n[yellow]Step 2: Executing the search...[/yellow]")
    try:
        query_response = requests.post(
            f"{MCP_SERVER_URL}/mcp/query_guidelines",
            json={"query_text": plan["search_query"], "top_k": plan["top_k"]}
        )
        query_response.raise_for_status()
        search_results = query_response.json()
        console.print(f"  - [green]Success:[/green] Found {len(search_results)} relevant guidelines.")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] Could not execute the query. {e}")
        return

    if not search_results:
        console.print("\n[bold yellow]Result:[/bold yellow] No relevant guidelines found to answer the question.")
        return

    # 3. Summarize the results
    console.print("\n[yellow]Step 3: Summarizing the findings...[/yellow]")
    try:
        sources_for_summary = [
            f"Guideline: {result['guideline']} (Provenance: {result['provenance']})"
            for result in search_results
        ]
        
        summarize_response = requests.post(
            f"{MCP_SERVER_URL}/mcp/summarize",
            json={
                "question": plan["summary_instruction"],
                "sources": sources_for_summary
            }
        )
        summarize_response.raise_for_status()
        summary = summarize_response.json()
        console.print(f"  - [green]Success:[/green] Summary generated.")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] Could not generate a summary. {e}")
        return

    # 4. Present the final answer
    console.print("\n[bold green]Final Answer:[/bold green]")
    console.print(summary["summary"])


if __name__ == "__main__":
    typer.run(execute_agent_workflow)
