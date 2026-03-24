"""Central configuration for the entire pipeline.

Every module imports its settings from here so there is a single source of
truth for paths, model names, and tuning parameters. If you need to change
a directory, tweak a hyperparameter, or swap a model — do it here.
"""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────
# All paths are derived from PROJECT_ROOT so the project stays portable.
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"          # Input lecture PDFs go here
EXTRACTED_TEXT_DIR = DATA_DIR / "extracted_text"  # Plain-text per lecture (for inspection)
CHUNKS_FILE = DATA_DIR / "chunks.jsonl"        # One JSON object per chunk
EMBEDDINGS_FILE = DATA_DIR / "chunk_embeddings.npy"  # Pre-computed SBERT vectors
QUESTIONS_FILE = DATA_DIR / "questions.json"   # Evaluation question bank
RESULTS_DIR = PROJECT_ROOT / "results"

# ── Chunking ─────────────────────────────────────────────────────────────
# Controls how slide text is split into retrieval units (chunks).
MIN_CHUNK_WORDS = 5          # Slides with fewer words are dropped (likely title-only)
MAX_CHUNK_WORDS = 300        # Slides exceeding this are sub-split with overlap
OVERLAP_WORDS = 30           # Word overlap between sub-split segments
INCLUDE_SLIDE_TITLE = True   # Prepend the slide title to every chunk's text

# ── BM25 (keyword-based retrieval) ───────────────────────────────────────
# Classic term-frequency ranking. K1 and B are the standard Okapi BM25 knobs.
BM25_K1 = 1.5               # Term-frequency saturation (higher → less saturation)
BM25_B = 0.75               # Document-length normalization (0 = none, 1 = full)
BM25_USE_STEMMING = True     # Reduce words to stems (e.g. "running" → "run")
BM25_REMOVE_STOPWORDS = True # Drop common words like "the", "is", "at"
TOP_K = 10                   # Number of results to return per query

# ── SBERT (semantic retrieval) ───────────────────────────────────────────
# Sentence-BERT encodes text into dense vectors; retrieval uses cosine similarity.
SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ── LLM Judge ────────────────────────────────────────────────────────────
# A local Ollama model scores retrieved chunks for relevance (0/1/2).
OLLAMA_MODEL = "llama3:8b"

# ── Evaluation ───────────────────────────────────────────────────────────
# Recall@k measures how many relevant chunks appear in the top-k results.
RECALL_K_VALUES = [1, 3, 5]
