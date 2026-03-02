# ECHR Communicated Cases Scanner

This tool automatically fetches "communicated cases" from the ECHR website, generates a one-line keyword summary for each case using OpenAI, and saves everything as a formatted Word document.

---

## What you need before starting

- A Python installation (available from [python.org/downloads](https://www.python.org/downloads/); see below)
- An OpenAI API key — [get one here](https://platform.openai.com/api-keys) (you need a paid account)
- An internet connection

---

## One-time setup

Do these steps once, in order. You won't need to repeat them.

### Step 1 — Install Python

Download and install Python from [python.org/downloads](https://www.python.org/downloads/). 

> **Windows users:** during installation, make sure to tick the box that says **"Add Python to PATH"** before clicking Install.

Once installed, you can verify it worked by opening a terminal and typing `python --version`. You should see a version number.

- On **Mac**: open the **Terminal** app (search for it with Spotlight — press `Cmd + Space` and type "Terminal")
- On **Windows**: open **Command Prompt** (press the Windows key, type "cmd", press Enter)

### Step 2 — Download this project

Click the green **Code** button at the top of this page, then click **Download ZIP**. Once downloaded, unzip the folder somewhere easy to find, like your Desktop.

### Step 3 — Open a terminal in the project folder

You need to navigate the terminal into the folder you just unzipped.

**On Mac:**
1. Open Terminal
2. Type `cd ` (with a space after it, don't press Enter yet)
3. Drag the unzipped project folder from Finder into the Terminal window — it will fill in the path automatically
4. Press Enter

**On Windows:**
1. Open the unzipped project folder in File Explorer
2. Click on the address bar at the top (where the folder path is shown)
3. Type `cmd` and press Enter — a Command Prompt window will open directly in that folder

### Step 4 — Install the required packages

In the terminal, paste the following and press Enter:

```
pip install -r requirements.txt
```

If you see an error saying `pip` was not found, try:

```
pip3 install -r requirements.txt
```

Wait for it to finish. This only needs to be done once.

### Step 5 — Add your OpenAI API key

1. In the project folder, find the file called `.env.example`
2. Make a copy of it and rename the copy to `.env` (just remove the `.example` part)
3. Open `.env` with any text editor (Notepad on Windows, TextEdit on Mac)
4. Replace `sk-...` with your actual OpenAI API key, so it looks like:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
```

5. Save and close the file

> **Note:** if you skip this step, the script will still run but will use `[Summary not available]` instead of real keyword summaries.

---

## Running the script

Every time you want to generate a document:

1. Open a terminal in the project folder (same as Step 3 above)
2. Run:

```
python main.py
```

If that gives an error, try `python3 main.py` instead.

3. The script will ask you three questions:

| Question | Example answer |
|----------|----------------|
| Start date | `2026-01-26` |
| End date | `2026-02-09` |
| Output filename | `communicated_cases.docx` |

4. The script will fetch the cases, generate summaries, and save a Word document in the project folder.

---

## What the output looks like

The Word document contains:
- A title page with the date range
- A table of contents with one entry per case (keyword summary in italics)
- A full section per case with the heading, application number, relevant articles, keyword summary, facts, and questions to the parties

---

## Troubleshooting

| Problem | What to do |
|---------|------------|
| `ModuleNotFoundError: No module named 'requests'` | Run `pip install -r requirements.txt` again |
| `No cases found` | Check that the date range is correct and try a slightly wider range |
| Summaries say `[Summary not available]` | Make sure your `.env` file exists and contains a valid API key |
| `python: command not found` | Use `python3` instead of `python` |
| `.env.example` doesn't show up in the folder | Your file browser may be hiding files that start with a dot — on Mac, press `Cmd + Shift + .` to show hidden files |

---

## Privacy

Case texts are fetched from the public ECHR HUDOC database. The text of each case is sent to the OpenAI API to generate the keyword summary. Do not use this tool on confidential documents.
