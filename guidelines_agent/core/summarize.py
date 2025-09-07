import os
import sys
import google.generativeai as genai

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GENERATIVE_MODEL = "models/gemini-1.5-flash"

# ==============================================================================
# --- PROMPT PLACEHOLDER ---
# ==============================================================================
import os
import sys
import google.generativeai as genai
from rich.console import Console

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GENERATIVE_MODEL = "models/gemini-1.5-flash"
console = Console()

# ==============================================================================
# --- PROMPT PLACEHOLDER ---
# ==============================================================================
SUMMARIZATION_PROMPT = """
You are a compliance assistant.
You will receive:
1. The user’s query
2. A block of retrieved context (investment guidelines)

====================================================
USER QUERY
{query}
====================================================

RETRIEVED CONTEXT
{context}
(each guideline includes: text and provenance, e.g., [Part V.C.3.a, page 8])

====================================================
TASK
- Analyze the context to create a direct, structured answer to the user's query.
- Use only the retrieved context. Do not add or invent external information.
- If ambiguities or conflicts exist, highlight them in the 'Notes' section.

====================================================
OUTPUT STRUCTURE

**Direct Answer:**
A concise, 1-2 sentence summary that directly answers the user's query.

**Key Points:**
- [Key finding 1]. (Provenance: [Source, Page X])
- [Key finding 2]. (Provenance: [Source, Page Y])
- [Key finding 3]. (Provenance: [Source, Page Z])

**Notes:**
(Optional) Highlight any gaps, conflicts, or ambiguity in the context.
====================================================
"""
# ==============================================================================


def generate_summary(query: str, context: str) -> str:
    """
    Core logic for generating a summary from a given context based on a query.
    Designed to be called from an API.
    """
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY environment variable not set."
    genai.configure(api_key=GEMINI_API_KEY)

    prompt = SUMMARIZATION_PROMPT.format(query=query, context=context)

    try:
        model = genai.GenerativeModel(GENERATIVE_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {e}"


def summarize_cli():
    """
    CLI wrapper for the summarization tool.
    Reads context from stdin and prints the summary.
    """
    if not sys.stdin.isatty():
        context = sys.stdin.read()
        # A bit of a hack for the CLI: the first line is the query.
        lines = context.strip().split('\n')
        if not lines:
            console.print("[bold red]Error:[/bold red] No input provided to summarize.")
            return
            
        query = lines[0]
        context_block = "\n".join(lines[1:])
        
        summary = generate_summary(query, context_block)
        if summary:
            console.print(summary)
    else:
        console.print(
            "[bold red]Error:[/bold red] The summarize command requires a context piped from standard input."
        )

# For backward compatibility with cli.py
summarize_context = generate_summary

# ==============================================================================


def summarize_context(query: str, context: str):
    """
    Generates a summary from a given context block based on a query.
    """
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        return None
    genai.configure(api_key=GEMINI_API_KEY)

    prompt = SUMMARIZATION_PROMPT.format(query=query, context=context)

    try:
        model = genai.GenerativeModel(GENERATIVE_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {e}"
