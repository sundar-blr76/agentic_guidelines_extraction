import os
import json
import sys
from typing import Dict, Any
from guidelines_agent.core.llm_providers import llm_manager, LLMProvider
from guidelines_agent.core.config import Config

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
PLANNER_MODEL = Config.GENERATIVE_MODEL

# ==============================================================================
# --- PLANNER PROMPT ---
# ==============================================================================
PLANNER_PROMPT = """
You are an intelligent assistant that deconstructs a user's request into a structured plan for a retrieval and summarization system.
Your task is to analyze the user's query and extract three key pieces of information.

**CONTEXT AWARENESS:** 
- If the user refers to "this fund", "the fund", "same portfolio", or similar contextual references, the query is likely a follow-up to previous conversation
- For contextual queries, expand the search to include broader terms while maintaining the specific intent
- Consider conversation flow - follow-up questions often seek different aspects of the same entity

Your output MUST be a single, valid JSON object with the following keys:
1.  `search_query`: A concise string optimized for semantic vector search. For contextual queries like "ESG guidelines of this fund", use specific terms like "ESG guidelines" that will match regardless of which fund is discussed.
2.  `summary_instruction`: A clear, natural language question or command that will be given to a summarization model. This should preserve the user's original intent and context.
3.  `top_k`: The number of documents to retrieve. If the user specifies a number (e.g., "top 5", "give me 10"), use that number. For follow-up contextual questions, default to 100. For broad initial questions, default to 25.

Here are some examples:

---
**Initial Query:**
User Query: "what are the rules for emerging markets? give me the top 5"
{{
  "search_query": "emerging market investment rules and restrictions",
  "summary_instruction": "What are the rules for emerging markets?",
  "top_k": 5
}}

---
**Follow-up Contextual Query:**
User Query: "Get me ESG guidelines of this fund" (following previous discussion about UN Pension Fund)
{{
  "search_query": "ESG guidelines",
  "summary_instruction": "Get me ESG guidelines of this fund.",
  "top_k": 7
}}

---
**General Query:**
User Query: "summarize the guidelines on private equity"
{{
  "search_query": "private equity guidelines",
  "summary_instruction": "Summarize the guidelines on private equity.",
  "top_k": 7
}}

---
**Specific Query:**
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


def generate_query_plan(user_query: str, 
                       provider: LLMProvider = None,
                       model: str = None) -> dict:
    """
    Uses a generative model to create a structured plan from a user query.
    Designed to be called from an API.
    """
    prompt = PLANNER_PROMPT.format(query=user_query)
    
    try:
        # Use the new LLM manager instead of direct genai calls
        response = llm_manager.generate_response(
            prompt=prompt,
            provider=provider or LLMProvider.GEMINI,
            model=model or PLANNER_MODEL,
            temperature=0.1
        )
        
        if not response.success:
            return {"error": f"LLM API call failed: {response.error}"}
        
        # Clean the response to ensure it's valid JSON
        json_text = response.content.strip().replace("```json", "").replace("```", "")
        plan = json.loads(json_text)
        return plan
        
    except Exception as e:
        return {
            "error": f"Error creating plan: {e}",
            "llm_response": getattr(response, 'content', '') if 'response' in locals() else ""
        }


def query_planner_cli(user_query: str):
    """
    CLI wrapper for the planning tool.
    """
    plan = generate_query_plan(user_query)
    if "error" in plan:
        print(f"Error: {plan['error']}", file=sys.stderr)
        if "llm_response" in plan:
            print(f"LLM Response was: {plan['llm_response']}", file=sys.stderr)
    else:
        print(json.dumps(plan, indent=2))

# For backward compatibility
create_plan = generate_query_plan
