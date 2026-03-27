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
MIN_CHUNK_WORDS = 1          # Only truly empty slides are dropped; title-only slides kept
MAX_CHUNK_WORDS = 200        # SBERT truncates at ~256 tokens; 200 words ≈ safe limit
OVERLAP_WORDS = 30           # Word overlap between sub-split segments
INCLUDE_SLIDE_TITLE = True   # Prepend the slide title to every chunk's text

# ── Image detection ───────────────────────────────────────────────────────
# The NTNU slide template includes a decorative 68×540pt sidebar on every page.
# We exclude images narrower than this threshold so only real content images
# (diagrams, figures, photos) are counted. Tune if switching to a different
# slide template.
MIN_IMAGE_WIDTH = 100        # minimum width in points to count as a content image

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

# ── Question Generation ──────────────────────────────────────────────────
# Controls automated question generation from chunks using a local LLM.
# Run: python src/question_gen.py
OLLAMA_MODEL = "llama3:8b"           # Model used for question gen and LLM judge
QUESTIONS_PER_CHUNK = 1              # Questions to generate per chunk
QUESTION_TYPES = ["factual", "conceptual", "practical"]
#   factual    → recall a specific fact directly stated in the slide
#   conceptual → explain or compare a concept described in the slide
#   practical  → apply, implement, or describe how to use something from the slide
# Demo mode — uncomment one line, comment out the other:
# DEMO_LECTURES: list[int] | None = None      # full run (all lectures)
DEMO_LECTURES: list[int] | None = [1, 2] # demo: only lectures 1 and 2

# ── LLM Judge ────────────────────────────────────────────────────────────
# A local Ollama model (OLLAMA_MODEL above) scores retrieved chunks:
#   0 = not relevant  |  1 = partially relevant  |  2 = highly relevant
# Used as a secondary, soft-relevance layer on top of exact-match evaluation.
# See src/llm_judge.py for full design rationale and usage.
JUDGE_SCORE_THRESHOLD = 1            # Minimum score to count as "relevant" in soft eval

# ── Vision / Image-to-Text (NOT YET ENABLED) ─────────────────────────────
# Future: use a multimodal model to describe images on slides so they become
# searchable. Plug in via VISION_ENABLED=True once implement in pdf_extraction.py.
VISION_MODEL = "llava:7b"            # Multimodal model for describing slide images
#   Common options: "llava:7b", "llava:13b", "llama3.2-vision", "bakllava"
#   Install via: ollama pull <model_name>
VISION_ENABLED = False               # Set True when image description is implemented

# ── Evaluation ───────────────────────────────────────────────────────────
# Recall@k measures how many relevant chunks appear in the top-k results.
RECALL_K_VALUES = [1, 3, 5]
