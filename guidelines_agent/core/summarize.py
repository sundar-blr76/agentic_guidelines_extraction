import os
import sys
from rich.console import Console
from guidelines_agent.core.llm_providers import llm_manager, LLMProvider
from guidelines_agent.core.config import Config

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GENERATIVE_MODEL = Config.GENERATIVE_MODEL
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


def generate_summary(query: str, context: str,
                    provider: LLMProvider = None,
                    model: str = None) -> str:
    """
    Core logic for generating a summary from a given context based on a query.
    Designed to be called from an API with multiple LLM provider support.
    
    Args:
        query: User's question
        context: Retrieved context to summarize  
        provider: LLM provider to use (defaults to configured default)
        model: Model name to use (defaults to provider default)
        
    Returns:
        Generated summary text
    """
    # Use configured defaults if not specified
    if provider is None:
        provider = Config.get_default_provider()
    if model is None:
        config = Config.get_llm_config(provider)
        model = config.model if config else GENERATIVE_MODEL
    
    if not GEMINI_API_KEY and provider == LLMProvider.GEMINI:
        return "Error: GEMINI_API_KEY environment variable not set."

    prompt = SUMMARIZATION_PROMPT.format(query=query, context=context)

    try:
        # Create metadata for debugging
        metadata = {
            "operation": "text_summarization",
            "query": query,
            "context_length": len(context),
        }
        
        # Use the new LLM manager with debug logging
        response = llm_manager.generate_response(
            prompt=prompt,
            model=model,
            provider=provider,
            temperature=0.1,
            metadata=metadata
        )
        
        if not response.success:
            return f"Error generating summary: {response.error}"
            
        return response.content
        
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

