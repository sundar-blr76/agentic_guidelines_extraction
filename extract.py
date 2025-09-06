import logging
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types as genai_types
import json
import re


# --- Custom IST Logging Configuration ---
class ISTFormatter(logging.Formatter):
    """A custom logging formatter to display timestamps in IST."""

    def formatTime(self, record, datefmt=None):
        utc_dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        ist_dt = utc_dt.astimezone(ist_tz)
        if datefmt:
            return ist_dt.strftime(datefmt)
        return ist_dt.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]


# Get the root logger, clear existing handlers, and add our custom one
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()

handler = logging.StreamHandler()
handler.setFormatter(ISTFormatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
# --- End of Logging Configuration ---

client = genai.Client()


def extract_json_from_text(text):
    """More robustly extracts a JSON array from a string, handling markdown code blocks."""
    # Regex to find a JSON array, possibly wrapped in markdown
    match = re.search(r"```json\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    # Fallback for non-markdown JSON
    start_index = text.find("[")
    end_index = text.rfind("]")
    if start_index != -1 and end_index != -1:
        return text[start_index : end_index + 1]

    return None


def extract_guidelines_from_pdf(pdf_path: str):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    model_name = "gemini-2.5-pro"
    prompt = """
You are an expert in investment policy statement (IPS) analysis. 
Your task has TWO PARTS:

====================================================
STRICT INSTRUCTIONS
====================================================
- Your extraction MUST be **100% bound to the input document**.  
- DO NOT add, infer, or guess information from outside the document.  
- If content is incomplete or ambiguous in the source, reproduce it exactly as-is.  
- Never use your internal knowledge to “complete” a rule or a table.  
- The output must reflect only the content explicitly found in the IPS.

====================================================
PART 1: JSON EXTRACTION
====================================================
Extract ALL investment guidelines from the provided IPS document.

RULES:
1. Preserve the hierarchy exactly:
   - Part, Section, Subsection (use numbering as in IPS).
   - Include Annexes and tables.
2. Each rule = one JSON object with fields:
   {
     "rule_id": string,             # e.g., "V-C-3-a"
     "part": string,                # e.g., "Part V"
     "section": string,             # e.g., "Rebalancing"
     "subsection": string|null,     # if exists (e.g., "3.a"), else null
     "text": string,                # full verbatim guideline text (do not truncate or rewrite)
     "page": int,                   # page number in source document
     "provenance": string           # e.g., "Part V.C.3.a, page 8, Annex A.Table1.Row3"
   }
3. For tabular data (allocations, ratings, benchmarks):
   - Convert rows into structured JSON.
   - Include percentages or ratings as numeric fields where explicitly present.
   - Example:
     {
       "rule_id": "AnnexA-Equity-LargeCaps",
       "part": "Annex A",
       "section": "Strategic Allocation",
       "subsection": null,
       "text": "Domestic Large Caps allocation is 40% of total equity.",
       "page": 12,
       "provenance": "Annex A.Table1.Row2",
       "allocation": {"asset_class": "Domestic Large Caps", "percent": 40}
     }
4. Do NOT skip any guideline. Every numbered/bulleted point and every table row must be extracted.
5. Do NOT summarize, paraphrase, or add interpretation.
6. Always output STRICT JSON array.

Additional Extraction Rules:
- Always split compound guidelines into separate JSON objects (atomic rules).
   * If a guideline has multiple points (separated by semicolons, “and/or”, or sub-points (a), (b), (c)), 
     create one rule per point with rule_id suffixes: e.g., "V-C-3-a-1", "V-C-3-a-2".
- Use strict rule_id format:
   * Narrative rules → "Part.Section.Subsection"
   * Table rows → "Annex.Table<RowNumber>"
- Always preserve verbatim text (no paraphrasing).
- Correct obvious OCR typos (e.g., Bods → Bonds).
- For tables:
   * text = plain human-readable sentence
   * structured = JSON object with fields (asset_class, min, target, max, etc.)

For tables, do not duplicate content in the "text" field if structured fields already cover it.
- text: A plain sentence (e.g., "Global Equities target allocation is 61%").
- structured: { "asset_class": "Global Equities", "min": 56, "target": 61, "max": 66 }.


====================================================
PART 2: HUMAN-READABLE GUIDELINES
====================================================
Produce a human-readable digest of the SAME extracted content:

- Group by Part → Section → Subsection.
- Each rule shown as a bullet or sentence.
- Include provenance inline (e.g., “[Part V.C.3.a, page 8]”).
- Use verbatim text from the IPS (do not rewrite or summarize).
- Tables should be expanded into readable sentences per row.
- Human-readable output must group tables concisely under one heading.
- Use compact bullet formatting.
- Group table rows under a single table heading, with one line per asset/benchmark.
- Always show provenance inline [Section, Page].

Example:

Part V – Investment Strategy
  Section C – Rebalancing
    • If any major asset class deviates ±5% from its target allocation, the portfolio must be rebalanced. [Part V.C.3.a, page 8]

Annex A – Strategic Allocation
  • Domestic Large Caps allocation is 40% of total equity. [Annex A.Table1.Row2, page 12]

====================================================
OUTPUT FORMAT
====================================================
1. First output: JSON array of extracted guidelines (machine-readable).
2. Second output: Human-readable digest of guidelines (verbatim, compliance-friendly).

    """

    pdf_part = genai_types.Part(
        inline_data=genai_types.Blob(data=pdf_bytes, mime_type="application/pdf")
    )
    contents = [prompt, pdf_part]

    logging.info("Initiating Google AI API call...")
    logging.info(f"  - Model: {model_name}")
    logging.info(f"  - Prompt length: {len(prompt)} characters")
    logging.info(f"  - PDF size: {len(pdf_bytes)} bytes")

    start_time_utc = datetime.now(timezone.utc)

    response = client.models.generate_content(model=model_name, contents=contents)

    end_time_utc = datetime.now(timezone.utc)
    duration = (end_time_utc - start_time_utc).total_seconds()

    # Convert to IST for logging
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    start_time_ist = start_time_utc.astimezone(ist_tz)
    end_time_ist = end_time_utc.astimezone(ist_tz)

    logging.info("API call successful.")
    logging.info(f"  - Start Time: {start_time_ist.isoformat()}")
    logging.info(f"  - End Time: {end_time_ist.isoformat()}")
    logging.info(f"  - Total Turnaround Time (TAT): {duration:.2f} seconds")
    logging.info(f"  - Response length: {len(response.text)} characters")

    response_text = response.text.strip()

    # --- Robustly separate JSON and human-readable text ---
    json_string = extract_json_from_text(response_text)

    if not json_string:
        logging.error("No JSON found in the model's response.")
        logging.debug(f"Full response text: {response_text}")
        raise ValueError("No JSON found in the response")

    # The human-readable part is identified by its header
    human_readable_text = ""
    digest_header = "PART 2: HUMAN-READABLE GUIDELINES"
    header_pos = response_text.find(digest_header)
    if header_pos != -1:
        # Get the text after the header and clean it up
        human_readable_text = response_text[header_pos + len(digest_header) :]
        human_readable_text = re.sub(
            r"^=+\s*", "", human_readable_text, flags=re.MULTILINE
        ).strip()
    else:
        logging.warning("Human-readable digest header not found in the response.")

    parsed_json = json.loads(json_string)

    return parsed_json, human_readable_text
