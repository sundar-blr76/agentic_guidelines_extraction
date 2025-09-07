import typer
import sys
import json
import os
import re
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table
from datetime import datetime

# Import the refactored functions from other modules
from guidelines_agent.core.persist_guidelines import persist_guidelines_from_file
from guidelines_agent.core.persistence import persist_embeddings
from guidelines_agent.core.query import query_guidelines
from guidelines_agent.core.summarize import summarize_cli
from guidelines_agent.core.query_planner import query_planner_cli
from guidelines_agent.core.extract import extract_guidelines_from_pdf

# Initialize Typer app and Rich console
app = typer.Typer(
    name="guideline-tool",
    help="A CLI for ingesting, embedding, and querying investment guidelines.",
    rich_markup_mode="rich",
)
console = Console()


def generate_clean_id(text):
    """Generates a clean, lowercase ID from a string."""
    text = text.lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_]", "", text)
    return text


@app.command("extract-guidelines")
def extract_guidelines(
    pdf_path: Annotated[
        str, typer.Argument(help="The path to the PDF file to extract guidelines from.")
    ],
    output_dir: Annotated[
        str, typer.Option(help="The directory to save the output files.")
    ] = "results",
):
    """Extracts guidelines from a PDF and saves them as JSON and Markdown."""
    console.print(f"Extracting guidelines from: {pdf_path}")
    try:
        guidelines_list, guidelines_text = extract_guidelines_from_pdf(pdf_path)

        base_name = os.path.basename(pdf_path)
        file_name_without_ext = os.path.splitext(base_name)[0]

        portfolio_name = file_name_without_ext
        portfolio_id = generate_clean_id(portfolio_name)
        doc_name = base_name
        doc_id = portfolio_id
        doc_date = datetime.now().strftime("%Y-%m-%d")

        output_data = {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio_name,
            "doc_id": doc_id,
            "doc_name": doc_name,
            "doc_date": doc_date,
            "guidelines": guidelines_list,
        }

        os.makedirs(output_dir, exist_ok=True)
        json_filename = f"{file_name_without_ext}.json"
        md_filename = f"{file_name_without_ext}.md"
        json_filepath = os.path.join(output_dir, json_filename)
        md_filepath = os.path.join(output_dir, md_filename)

        with open(json_filepath, "w") as f:
            json.dump(output_data, f, indent=2)
        with open(md_filepath, "w") as f:
            f.write(guidelines_text)

        console.print(f"Successfully extracted {len(guidelines_list)} guidelines.")
        console.print(f"  - JSON saved to: {json_filepath}")
        console.print(f"  - Digest saved to: {md_filepath}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not process {pdf_path}. Details: {e}")


@app.command("persist-guidelines")
def persist_guidelines(
    json_path: Annotated[
        str, typer.Argument(help="The path to the JSON file to ingest.")
    ],
):
    """Persist a guideline document from a JSON file into the database."""
    persist_guidelines_from_file(json_path)


@app.command("stamp-embedding")
def stamp_embedding():
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
    console.print(f"Generating embedding for your query: '{query_text}'...")
    results = query_guidelines(
        query_text, portfolio_id, top_k
    )

    if not results:
        if formatted:
            console.print("No matching guidelines found.")
        return

    console.print("Search complete.")

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

        for i, result in enumerate(results):
            table.add_row(
                str(i + 1),
                f"{result['similarity']:.4f}",
                result['portfolio_name'],
                result['guideline_text'],
                f"{result['provenance']} (Page: {result['page']})",
            )

        console.print(table)
    else:
        print(json.dumps(results, indent=2))


@app.command()
def summarize():
    """
    Summarize a context provided via standard input.
    The first line of the input should be the question.
    """
    summarize_cli()


@app.command()
def plan_query(
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
    query_planner_cli(user_query)


if __name__ == "__main__":
    app()
