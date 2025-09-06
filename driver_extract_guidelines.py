# ==============================================================================
# --- DEVELOPER ASSISTANCE SCRIPT ---
# This script is a one-time utility for developers. Its purpose is to process
# a directory of PDF investment policy statements and generate the initial
# structured JSON and human-readable Markdown files.
#
# These generated files serve as the source data for the 'ingest' command
# and can be used for cross-referencing with database entries during development.
#
# This script is NOT part of the main application workflow or the API.
# ==============================================================================
import glob
import os
import json
import re
from datetime import datetime
from extract import extract_guidelines_from_pdf


def generate_clean_id(text):
    """Generates a clean, lowercase ID from a string."""
    text = text.lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_]", "", text)
    return text


# Path to Investment Policy Statement PDFs
pdf_dir = "/home/sundar/Sample Investment Policy Statements"
pdf_pattern = "*.pdf"  # Process all PDFs in the directory
pdf_paths = glob.glob(os.path.join(pdf_dir, pdf_pattern))

# Output directory for results
output_dir = "results"
os.makedirs(output_dir, exist_ok=True)

for pdf_path in pdf_paths:
    print(f"Extracting guidelines from: {pdf_path}")
    try:
        guidelines_list, guidelines_text = extract_guidelines_from_pdf(pdf_path)

        base_name = os.path.basename(pdf_path)
        file_name_without_ext = os.path.splitext(base_name)[0]

        # --- Generate Metadata ---
        # For now, we'll treat each document as its own portfolio.
        portfolio_name = file_name_without_ext
        portfolio_id = generate_clean_id(portfolio_name)

        doc_name = base_name
        doc_id = portfolio_id  # Since it's one doc per portfolio for now
        doc_date = datetime.now().strftime("%Y-%m-%d")

        # --- Create Final JSON Structure ---
        output_data = {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio_name,
            "doc_id": doc_id,
            "doc_name": doc_name,
            "doc_date": doc_date,
            "guidelines": guidelines_list,
        }

        # --- Save Output Files ---
        json_filename = f"{file_name_without_ext}.json"
        md_filename = f"{file_name_without_ext}.md"

        json_filepath = os.path.join(output_dir, json_filename)
        md_filepath = os.path.join(output_dir, md_filename)

        # Save the structured JSON file
        with open(json_filepath, "w") as f:
            json.dump(output_data, f, indent=2)

        # Save the human-readable digest as a Markdown file
        with open(md_filepath, "w") as f:
            f.write(guidelines_text)

        print(f"Successfully extracted {len(guidelines_list)} guidelines.")
        print(f"  - JSON saved to: {json_filepath}")
        print(f"  - Digest saved to: {md_filepath}")

    except Exception as e:
        print(f"Could not process {pdf_path}. Error: {e}")
