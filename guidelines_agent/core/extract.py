import os
import logging
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
import json
import re
from typing import Dict, Any

# --- Custom Logging Configuration ---
# (Assuming ISTFormatter and logger setup remains the same)
class ISTFormatter(logging.Formatter):
    """A custom logging formatter to display timestamps in IST."""
    def formatTime(self, record, datefmt=None):
        utc_dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        ist_dt = utc_dt.astimezone(ist_tz)
        if datefmt:
            return ist_dt.strftime(datefmt)
        return ist_dt.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(ISTFormatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
# --- End of Logging Configuration ---

def extract_json_from_text(text: str) -> str:
    """More robustly extracts a JSON object from a string."""
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    start_index = text.find("{")
    end_index = text.rfind("}")
    if start_index != -1 and end_index != -1:
        return text[start_index : end_index + 1]
    return None

def extract_guidelines_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Core logic to extract and validate guidelines from a PDF file using the Gemini API.
    Returns a single dictionary containing validation status and extracted data.
    """
    model_name = "gemini-1.5-pro"
    prompt = """
You are an expert financial document analyst. Your task is to analyze the provided document and determine if it is an Investment Policy Statement (IPS). Then, you will extract its contents. 

Your output MUST be a single, valid JSON object.

====================================================
TASK & OUTPUT STRUCTURE
====================================================
{
  "is_valid_document": boolean,
  "validation_summary": string,
  "portfolio_id": string,
  "portfolio_name": string,
  "doc_id": string,
  "doc_name": string,
  "doc_date": string,
  "guidelines": array | null,
  "human_readable_digest": string | null
}

====================================================
FIELD DESCRIPTIONS
====================================================
1.  `is_valid_document`:
    - true if the document is an Investment Policy Statement (IPS) or similar investment guideline.
    - false otherwise (e.g., brochure, marketing doc, quarterly report).

2.  `validation_summary`:
    - One sentence explaining your decision.
    - Example (true): "The document is a valid Investment Policy Statement for the PRIM board."
    - Example (false): "The document appears to be a marketing brochure and does not contain investment guidelines."

3.  `portfolio_id`:
    - If valid: extract the most concise portfolio/entity ID (e.g., "PBGC", "UNJSPF").
    - If invalid: derive from content if possible, else "Unknown Portfolio".

4.  `portfolio_name`:
    - If valid: the descriptive portfolio name (e.g., "PBGC Single-Employer Policy Portfolio").
    - If invalid: "Unknown Portfolio".

5.  `doc_id`:
    - Combine `portfolio_id` and `doc_date`. Example: "PBGC_2019-04-01".

6.  `doc_name`:
    - Official document title (cover page or header).

7.  `doc_date`:
    - Publication/effective date in YYYY-MM-DD.
    - If day not given, default to '01'.

8.  `guidelines`:
    - If invalid: null.
    - If valid: extract ALL rules into an array of JSON objects, each with:
        {
          "rule_id": string (unique, sequential),
          "part": string (e.g., "V"),
          "section": string (heading/subheading),
          "subsection": string | null,
          "text": string (verbatim rule/constraint),
          "page": integer,
          "provenance": string (section headings),
          "structured_data": object | null (for tables/ranges, optional)
        }
    - Consider as a guideline **any**: objective, constraint, policy, requirement, limit, permitted/prohibited activity, responsibility, benchmark, threshold, or range.
    - Include rules from prose, numbered/bulleted lists, AND tables.

9.  `human_readable_digest`:
    - If invalid: null.
    - If valid: a digest grouped by section, rules expressed in plain sentences, with inline provenance and page refs.

====================================================
STRICT EXTRACTION RULES
====================================================
- Do not omit rules: cover objectives, strategic considerations, governance, asset allocation, benchmarks, ranges, LDI targets, permitted/prohibited activities, ownership/security limits, reporting, and risk mgmt.
- Capture tables (like asset allocation ranges) as structured_data objects (array of row objects).
- Text must be verbatim from document, no paraphrasing.
- If in doubt, include it as a guideline.
- Output must remain valid JSON.

====================================================
EXAMPLES (MUST FOLLOW THESE EXACT OBJECT FORMATS)
====================================================

Example A — Permitted activity: Derivatives
{
  "rule_id": "PERM-001",
  "part": "V",
  "section": "Permitted Activities and Delegations",
  "subsection": "Derivatives",
  "text": "Derivatives may be utilized only to take or support positions relating to allowed asset classes for non-speculative purposes.",
  "page": 6,
  "provenance": "V. Permitted Activities and Delegations; 2. Derivatives",
  "structured_data": {
    "type": "permitted_activity",
    "name": "Derivatives",
    "allowed_purposes": [
      "hedging",
      "liability-driven positioning",
      "cash management"
    ],
    "prohibitions": [
      "use for leverage to replicate leveraged positions",
      "speculative trading"
    ],
    "governing_phrase": "non-speculative purposes"
  }
}

Example B — Ownership limit (hard numeric constraint)
{
  "rule_id": "LIMIT-001",
  "part": "V",
  "section": "Other Requirements and Limitations",
  "subsection": "Ownership Limit",
  "text": "PBGC will limit its holding of any class of securities in any company to no more than five percent of the total outstanding securities of such class.",
  "page": 8,
  "provenance": "V. Other Requirements and Limitations; 1. Ownership Limit",
  "structured_data": {
    "type": "numeric_limit",
    "subject": "holding of any class of securities in any company",
    "threshold": 5,
    "threshold_unit": "percent",
    "action_on_violation": "liquidate sufficient securities as soon as prudently feasible to reduce to threshold"
  }
}

Example C — Performance / Reporting requirement
{
  "rule_id": "REPORT-001",
  "part": "VI",
  "section": "Performance Reporting and Risk Management",
  "subsection": "Performance Reporting",
  "text": "Monthly and quarterly investment reports will be prepared by PBGC and will be submitted by the Director to the Board.",
  "page": 6,
  "provenance": "VI. Performance Reporting and Risk Management; a. Performance Reporting",
  "structured_data": {
    "type": "reporting_requirement",
    "reports": [
      {
        "name": "Monthly investment report",
        "recipient": "Director -> Board",
        "frequency": "monthly"
      },
      {
        "name": "Quarterly investment performance report",
        "recipient": "Director -> Board; Advisory Committee",
        "frequency": "quarterly"
      }
    ],
    "notes": "Include performance metrics, manager breaches, and comparative benchmarks"
  }
}

End of examples.
"""
    
    logging.info(f"Starting extraction and validation for: {pdf_path}")
    
    pdf_file = genai.upload_file(path=pdf_path, mime_type="application/pdf")
    contents = [prompt, pdf_file]

    logging.info("Initiating Google AI API call...")
    logging.info(f"  - Model: {model_name}")
    logging.info(f"  - PDF size: {os.path.getsize(pdf_path)} bytes")

    start_time_utc = datetime.now(timezone.utc)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(contents)
    end_time_utc = datetime.now(timezone.utc)
    duration = (end_time_utc - start_time_utc).total_seconds()
    
    logging.info(f"API call successful. Turnaround Time (TAT): {duration:.2f} seconds")

    response_text = response.text.strip()
    json_string = extract_json_from_text(response_text)

    if not json_string:
        logging.error("No JSON object found in the model's response.")
        logging.debug(f"Full response text: {response_text}")
        # Return a failure state if the model's output is malformed
        return {
            "is_valid_document": False,
            "validation_summary": "Failed to process the document due to a malformed response from the AI model.",
            "guidelines": None,
            "human_readable_digest": None
        }

    try:
        parsed_json = json.loads(json_string)
        logging.info(f"Successfully parsed JSON. Validation status: {parsed_json.get('is_valid_document')}")
        return parsed_json
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from the model's response: {e}")
        logging.debug(f"Invalid JSON string: {json_string}")
        return {
            "is_valid_document": False,
            "validation_summary": "Failed to process the document due to an invalid JSON structure in the AI response.",
            "guidelines": None,
            "human_readable_digest": None
        }