import re
from pathlib import Path
from datetime import datetime


def normalize_lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def normalize_date(value):
    if not value:
        return None

    formats = [
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d.%m.%y",
        "%d-%m-%y",
    ]

    for fmt in formats:
        try:
            date = datetime.strptime(value.strip(), fmt)
            return date.strftime("%d/%m/%Y")
        except ValueError:
            pass

    return None


def clean_amount(value):
    if not value:
        return None

    value = value.replace("€", "").strip()
    value = value.replace(".", "")
    value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None


def find_after_label(lines, labels, max_lines=5):
    if isinstance(labels, str):
        labels = [labels]

    for index, line in enumerate(lines):
        for label in labels:
            if label.lower() in line.lower():
                for next_line in lines[index + 1:index + 1 + max_lines]:
                    value = next_line.strip()
                    if value:
                        return value

    return None


def extract_supplier(text, lines):
    supplier = find_after_label(lines, ["Società emittente:", "Società emittente"])

    if supplier:
        return supplier

    text_lower = text.lower()

    if "digas.it" in text_lower:
        return "DIGAS S.r.l."

    if "gruppohera.it" in text_lower:
        return "ESTENERGY S.p.A."

    return None


def extract_invoice_number(text, filename):
    patterns = [
        r"Numero fattura elettronica valida ai fini fiscali:\s*([A-Z0-9\-\/]+)",
        r"Numero fattura\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        r"Fattura n[°.]?\s*[:\-]?\s*([A-Z0-9\-\/]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    file_stem = Path(filename).stem

    if file_stem and file_stem.lower() in text.lower():
        return file_stem

    return None


def extract_issue_date(text, invoice_number=None):
    patterns = [
        r"Data emissione:\s*(\d{2}[./-]\d{2}[./-]\d{2,4})",
        r"Data fattura:\s*(\d{2}[./-]\d{2}[./-]\d{2,4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return normalize_date(match.group(1))

    if invoice_number:
        position = text.find(invoice_number)

        if position != -1:
            section = text[position:position + 200]
            match = re.search(r"\b(\d{2}[./-]\d{2}[./-]\d{2,4})\b", section)

            if match:
                return normalize_date(match.group(1))

    return None


def extract_due_date(text, lines, issue_date=None):
    for index, line in enumerate(lines):
        if "entro il" in line.lower():
            for value in lines[index + 1:index + 6]:
                match = re.search(r"\b(\d{2}[./-]\d{2}[./-]\d{2,4})\b", value)
                if match:
                    return normalize_date(match.group(1))

    match = re.search(
        r"Scadenza\s*[:\-]?\s*(\d{2}[./-]\d{2}[./-]\d{2,4})",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return normalize_date(match.group(1))

    all_dates = re.findall(r"\b\d{2}[./-]\d{2}[./-]\d{2,4}\b", text)
    parsed_dates = []

    for value in all_dates:
        normalized = normalize_date(value)
        if not normalized:
            continue

        try:
            parsed_dates.append(datetime.strptime(normalized, "%d/%m/%Y"))
        except ValueError:
            pass

    if issue_date:
        try:
            issue = datetime.strptime(issue_date, "%d/%m/%Y")
            future_dates = [date for date in parsed_dates if date > issue]

            if future_dates:
                return min(future_dates).strftime("%d/%m/%Y")
        except ValueError:
            pass

    return None


def extract_amount(text, lines):
    match = re.search(r"Netto\s+a\s+Pagare\s+([\d\.,]+)", text, flags=re.IGNORECASE)

    if match:
        return clean_amount(match.group(1))

    for index, line in enumerate(lines):
        if "totale da pagare" in line.lower():
            match = re.search(r"([\d\.]+,\d{2})", line)

            if match:
                return clean_amount(match.group(1))

            for value in lines[index + 1:index + 6]:
                match = re.search(r"([\d\.]+,\d{2})\s*€?", value)
                if match:
                    return clean_amount(match.group(1))

    matches = re.findall(r"\bTotale\s+([\d\.]+,\d{2})", text, flags=re.IGNORECASE)

    if matches:
        return clean_amount(matches[-1])

    return None


def calculate_confidence(invoice):
    fields = {
        "fornitore": "Fornitore",
        "numero_fattura": "Numero fattura",
        "data_emissione": "Data emissione",
        "scadenza": "Scadenza",
        "importo": "Importo",
    }

    missing_fields = []

    for key, label in fields.items():
        value = invoice.get(key)
        if value is None or value == "":
            missing_fields.append(label)

    total_fields = len(fields)
    found_fields = total_fields - len(missing_fields)
    confidence = round((found_fields / total_fields) * 100)

    if confidence == 100:
        status = "OK"
    elif confidence >= 60:
        status = "PARZIALE"
    else:
        status = "DA CONTROLLARE"

    return confidence, status, missing_fields


def parse_invoice(text, filename=""):
    lines = normalize_lines(text)

    supplier = extract_supplier(text, lines)
    invoice_number = extract_invoice_number(text, filename)
    issue_date = extract_issue_date(text, invoice_number)
    due_date = extract_due_date(text, lines, issue_date)
    amount = extract_amount(text, lines)

    invoice = {
        "file": filename,
        "fornitore": supplier,
        "numero_fattura": invoice_number,
        "data_emissione": issue_date,
        "scadenza": due_date,
        "importo": amount,
    }

    confidence, status, missing_fields = calculate_confidence(invoice)

    invoice["confidence"] = confidence
    invoice["status"] = status
    invoice["campi_mancanti"] = missing_fields

    return invoice
