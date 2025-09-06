import os
import json
import sys
import google.generativeai as genai

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PLANNER_MODEL = "models/gemini-1.5-pro-latest"

# ==============================================================================
# --- PLANNER PROMPT ---
# This prompt instructs the LLM to deconstruct a user's query.
# ==============================================================================
PLANNER_PROMPT = """
You are an intelligent assistant that deconstructs a user's request into a structured plan for a retrieval and summarization system.
Your task is to analyze the user's query and extract three key pieces of information.

Your output MUST be a single, valid JSON object with the following keys:
1.  `search_query`: A concise string optimized for semantic vector search. This should be a "bag of keywords" or a simple noun phrase that captures the core topic of the request.
2.  `summary_instruction`: A clear, natural language question or command that will be given to a summarization model. This should be the user's complete, original question or a well-formed version of it.
3.  `top_k`: The number of documents to retrieve. If the user specifies a number (e.g., "top 5", "give me 10"), use that number. If not specified, you MUST default to 7.

Here are some examples:

---
User Query: "what are the rules for emerging markets? give me the top 5"
{{
  "search_query": "emerging market investment rules and restrictions",
  "summary_instruction": "What are the rules for emerging markets?",
  "top_k": 5
}}
---
User Query: "summarize the guidelines on private equity"
{{
  "search_query": "private equity guidelines",
  "summary_instruction": "Summarize the guidelines on private equity.",
  "top_k": 7
}}
---
User Query: "tell me about any restrictions on using derivatives, I need about 10 results"
{{
  "search_query": "restrictions on using derivatives",
  "summary_instruction": "Tell me about any restrictions on using derivatives.",
  "top_k": 10
}}
---

Now, analyze the following user query.

User Query: "{query}"
"""
# ==============================================================================


def create_plan(user_query: str):
    """
    Uses a generative model to create a structured plan from a user query.
    """
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        return None
    genai.configure(api_key=GEMINI_API_KEY)

    prompt = PLANNER_PROMPT.format(query=user_query)

    try:
        model = genai.GenerativeModel(PLANNER_MODEL)
        response = model.generate_content(prompt)

        # Clean the response to ensure it's valid JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        plan = json.loads(json_text)
        return plan
    except Exception as e:
        print(f"Error creating plan: {e}", file=sys.stderr)
        print(f"LLM Response was: {response.text}", file=sys.stderr)
        return None
