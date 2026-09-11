from pathlib import Path
import pymupdf


def extract_text_from_pdf(pdf_path):
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    text = ""

    with pymupdf.open(pdf_path) as document:
        for page in document:
            text += page.get_text()
            text += "\n"

    return text
