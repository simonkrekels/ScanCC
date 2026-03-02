"""ECHR Communicated Cases Scanner — interactive entry point."""

import os
import sys
from datetime import datetime

# Load .env before any other imports so API keys are available
from dotenv import load_dotenv
load_dotenv()

from scraper import search_communicated_cases, fetch_case_content
from summarizer import generate_summary, translate_case
from document import build_document


def _prompt(prompt_text: str, default: str = "") -> str:
    if default:
        value = input(f"{prompt_text} [{default}]: ").strip()
        return value if value else default
    return input(f"{prompt_text}: ").strip()


def _parse_date(date_str: str) -> str | None:
    """Validate YYYY-MM-DD format. Returns the date string or None if invalid."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        print(f"  Error: '{date_str}' is not a valid date. Use YYYY-MM-DD format.")
        return None


def _check_api_key():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key or key == "sk-...":
        print(
            "\n  Note: OPENAI_API_KEY is not set in your .env file.\n"
            "  Keyword summaries will be replaced with '[Summary not available]'.\n"
            "  See README.md for setup instructions.\n"
        )


def main():
    print("=" * 60)
    print("  ECHR Communicated Cases Scanner")
    print("=" * 60)
    print()

    _check_api_key()

    # ── User prompts ─────────────────────────────────────────────────────────
    while True:
        start_str = _prompt("Start date (YYYY-MM-DD)")
        start_date = _parse_date(start_str)
        if start_date:
            break

    while True:
        end_str = _prompt("End date   (YYYY-MM-DD)")
        end_date = _parse_date(end_str)
        if end_date:
            break

    if end_date < start_date:
        print("  Error: End date must be on or after start date.")
        sys.exit(1)

    output_file = _prompt("Output filename", default="communicated_cases.docx")
    if not output_file.endswith(".docx"):
        output_file += ".docx"

    print()

    # ── Step 1: Search ───────────────────────────────────────────────────────
    print(f"Fetching cases from HUDOC ({start_date} → {end_date})...")
    cases = search_communicated_cases(start_date, end_date)

    if not cases:
        print(
            "\n  No communicated cases found for this date range.\n"
            "  Try widening the range or check the HUDOC website directly."
        )
        sys.exit(0)

    print(f"Found {len(cases)} case{'s' if len(cases) != 1 else ''}. "
          "Fetching content and generating summaries...\n")

    # ── Step 2: Enrich each case ─────────────────────────────────────────────
    for i, case in enumerate(cases, start=1):
        case_name = case.get("docname", f"Case {i}")
        print(f"  [{i}/{len(cases)}] {case_name}")

        # Fetch full text
        content = fetch_case_content(case["itemid"])
        case["subject_matter"] = content["subject_matter"]
        case["questions"]      = content["questions"]
        case["raw_text"]       = content["raw_text"]

        # Translate French cases into English before summarising
        if case.get("languageisocode", "").upper() == "FRE":
            print(f"    Translating French case to English...")
            case["subject_matter"], case["questions"] = translate_case(
                case["subject_matter"], case["questions"]
            )

        # Generate keyword summary
        text_for_summary = case["subject_matter"] or case["raw_text"]
        case["summary"] = generate_summary(case_name, text_for_summary)

    print()

    # ── Step 3: Build document ───────────────────────────────────────────────
    print("Building Word document...")
    build_document(cases, output_file)
    print()
    print(f"Done! Open '{output_file}' in Microsoft Word or LibreOffice.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Cancelled by user.")
        sys.exit(0)
