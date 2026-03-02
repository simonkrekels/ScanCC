"""OpenAI summarizer: generates one-line keyword summaries for ECHR cases."""

import os

PLACEHOLDER = "[Summary not available]"

# Style examples drawn from the reference document
STYLE_EXAMPLES = (
    "fair trial – lack of opportunity to challenge victim's statements; "
    "right to liberty – unlawful pre-trial detention; "
    "inhuman treatment – conditions of detention in psychiatric facility; "
    "freedom of expression – criminal conviction for online speech"
)

SYSTEM_PROMPT = (
    "You are a legal assistant specialising in European human rights law. "
    "Your task is to produce a concise one-line keyword summary of an ECHR "
    "communicated case in the style of the European Court's own case lists.\n\n"
    "Format: [right/issue] – [specific legal question or factual context]\n"
    "Examples:\n" + STYLE_EXAMPLES + "\n\n"
    "Rules:\n"
    "- Use lower case except for proper nouns\n"
    "- Separate multiple issues with a semicolon\n"
    "- Do NOT include the case name, application number, or country\n"
    "- Maximum 20 words\n"
    "- Output the summary line only, no preamble"
)

_TRANSLATE_SYSTEM = (
    "You are a legal translator. Translate the following French text from the "
    "European Court of Human Rights into clear, formal English. "
    "Preserve paragraph structure, headings, numbering, and legal terminology exactly. "
    "Do not summarise or omit anything."
)


def _client():
    """Return an OpenAI client using the configured API key."""
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    return OpenAI(api_key=api_key)


def _model() -> str:
    """Return the configured OpenAI model name."""
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def generate_summary(case_name: str, subject_matter_text: str) -> str:
    """
    Generate a one-line keyword summary for an ECHR case.

    Args:
        case_name: Full case name, e.g. "VLASHKI v. North Macedonia"
        subject_matter_text: Extracted subject matter / facts text

    Returns:
        One-line keyword summary string, or PLACEHOLDER on failure.
    """
    try:
        from openai import OpenAI  # noqa: F401 — verify package is installed
    except ImportError:
        print("  Warning: openai package not installed. Run: pip install openai")
        return PLACEHOLDER

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "sk-...":
        return PLACEHOLDER

    # Truncate to avoid excessive token usage
    truncated = subject_matter_text[:3000] if subject_matter_text else ""
    user_content = f"Case: {case_name}\n\nSubject matter:\n{truncated}"

    try:
        response = _client().chat.completions.create(
            model=_model(),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=60,
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
        # Strip surrounding quotes if the model added them
        summary = summary.strip('"').strip("'")
        return summary if summary else PLACEHOLDER
    except Exception as e:
        print(f"  Warning: OpenAI API error for '{case_name}': {e}")
        return PLACEHOLDER


def translate_case(subject_matter: str, questions: str) -> tuple[str, str]:
    """
    Translate French subject_matter and questions into English.
    Returns (translated_subject_matter, translated_questions).
    Falls back to original text on API error.
    """
    if not subject_matter and not questions:
        return subject_matter, questions

    SEPARATOR = "\n\n===QUESTIONS===\n\n"
    combined = subject_matter + SEPARATOR + questions

    try:
        response = _client().chat.completions.create(
            model=_model(),
            temperature=0.1,
            messages=[
                {"role": "system", "content": _TRANSLATE_SYSTEM},
                {"role": "user", "content": combined},
            ],
        )
        result = response.choices[0].message.content or ""
        if SEPARATOR in result:
            sm, q = result.split(SEPARATOR, 1)
            return sm.strip(), q.strip()
        return result.strip(), ""
    except Exception as e:
        print(f"  Warning: translation failed: {e}")
        return subject_matter, questions
