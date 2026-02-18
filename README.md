# AI Job Recommender

End-to-end desktop application that scrapes job listings from Wuzzuf, parses a candidate CV (PDF/DOCX), and ranks the best-matching roles using a similarity score (semantic + skills + experience).

## Highlights

- **Modern desktop UI**: PyQt6 interface with background worker for scraping and ranking.
- **Job data pipeline**: Requests/BeautifulSoup for listings + Selenium for job detail extraction.
- **Similarity-based ranking**: Sentence-Transformers semantic similarity combined with skill and experience alignment.
- **CV parsing**: Extracts text from PDF/DOCX; uses a local LLM (Ollama) to extract skills and infer experience ranges.

## Tech stack

- **Python**: PyQt6, Selenium, Requests, BeautifulSoup4
- **NLP / Matching**: Sentence-Transformers (cosine similarity)
- **CV parsing**: PyMuPDF (PDF), python-docx (DOCX)
- **LLM (local)**: Ollama (for skills + experience extraction)

## Repository structure

```text
src/
  main.py                 # app entry point (enables logging)
  models.py               # Job + CVData dataclasses and parsing helpers
  cv_parser.py            # CV parsing (PDF/DOCX) + skill/experience extraction
  scraper.py              # Wuzzuf scraping (listings + Selenium job details)
  similarity.py           # similarity scoring + top-k ranking
  ui/                     # PyQt6 UI components
    app.py
    worker.py
    dialogs.py
    widgets.py
    styles.py
  utils/
    job_details_extractor.js
```

## Quickstart (Windows)

1) Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

2) Install Python dependencies:

```bash
pip install -r requirements.txt
```

3) Install and run Ollama (required by `src/cv_parser.py`):

- Install Ollama and start the service (must be reachable at `http://127.0.0.1:11434`).
- Pull the default model used by this project:

```bash
ollama pull llama3.2
```

4) Ensure **Google Chrome** is installed (used by Selenium for Wuzzuf job details).

5) Run the app:

```bash
cd src
python main.py
```

## How it works (high level)

1) **Scrape listings** from Wuzzuf search results.
2) **Fetch job details** per listing using Selenium and `src/utils/job_details_extractor.js` (skills, requirements, etc.).
3) **Parse the CV** to extract raw text, skills list, and estimate experience years.
4) **Score and rank jobs** with a weighted similarity score:
   - semantic similarity (CV text vs job requirements)
   - skill similarity (skill-to-skill matching)
   - experience fit (CV years vs required years)

## Troubleshooting

- **Job details show as N/A**
  - Confirm Chrome is installed.
  - Selenium requires a working Chrome/driver setup. New Selenium versions can auto-manage drivers, but if it fails, install a compatible ChromeDriver and ensure it is on PATH.
  - Check console logs; `scraper.py` logs detail extraction progress and warnings.

- **Ollama errors / connection refused**
  - Ensure Ollama is running locally and reachable at `http://127.0.0.1:11434`.
  - Ensure the model exists: `ollama pull llama3.2`.

## Notes

- This project scrapes a third-party website (Wuzzuf). Ensure your usage complies with their terms and rate limits.

## License

MIT — see `LICENSE`.
