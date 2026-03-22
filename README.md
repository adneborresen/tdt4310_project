# Semantic Search for Lecture Materials: BM25 vs SBERT


<div>
  <p><b>Ådne Børresen</b> • <b>Richard Kraus</b></p>
</div>

*Built for TDT4310 Intelligent Text Analysis at NTNU, Spring 2026.*

See [todo.md](todo.md) for an overview of what has been done and what needs to be done.


In this project we look at whether a neural search model can find the right lecture slide when a student asks a question in their own words, or if keyword matching does just as well.

This project builds a search system over NTNU lecture slides and compares two retrieval approaches:
- **BM25** — classic keyword-based ranking (does the question share words with the slide?)
- **SBERT** — neural embeddings that capture meaning (does the question *mean* the same thing as the slide?)

We test both on student-style questions, including paraphrased ones that deliberately use different words than the slides, and measure which system actually retrieves the right content.

## What this project does

1. **Extracts text from lecture PDFs:** each page is one slide, text is cleaned and stored as searchable chunk
2. **Indexes chunks** with both BM25 (lexical) and SBERT (semantic) retrieval
3. **Evaluates retrieval quality** using a local LLM judge + human review, measuring Recall@1/3/5
4. **Compares the two systems** across factual, conceptual, and paraphrase queries
5. **(Potentially) RAG extension:** feeds retrieved chunks to an LLM to generate answers

## Quick start

```bash
# Clone and set up
git clone https://github.com/adneborresen/tdt4310_project.git
cd tdt4310_project
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords')"

# Install Ollama (https://ollama.com) and pull a model
ollama pull llama3:8b
```

Then drop lecture PDFs into `data/raw_pdfs/tdt4310` and run the pipeline. Right now the lectures are just the TDT4310 lectures from 2026, directly downloaded from the Blacboard page, having removed the "full" part from the filenames.
The names are thus: tdt4310_2026_lect1.pdf, tdt4310_2026_lect2.pdf, etc.
The idea is to add more courses later, but we just set up the pipeline for now.

## Project structure

```
tdt4310_project/
├── config.py                 # All tunable parameters in one place
├── requirements.txt          # Python dependencies
├── src/
│   ├── __init__.py
│   ├── pdf_extraction.py     # PDF → per-slide text (pdfplumber)
│   ├── chunking.py           # Clean, filter, split into chunks
│   ├── bm25_search.py        # BM25 retrieval
│   ├── sbert_search.py       # SBERT retrieval
│   ├── llm_judge.py          # LLM-based relevance labeling
│   ├── evaluate.py           # Recall@k, MRR, statistical tests
│   └── rag.py                # RAG pipeline (extension)
├── data/
│   ├── raw_pdfs/             # Input lecture PDFs
│   ├── extracted_text/       # Per-lecture raw text (for inspection)
│   ├── chunks.jsonl          # Extracted + chunked slide text
│   └── questions.json        # Evaluation question set
├── notebooks/                # Exploration + analysis notebooks
└── results/                  # Retrieval results + metrics
```

## How it works

### Data pipeline

Lecture PDFs are processed with pdfplumber. Text is extracted directly from each page, cleaned, and stored as one chunk per slide. Tables are extracted separately. Image-heavy slides are flagged but kept in the corpus.

### Retrieval

Both systems search the same chunk corpus. BM25 uses tokenized keyword matching with NLTK. SBERT encodes chunks and queries into 384-dim vectors with `all-MiniLM-L6-v2` and ranks by cosine similarity.

### Evaluation

A local LLM (Llama 3 8B via Ollama) labels each retrieved chunk as relevant/partially relevant/not relevant. A subset is human-reviewed to verify label quality. We report Recall@k and MRR, broken down by question type. The interesting comparison is whether SBERT is better on paraphrase queries where BM25 can't match on keywords.

### Evaluation questions

We currently have 120 student-style questions (10 per lecture), generated with the help of an LLM based on the actual slide content. The questions cover three types: factual (35), conceptual (50), and paraphrase (35 — deliberately using different wording than the slides). They are stored in `data/questions.json` and will be human-reviewed before evaluation.

## Tech stack

- **pdfplumber** — PDF text extraction (1 page = 1 slide)
- **rank-bm25** — BM25Okapi implementation
- **sentence-transformers** — SBERT embeddings (all-MiniLM-L6-v2)
- **Ollama** — local LLM for evaluation and question generation
- **pandas / matplotlib / seaborn** — analysis and visualization


