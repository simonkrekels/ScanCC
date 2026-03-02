# ECHR Communicated Cases Scanner

Automatically fetches ECHR "communicated cases" from HUDOC, generates one-line keyword summaries with OpenAI, and produces a formatted Word document.

---

## Requirements

- **Python 3.10 or newer** — [Download here](https://www.python.org/downloads/)
- An **OpenAI API key** — [Get one here](https://platform.openai.com/api-keys)
- Internet connection (to reach HUDOC and OpenAI)

---

## Setup (one-time)

### 1. Install Python packages

Open a terminal (on Mac: **Terminal** app; on Windows: **Command Prompt** or **PowerShell**) and run:

```
pip install -r requirements.txt
```

If `pip` is not recognised, try:

```
pip3 install -r requirements.txt
```

### 2. Set your OpenAI API key

1. In the project folder, find the file called `.env.example`
2. Make a copy of it and rename the copy to `.env`
3. Open `.env` in any text editor (Notepad, TextEdit, etc.)
4. Replace `sk-...` with your actual OpenAI API key:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
```

5. Save and close the file.

> **Note:** The script will still run without an API key — it will use `[Summary not available]` as a placeholder for keyword summaries.

---

## Running the script

In the terminal, navigate to the project folder:

```
cd /path/to/echr-communicated-cases
```

Then run:

```
python main.py
```

You will be asked three questions:

| Prompt | Example |
|--------|---------|
| Start date (YYYY-MM-DD) | `2026-01-26` |
| End date (YYYY-MM-DD) | `2026-02-09` |
| Output filename | `communicated_cases.docx` |

The script will then:
1. Fetch matching cases from the ECHR HUDOC database
2. Download the full text of each case
3. Generate a one-line keyword summary via OpenAI
4. Save a formatted Word document to the project folder

---

## Output format

The `.docx` file contains:
- A **title page** with the date range
- A **table of contents** — one entry per case with keyword summary in italics
- A **full section per case** with heading, application number, articles, keyword summary subtitle, facts, and questions to the parties

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'requests'` | Run `pip install -r requirements.txt` again |
| `No cases found` | Check that the date range is correct; try a wider range |
| Summaries say `[Summary not available]` | Check that your `.env` file exists and contains a valid API key |
| `python: command not found` | Use `python3` instead of `python` |

---

## Privacy

Case texts are fetched directly from the public ECHR HUDOC database. The subject matter text of each case is sent to the OpenAI API for summarisation. Do not run the script on confidential documents.
