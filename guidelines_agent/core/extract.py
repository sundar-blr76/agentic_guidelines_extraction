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
    model_name = "gemini-1.5-pro-latest"
    prompt = """
You are an expert financial document analyst. Your task is to analyze the provided document and determine if it is an Investment Policy Statement (IPS). Then, you will extract its contents.

Your output MUST be a single, valid JSON object.

====================================================
TASK & OUTPUT STRUCTURE
====================================================
Analyze the document and produce a JSON object with the following structure:

{
  "is_valid_document": boolean,
  "validation_summary": string,
  "guidelines": array | null,
  "human_readable_digest": string | null
}

====================================================
FIELD DESCRIPTIONS
====================================================
1.  `is_valid_document`:
    - Set to `true` if the document is an Investment Policy Statement (IPS) or a similar set of investment guidelines.
    - Set to `false` if it is any other type of document (e.g., a marketing brochure, a lunch menu, a quarterly report).

2.  `validation_summary`:
    - A concise, one-sentence explanation of your decision.
    - Example (if true): "The document is a valid Investment Policy Statement for the PRIM board."
    - Example (if false): "The document appears to be a marketing brochure and does not contain investment guidelines."

3.  `guidelines`:
    - If `is_valid_document` is `false`, this field MUST be `null`.
    - If `true`, extract ALL investment guidelines into a JSON array. Each rule must be a JSON object with the fields: "rule_id", "part", "section", "subsection", "text", "page", "provenance", and optionally "structured_data".
    - STRICTLY follow all extraction rules from the previous version (hierarchy, verbatim text, tables, etc.).

4.  `human_readable_digest`:
    - If `is_valid_document` is `false`, this field MUST be `null`.
    - If `true`, produce a human-readable digest of the extracted content, grouped by section, with inline provenance.

====================================================
STRICT INSTRUCTIONS
====================================================
- Your entire output must be a single, valid JSON object. Do not include any text before or after the JSON block.
- If the document is not a valid IPS, you MUST set `guidelines` and `human_readable_digest` to `null`.
- Your extraction of guidelines (if valid) MUST be 100% bound to the input document. Do not infer or add external information.
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