# InvoicePy

InvoicePy is a beginner-friendly Python web app that extracts key information from PDF invoices and exports structured data to Excel.

## What it does

- Upload one or more PDF invoices
- Extract supplier, invoice number, issue date, due date and total amount
- Calculate a simple extraction confidence score
- Flag missing fields for manual review
- Show a summary dashboard in Streamlit
- Export results to Excel

## Tech stack

- Python
- PyMuPDF
- Streamlit
- pandas
- openpyxl
- Regular Expressions

## How it works

```text
PDF invoice
    ↓
Text extraction (PyMuPDF)
    ↓
Rule-based parsing / regex
    ↓
Structured Python data
    ↓
Streamlit dashboard
    ↓
Excel export
```

## Installation

Clone the repository:

```bash
git clone https://github.com/AndreaJoeleMontone/InvoicePy.git
cd InvoicePy
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the Streamlit app:

```bash
python -m streamlit run streamlit_app.py
```

Then open `http://localhost:8501` in your browser.

## Extracted fields

InvoicePy currently tries to extract:

- Supplier
- Invoice number
- Issue date
- Due date
- Total amount

The parser uses multiple strategies so it can handle invoices with different layouts.

## Confidence score

The app checks how many expected fields were extracted successfully.

```text
Supplier       ✓
Invoice number ✓
Issue date     ✓
Due date       ✓
Amount         ✓

Confidence: 100%
Status: OK
```

If one or more fields are missing, the invoice is marked as partial or requiring review.

## Project structure

```text
InvoicePy/
├── app.py
├── streamlit_app.py
├── extractor.py
├── invoice_parser.py
├── excel_exporter.py
├── requirements.txt
├── README.md
├── .gitignore
├── input/
└── output/
```

## Privacy

InvoicePy processes files locally when run on your computer. Personal invoices and generated spreadsheet files are excluded from this repository through `.gitignore`.

## Roadmap

Possible future improvements:

- Support more invoice layouts
- Generic supplier detection
- Multiple payment instalments
- Editable extracted fields
- OCR for scanned PDFs
- Additional export formats
- Online deployment

## Disclaimer

InvoicePy is an educational project. Extracted information should always be verified before being used for accounting or financial purposes.
