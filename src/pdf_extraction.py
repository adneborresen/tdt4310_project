"""PDF extraction module — extracts text from lecture PDFs (1 page = 1 slide)."""

import re
from pathlib import Path

import pdfplumber

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import RAW_PDFS_DIR, EXTRACTED_TEXT_DIR


# Patterns to strip from slide text
HEADER_PATTERNS = [
    # "TDT4310 2026: Lecture 1" style headers
    re.compile(r"^.*TDT\d{4}.*Lecture\s*\d+.*$", re.IGNORECASE | re.MULTILINE),
    # Date patterns like "6/1 2026" or "January 2026"
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

# Standalone page/slide number at end of text
TRAILING_NUMBER = re.compile(r"\n\d{1,3}\s*$")


def extract_slides_from_pdf(pdf_path: Path) -> list[dict]:
    """Extract one slide per page from a PDF.

    Returns a list of dicts with keys: slide_number, text, pdf_page.
    """
    slides = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            slides.append(
                {
                    "slide_number": i + 1,
                    "text": text,
                    "pdf_page": i + 1,
                }
            )
    return slides


def extract_slide_title(text: str) -> str:
    """Return the first non-empty line of the slide text as the title."""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def clean_slide_text(text: str, course: str = "") -> str:
    """Clean extracted slide text by removing headers, footers, and noise."""
    # Remove header patterns
    for pattern in HEADER_PATTERNS:
        text = pattern.sub("", text)

    # Remove footer patterns
    for pattern in FOOTER_PATTERNS:
        text = pattern.sub("", text)

    # Remove trailing standalone page number (e.g. "\n37" at end)
    text = TRAILING_NUMBER.sub("", text)

    # Also remove a standalone number on its own line anywhere
    text = re.sub(r"^\d{1,3}\s*$", "", text, flags=re.MULTILINE)

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_all_pdfs(pdf_dir: Path) -> list[dict]:
    """Extract slides from all PDFs in a directory.

    Infers course and lecture number from filenames like:
        tdt4310_2026_lect1.pdf  ->  course="tdt4310", lecture=1

    Returns a list of slide dicts with full metadata.
    """
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return []

    all_slides = []

    for pdf_path in pdf_files:
        # Infer course and lecture number from filename
        name = pdf_path.stem  # e.g. "tdt4310_2026_lect1"
        course = name.split("_")[0]  # e.g. "tdt4310"

        # Extract lecture number
        lect_match = re.search(r"lect(\d+)", name, re.IGNORECASE)
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
                }
            )

    return all_slides


if __name__ == "__main__":
    EXTRACTED_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    slides = extract_all_pdfs(RAW_PDFS_DIR)

    # Group by lecture and save extracted text files
    lectures = {}
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

    # Summary
    word_counts = [len(s["text"].split()) for s in slides]
    total_words = sum(word_counts)
    avg_words = total_words / len(slides) if slides else 0
    print(f"\n--- Summary ---")
    print(f"PDFs processed: {len(lectures)}")
    print(f"Total slides extracted: {len(slides)}")
    print(f"Average words per slide: {avg_words:.1f}")
    print(f"Min words: {min(word_counts)}, Max words: {max(word_counts)}")
