"""Chunking module — turns extracted slides into searchable chunks.

Each slide normally becomes one chunk. Slides exceeding MAX_CHUNK_WORDS are
sub-split into overlapping segments so that SBERT (which truncates at ~256
tokens) never loses content.

Usage:
    python src/chunking.py        # extracts PDFs → builds chunks → saves chunks.jsonl
"""

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    RAW_PDFS_DIR,
    CHUNKS_FILE,
    MIN_CHUNK_WORDS,
    MAX_CHUNK_WORDS,
    OVERLAP_WORDS,
    INCLUDE_SLIDE_TITLE,
)
from src.pdf_extraction import extract_all_pdfs


def build_chunk_id(course: str, lecture: int, slide_number: int, part: int | None = None) -> str:
    """Build a deterministic chunk ID.

    Returns e.g. "tdt4310_lect1_slide15" or "tdt4310_lect1_slide15_part2".
    """
    chunk_id = f"{course}_lect{lecture}_slide{slide_number}"
    if part is not None:
        chunk_id += f"_part{part}"
    return chunk_id


def build_chunk_text(title: str, text: str, include_title: bool = True) -> str:
    """Construct searchable text for a chunk.

    Prepends the slide title if configured and not already present at the
    start of the cleaned text.
    """
    if include_title and title and not text.startswith(title):
        return f"{title}\n{text}"
    return text


def split_long_text(text: str, max_words: int, overlap: int) -> list[str]:
    """Split text exceeding max_words into overlapping segments.

    Each segment is at most max_words long. Consecutive segments share
    `overlap` words so context is not lost at boundaries.
    """
    words = text.split()
    if len(words) <= max_words:
        return [text]

    segments = []
    start = 0
    while start < len(words):
        end = start + max_words
        segment = " ".join(words[start:end])
        segments.append(segment)
        if end >= len(words):
            break
        start = end - overlap
    return segments


def build_chunks(slides: list[dict]) -> tuple[list[dict], list[dict]]:
    """Convert extracted slides into chunks.

    Returns (kept_chunks, filtered_slides) so the caller can inspect
    what was dropped.
    """
    kept: list[dict] = []
    filtered: list[dict] = []

    for slide in slides:
        # Filter based on the slide's own text (before title prepend),
        # so slides with only a page-number title don't sneak through
        slide_word_count = len(slide["text"].split())
        if slide_word_count < MIN_CHUNK_WORDS:
            filtered.append(slide)
            continue

        text = build_chunk_text(slide["title"], slide["text"], INCLUDE_SLIDE_TITLE)
        word_count = len(text.split())

        # Sub-split if text exceeds SBERT-safe limit
        segments = split_long_text(text, MAX_CHUNK_WORDS, OVERLAP_WORDS)

        for i, segment in enumerate(segments):
            part = (i + 1) if len(segments) > 1 else None
            chunk = {
                "chunk_id": build_chunk_id(
                    slide["course"], slide["lecture"], slide["slide_number"], part
                ),
                "course": slide["course"],
                "lecture": slide["lecture"],
                "slide_number": slide["slide_number"],
                "title": slide["title"],
                "text": segment,
                "word_count": len(segment.split()),
                "has_image": slide.get("has_image", False),
            }
            kept.append(chunk)

    return kept, filtered


def save_chunks(chunks: list[dict], output_path: Path) -> None:
    """Write chunks to JSONL (one JSON object per line)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def load_chunks(path: Path) -> list[dict]:
    """Read chunks from a JSONL file."""
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


if __name__ == "__main__":
    print("Extracting slides from PDFs...")
    slides = extract_all_pdfs(RAW_PDFS_DIR)

    print("Building chunks...")
    chunks, filtered = build_chunks(slides)

    save_chunks(chunks, CHUNKS_FILE)
    print(f"Saved {len(chunks)} chunks to {CHUNKS_FILE}")

    # Summary
    word_counts = [c["word_count"] for c in chunks]
    sub_split = sum(1 for c in chunks if "_part" in c["chunk_id"])
    print(f"\n--- Summary ---")
    print(f"Total slides: {len(slides)}")
    print(f"Chunks created: {len(chunks)}")
    print(f"Slides filtered (< {MIN_CHUNK_WORDS} words): {len(filtered)}")
    print(f"Sub-split chunks (> {MAX_CHUNK_WORDS} words): {sub_split}")
    if word_counts:
        avg = sum(word_counts) / len(word_counts)
        print(f"Word counts — min: {min(word_counts)}, max: {max(word_counts)}, avg: {avg:.1f}")

    if filtered:
        print(f"\nFiltered slides:")
        for s in filtered:
            wc = len(s["text"].split())
            print(f"  {s['course']}_lect{s['lecture']}_slide{s['slide_number']}: "
                  f"{wc} words — \"{s['title'][:50]}\"")
