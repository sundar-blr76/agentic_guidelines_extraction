import os
import sys
import google.generativeai as genai

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GENERATIVE_MODEL = "models/gemini-1.5-flash"

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
