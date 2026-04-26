"""
Resume parser — extracts text from PDF files or accepts plain text.
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text content from a PDF file given as bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()

    full_text = "\n".join(text_parts)
    # Clean up excessive whitespace
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    return "\n".join(lines)


def clean_text(raw_text: str) -> str:
    """Clean and normalise raw text input."""
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    return "\n".join(lines)
