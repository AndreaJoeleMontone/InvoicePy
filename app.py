from pathlib import Path

from extractor import extract_text_from_pdf
from invoice_parser import parse_invoice
from excel_exporter import export_to_excel


INPUT_FOLDER = Path("input")
OUTPUT_FILE = Path("output") / "invoices.xlsx"


def main():
    print("=" * 60)
    print("PDF INVOICE READER")
    print("=" * 60)

    pdf_files = list(INPUT_FOLDER.glob("*.pdf"))

    if not pdf_files:
        print()
        print("Nessun PDF trovato nella cartella input.")
        return

    print()
    print(f"PDF trovati: {len(pdf_files)}")
    print()

    invoices = []

    for pdf_file in pdf_files:
        print("-" * 60)
        print(f"Analisi: {pdf_file.name}")

        try:
            text = extract_text_from_pdf(pdf_file)
            invoice = parse_invoice(text, filename=pdf_file.name)
            invoices.append(invoice)

            print(f"  Fornitore:      {invoice['fornitore']}")
            print(f"  Numero fattura: {invoice['numero_fattura']}")
            print(f"  Data emissione: {invoice['data_emissione']}")
            print(f"  Scadenza:       {invoice['scadenza']}")
            print(f"  Importo:        {invoice['importo']} €")
            print()
            print(
                f"  Riconoscimento: {invoice['confidence']}% "
                f"[{invoice['status']}]"
            )

            if invoice["campi_mancanti"]:
                print("  Campi mancanti:")
                for field in invoice["campi_mancanti"]:
                    print(f"    - {field}")

            print()

        except Exception as error:
            print("  ERRORE durante l'elaborazione:")
            print(f"  {error}")
            print()

    if invoices:
        export_to_excel(invoices, OUTPUT_FILE)

        print("=" * 60)
        print("ELABORAZIONE COMPLETATA")
        print("=" * 60)
        print()
        print(f"Fatture elaborate: {len(invoices)}")
        print(f"Excel creato: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
