import os
import sys
import json
from rich.console import Console

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from guidelines_agent.core.extract import extract_guidelines_from_pdf

def main():
    """
    A simple script to test the PDF extraction function directly.
    """
    console = Console()
    console.print("[bold yellow]Testing PDF Extraction...[/bold yellow]")

    # Ensure the API key is set
    if not os.getenv("GEMINI_API_KEY"):
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY environment variable not set.")
        return

    # Path to the sample document
    file_path = "sample_docs/PRIM-Investment-Policy-Statement-02152024.pdf"
    console.print(f"Using sample file: [cyan]{file_path}[/cyan]")

    if not os.path.exists(file_path):
        console.print(f"[bold red]Error:[/bold red] Sample file not found at '{file_path}'.")
        return

    try:
        # Call the extraction function directly
        result = extract_guidelines_from_pdf(file_path)
        
        console.print("\n[bold green]Extraction Complete. Result:[/bold green]")
        console.print(json.dumps(result, indent=2))

        # Basic validation of the output
        if result.get("is_valid_document"):
            console.print("\n[bold green]Validation Status: Document is VALID.[/bold green]")
        else:
            console.print("\n[bold red]Validation Status: Document is INVALID.[/bold red]")
            console.print(f"Reason: {result.get('validation_summary')}")

    except Exception as e:
        console.print(f"\n[bold red]An error occurred during extraction:[/bold red]")
        console.print_exception()

if __name__ == "__main__":
    main()
