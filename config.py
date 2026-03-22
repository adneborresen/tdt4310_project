# config.py — central configuration
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"
EXTRACTED_TEXT_DIR = DATA_DIR / "extracted_text"
CHUNKS_FILE = DATA_DIR / "chunks.jsonl"
EMBEDDINGS_FILE = DATA_DIR / "chunk_embeddings.npy"
QUESTIONS_FILE = DATA_DIR / "questions.json"
RESULTS_DIR = PROJECT_ROOT / "results"

# Chunking
MIN_CHUNK_WORDS = 5
MAX_CHUNK_WORDS = 300
OVERLAP_WORDS = 30
INCLUDE_SLIDE_TITLE = True

# BM25
BM25_K1 = 1.5
BM25_B = 0.75
BM25_USE_STEMMING = True
BM25_REMOVE_STOPWORDS = True
TOP_K = 10

# SBERT
SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# LLM Judge
OLLAMA_MODEL = "llama3:8b"

# Evaluation
RECALL_K_VALUES = [1, 3, 5]
