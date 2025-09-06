import typer
import sys
import json
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table

# Import the refactored functions from other modules
from ingest import ingest_file
from persistence import persist_embeddings
from query import query_guidelines
from summarize import summarize_context
from plan import create_plan

# Initialize Typer app and Rich console
app = typer.Typer(
    name="guideline-tool",
    help="A CLI for ingesting, embedding, and querying investment guidelines.",
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def ingest(
    json_path: Annotated[
        str, typer.Argument(help="The path to the JSON file to ingest.")
    ],
):
    """Ingest a guideline document from a JSON file into the database."""
    ingest_file(json_path)


@app.command()
def persist():
    """
    Generate and store embeddings for all guidelines missing them.
    """
    persist_embeddings()


@app.command()
def query(
    query_text: Annotated[
        str, typer.Argument(help="The natural language query to search for.")
    ],
    portfolio_id: Annotated[
        str, typer.Option(help="Optional: The portfolio_id to filter by.")
    ] = None,
    top_k: Annotated[
        int, typer.Option(help="The number of top results to return.")
    ] = 5,
    formatted: Annotated[
        bool, typer.Option(help="Output a formatted table instead of raw text.")
    ] = False,
):
    """Query investment guidelines. Default output is JSON for piping."""
    results = query_guidelines(
        query_text, portfolio_id, top_k, raw_output=not formatted
    )

    if not results:
        if formatted:
            console.print("No matching guidelines found.")
        return

    if formatted:
        table = Table(
            title="--- Top Search Results ---",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Rank", style="dim", width=4)
        table.add_column("Similarity", style="cyan")
        table.add_column("Portfolio")
        table.add_column("Guideline")
        table.add_column("Provenance")

        for i, row in enumerate(results):
            text, provenance, page, portfolio_name, similarity = row
            table.add_row(
                str(i + 1),
                f"{similarity:.4f}",
                portfolio_name,
                text,
                f"{provenance} (Page: {page})",
            )

        console.print(table)
    else:
        print(results)


@app.command()
def summarize(
    question: Annotated[
        str,
        typer.Argument(help="The specific question to ask about the provided context."),
    ],
):
    """Summarize a context provided via standard input."""
    if not sys.stdin.isatty():
        context = sys.stdin.read()
        summary = summarize_context(question, context)
        if summary:
            console.print(summary)
    else:
        console.print(
            "[bold red]Error:[/bold red] The summarize command requires a context piped from standard input."
        )


@app.command()
def plan(
    user_query: Annotated[
        str,
        typer.Argument(
            help="Your full question, including summarization instructions."
        ),
    ],
):
    """
    Create a structured JSON plan from a complex user query.
    """
    plan_obj = create_plan(user_query)
    if plan_obj:
        print(json.dumps(plan_obj, indent=2))


if __name__ == "__main__":
    app()
