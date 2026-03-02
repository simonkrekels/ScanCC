"""HUDOC scraper: fetches communicated cases and their content."""

import re
import time
import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://hudoc.echr.coe.int/app/query/results"
CONTENT_URL = "https://hudoc.echr.coe.int/app/conversion/docx/html/body"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ECHRCasesBot/1.0)",
    "Accept": "application/json, text/html, */*",
}


def search_communicated_cases(start_date: str, end_date: str) -> list[dict]:
    """
    Search HUDOC for communicated cases in the given date range.

    Args:
        start_date: ISO date string, e.g. "2026-01-26"
        end_date:   ISO date string, e.g. "2026-02-09"

    Returns:
        List of case metadata dicts with keys:
        itemid, docname, appno, article, createddate, respondent
    """
    start_iso = f"{start_date}T00:00:00.000Z"
    end_iso = f"{end_date}T23:59:59.999Z"

    query = (
        f'documentcollectionid2:"COMMUNICATEDCASES" AND '
        f'(languageisocode:"ENG" OR languageisocode:"FRE") AND '
        f"createddate:[{start_iso} TO {end_iso}]"
    )

    cases = []
    start = 0
    page_size = 500

    while True:
        params = {
            "query": query,
            "select": "itemid,docname,appno,article,createddate,respondent,languageisocode",
            "sort": "createddate Ascending",
            "start": start,
            "length": page_size,
        }

        try:
            response = requests.get(
                SEARCH_URL, params=params, headers=HEADERS, timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"  Warning: search request failed: {e}")
            break
        except ValueError as e:
            print(f"  Warning: could not parse search response as JSON: {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        for item in results:
            doc = item.get("columns", item)
            cases.append(
                {
                    "itemid": doc.get("itemid", ""),
                    "docname": doc.get("docname", ""),
                    "appno": doc.get("appno", ""),
                    "article": doc.get("article", ""),
                    "createddate": doc.get("createddate", ""),
                    "respondent": doc.get("respondent", ""),
                    "languageisocode": doc.get("languageisocode", ""),
                }
            )

        if len(results) < page_size:
            break
        start += page_size
        time.sleep(0.5)

    return cases


def fetch_case_content(itemid: str) -> dict:
    """
    Fetch the full HTML content of a case and extract key sections.

    Args:
        itemid: HUDOC item ID, e.g. "001-230000"

    Returns:
        Dict with keys:
        - subject_matter: text of the subject matter section
        - questions: text of the questions to the parties section
        - raw_text: full plain text of the document (fallback)
    """
    # Note: no trailing slash — HUDOC returns 404 if present
    params = {"library": "ECHR", "id": itemid}

    try:
        response = requests.get(
            CONTENT_URL, params=params, headers=HEADERS, timeout=30
        )
        response.raise_for_status()
        html = response.text
    except requests.RequestException as e:
        print(f"  Warning: could not fetch content for {itemid}: {e}")
        return {"subject_matter": "", "questions": "", "raw_text": ""}

    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style noise
    for tag in soup(["script", "style"]):
        tag.decompose()

    full_text = _html_to_text(soup)

    subject_matter = _extract_section(
        full_text,
        start_patterns=[
            # English
            r"STATEMENT OF FACTS",
            r"THE FACTS",
            r"THE CIRCUMSTANCES OF THE CASE",
            r"SUBJECT.MATTER",
            r"FACTS AND PROCEDURE",
            r"I\.\s+THE FACTS",
            r"A\.\s+The facts",
            # French
            r"OBJET DE L[\u2019']AFFAIRE",
            r"EN FAIT",
            r"LES FAITS",
            r"EXPOS[EÉ] DES FAITS",
        ],
        end_patterns=[
            # English
            r"THE LAW",
            r"QUESTIONS TO THE\b",
            r"PROCEDURAL QUESTIONS",
            r"LIST OF APPLICATIONS",
            # French
            r"QUESTIONS AUX (?:PARTIES|GOUVERNEMENTS?)",
            r"QUESTIONS PROC[EÉ]DURALES",
        ],
    )

    questions = _extract_section(
        full_text,
        start_patterns=[
            # English
            r"QUESTIONS TO THE\b",
            r"PROCEDURAL QUESTIONS",
            # French
            r"QUESTIONS AUX (?:PARTIES|GOUVERNEMENTS?)",
            r"QUESTIONS PROC[EÉ]DURALES",
        ],
        end_patterns=[
            r"ANNEX(?:E|URE)?",
            r"APPENDIX",
            r"LIST OF APPLICATIONS",
        ],
    )

    # Detect whether the document has an appendix/annex section
    has_appendix = bool(re.search(
        r"^\s*(?:ANNEX(?:E|URE)?|APPENDIX|LIST OF APPLICATIONS)\b",
        full_text, re.IGNORECASE | re.MULTILINE,
    ))

    # If structured extraction failed, fall back to first ~2000 chars of text
    if not subject_matter:
        subject_matter = _clean_text(full_text[:3000])

    return {
        "subject_matter": _clean_text(subject_matter),
        "questions": _clean_text(questions),
        "raw_text": _clean_text(full_text[:5000]),
        "has_appendix": has_appendix,
    }


def _html_to_text(soup) -> str:
    """
    Convert BeautifulSoup tree to clean plain text.

    Strategy: iterate only over paragraph-level elements (p, headings, li) and
    join each one's inline content with a space.  This avoids two problems:
    - get_text(separator="\\n") inserts a newline between every <span>, breaking
      inline text into fragments
    - Including <div>/<body> in the set causes text to be emitted multiple times
      (once for the container, then again for each child <p>)
    """
    lines = []
    for elem in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
        raw = elem.get_text(separator=" ")
        raw = raw.replace("\xa0", " ")
        raw = re.sub(r"[ \t]+", " ", raw).strip()
        if raw:
            lines.append(raw)
    return "\n".join(lines)


def _extract_section(
    text: str, start_patterns: list[str], end_patterns: list[str]
) -> str:
    """Extract a section of text between start and end patterns."""
    start_idx = None

    for pattern in start_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            # Skip past the rest of the heading line so nothing from the
            # title leaks into the body (e.g. "OF THE CASE" after "SUBJECT MATTER")
            newline_pos = text.find("\n", match.end())
            start_idx = newline_pos if newline_pos != -1 else match.end()
            break

    if start_idx is None:
        return ""

    section = text[start_idx:]

    # Find the earliest end boundary across all patterns (not just the first
    # pattern in list order that happens to match somewhere in the text).
    end_idx = None
    for pattern in end_patterns:
        match = re.search(pattern, section, re.IGNORECASE | re.MULTILINE)
        if match and match.start() > 50:
            if end_idx is None or match.start() < end_idx:
                end_idx = match.start()
    if end_idx is not None:
        section = section[:end_idx]

    return section.strip()


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove excessive blank lines."""
    # Normalise non-breaking spaces that slipped through
    text = text.replace("\xa0", " ")
    lines = text.splitlines()
    cleaned = []
    blank_count = 0
    for line in lines:
        stripped = re.sub(r" +", " ", line).strip()
        if stripped:
            blank_count = 0
            cleaned.append(stripped)
        else:
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
    return "\n".join(cleaned).strip()
