"""PDF extraction — turns lecture PDFs into clean, structured slide text.

Assumption: each PDF page corresponds to exactly one lecture slide.
The module strips recurring headers/footers (course codes, instructor names,
page numbers, etc.) so downstream stages get clean content.

Usage:
    python src/pdf_extraction.py        # extracts all PDFs in data/raw_pdfs/
"""

import re
from pathlib import Path

import pdfplumber

# Allow importing config.py from the project root when running this file directly
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import RAW_PDFS_DIR, EXTRACTED_TEXT_DIR


# ── Regex patterns for stripping recurring slide chrome ─────────────────
# These are compiled once at import time. Each pattern matches a full line
# so we can cleanly sub it out without leaving stray whitespace.

HEADER_PATTERNS = [
    # Course-code headers, e.g. "TDT4310 2026: Lecture 1"
    re.compile(r"^.*TDT\d{4}.*Lecture\s*\d+.*$", re.IGNORECASE | re.MULTILINE),
    # Bare date lines, e.g. "6/1 2026"
    re.compile(r"^\d{1,2}/\d{1,2}\s+\d{4}\s*$", re.MULTILINE),
]

FOOTER_PATTERNS = [
    # Instructor names: "Björn Gambäck, NTNU" or similar
    re.compile(
        r"^.*Bj[öo]rn\s+Gamb[äa]ck.*$", re.IGNORECASE | re.MULTILINE
    ),
    # "Norwegian University of Science and Technology" line
    re.compile(
        r"^.*Norwegian University of Science and Technology.*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    # "Trondheim, Norway" line
    re.compile(r"^.*Trondheim,?\s*Norway.*$", re.IGNORECASE | re.MULTILINE),
]

# Catches a lone page/slide number sitting at the very end of extracted text
TRAILING_NUMBER = re.compile(r"\n\d{1,3}\s*$")


def extract_slides_from_pdf(pdf_path: Path) -> list[dict]:
    """Open a single PDF and return raw text for every page.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of dicts, one per page::

            {"slide_number": int, "text": str, "pdf_page": int}

        The text is *raw* (not yet cleaned) — headers/footers are still present.
    """
    slides = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            has_image = len(page.images) > 0
            slides.append(
                {
                    "slide_number": i + 1,
                    "text": text,
                    "pdf_page": i + 1,
                    "has_image": has_image,
                }
            )
    return slides


def extract_slide_title(text: str) -> str:
    """Return the first non-empty line as the slide title.

    This is a simple heuristic — lecture slides almost always have the title
    as the very first line of text on the page.
    """
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def clean_slide_text(text: str, course: str = "") -> str:
    """Strip headers, footers, page numbers, and excess whitespace.

    Args:
        text:   Raw text extracted from a single slide.
        course: Course code (reserved for future course-specific rules).

    Returns:
        Cleaned text ready for chunking / indexing.
    """
    for pattern in HEADER_PATTERNS:
        text = pattern.sub("", text)

    for pattern in FOOTER_PATTERNS:
        text = pattern.sub("", text)

    # Remove trailing standalone page number (e.g. "\n37" at end)
    text = TRAILING_NUMBER.sub("", text)

    # Remove standalone numbers on their own line anywhere in the text
    text = re.sub(r"^\d{1,3}\s*$", "", text, flags=re.MULTILINE)

    # Collapse runs of blank lines and trim edges
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def extract_all_pdfs(pdf_dir: Path) -> list[dict]:
    """Batch-extract and clean slides from every PDF in *pdf_dir*.

    Metadata (course code, lecture number) is inferred from filenames.
    Expected naming convention::

        tdt4310_2026_lect1.pdf  →  course="tdt4310", lecture=1

    Args:
        pdf_dir: Directory containing the lecture PDFs.

    Returns:
        List of slide dicts, each containing::

            course, lecture, slide_number, pdf_page,
            title, text (cleaned), raw_text (original)
    """
    pdf_files = sorted(pdf_dir.rglob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return []

    all_slides = []

    for pdf_path in pdf_files:
        # Course code from parent folder (e.g. data/raw_pdfs/tdt4310/)
        course = pdf_path.parent.name                  # e.g. "tdt4310"
        name = pdf_path.stem                           # e.g. "tdt4310_2026_lect1"
        lect_match = re.search(r"lec(?:t(?:ure)?)?(\d+)", name, re.IGNORECASE)
        lecture = int(lect_match.group(1)) if lect_match else 0

        raw_slides = extract_slides_from_pdf(pdf_path)

        for slide in raw_slides:
            title = extract_slide_title(slide["text"])
            cleaned = clean_slide_text(slide["text"], course)

            all_slides.append(
                {
                    "course": course,
                    "lecture": lecture,
                    "slide_number": slide["slide_number"],
                    "pdf_page": slide["pdf_page"],
                    "title": title,
                    "text": cleaned,
                    "raw_text": slide["text"],
                    "has_image": slide["has_image"],
                }
            )

    return all_slides


if __name__ == "__main__":
    # ── Run extraction and write one .txt per lecture for manual inspection ──
    EXTRACTED_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    slides = extract_all_pdfs(RAW_PDFS_DIR)

    # Group slides by (course, lecture) so each lecture gets its own file
    lectures: dict[tuple, list[dict]] = {}
    for slide in slides:
        key = (slide["course"], slide["lecture"])
        lectures.setdefault(key, []).append(slide)

    for (course, lecture), lecture_slides in sorted(lectures.items()):
        out_path = EXTRACTED_TEXT_DIR / f"{course}_lect{lecture}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            for s in lecture_slides:
                f.write(f"=== Slide {s['slide_number']} ===\n")
                f.write(f"Title: {s['title']}\n")
                f.write(s["text"])
                f.write("\n\n")
        print(f"Saved {out_path.name} ({len(lecture_slides)} slides)")

    # ── Print a quick summary to the console ──
    word_counts = [len(s["text"].split()) for s in slides]
    total_words = sum(word_counts)
    avg_words = total_words / len(slides) if slides else 0
    print(f"\n--- Summary ---")
    print(f"PDFs processed: {len(lectures)}")
    print(f"Total slides extracted: {len(slides)}")
    print(f"Average words per slide: {avg_words:.1f}")
    if word_counts:
        print(f"Min words: {min(word_counts)}, Max words: {max(word_counts)}")
