import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from extractor import extract_text_from_pdf
from invoice_parser import parse_invoice
from excel_exporter import export_to_excel


st.set_page_config(
    page_title="InvoicePy",
    page_icon="📄",
    layout="wide",
)


st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    .invoice-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .invoice-subtitle {
        font-size: 18px;
        color: #6b7280;
        margin-top: 0;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #e5e7eb;
        padding: 18px;
        border-radius: 12px;
        background-color: white;
    }

    div[data-testid="stDownloadButton"] button {
        width: 100%;
        height: 48px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


def format_euro(value):
    if value is None:
        return "-"

    formatted = (
        f"{value:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"€ {formatted}"


st.markdown(
    '<div class="invoice-title">InvoicePy</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="invoice-subtitle">
        Estrazione automatica dei dati principali dalle fatture PDF.
    </div>
    """,
    unsafe_allow_html=True,
)


uploaded_files = st.file_uploader(
    "Carica una o più fatture PDF",
    type=["pdf"],
    accept_multiple_files=True,
)


if uploaded_files:
    invoices = []

    with st.spinner("Analisi dei documenti..."):
        with tempfile.TemporaryDirectory() as temp_folder:
            temp_folder = Path(temp_folder)

            for uploaded_file in uploaded_files:
                pdf_path = temp_folder / uploaded_file.name

                with open(pdf_path, "wb") as file:
                    file.write(uploaded_file.getbuffer())

                try:
                    text = extract_text_from_pdf(pdf_path)
                    invoice = parse_invoice(text, filename=uploaded_file.name)
                    invoices.append(invoice)

                except Exception as error:
                    invoices.append({
                        "file": uploaded_file.name,
                        "fornitore": None,
                        "numero_fattura": None,
                        "data_emissione": None,
                        "scadenza": None,
                        "importo": None,
                        "confidence": 0,
                        "status": "ERRORE",
                        "campi_mancanti": [str(error)],
                    })

            total_documents = len(invoices)
            recognized_documents = sum(
                1 for invoice in invoices if invoice.get("status") == "OK"
            )
            total_amount = sum(
                invoice.get("importo") or 0 for invoice in invoices
            )
            average_confidence = round(
                sum(invoice.get("confidence", 0) for invoice in invoices)
                / total_documents
            )

            st.markdown(
                '<div class="section-title">Riepilogo</div>',
                unsafe_allow_html=True,
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Documenti", total_documents)

            with col2:
                st.metric(
                    "Riconosciuti",
                    f"{recognized_documents}/{total_documents}",
                )

            with col3:
                st.metric("Importo totale", format_euro(total_amount))

            with col4:
                st.metric("Affidabilità media", f"{average_confidence}%")

            st.markdown(
                '<div class="section-title">Documenti elaborati</div>',
                unsafe_allow_html=True,
            )

            for invoice in invoices:
                with st.container(border=True):
                    col_a, col_b, col_c = st.columns([2.3, 1.5, 1])

                    with col_a:
                        st.markdown(
                            f"### {invoice['fornitore'] or 'Fornitore non riconosciuto'}"
                        )
                        st.write(
                            f"**Numero fattura:** {invoice['numero_fattura'] or '-'}"
                        )
                        st.caption(invoice["file"])

                    with col_b:
                        st.write(
                            f"**Data emissione**  \n{invoice['data_emissione'] or '-'}"
                        )
                        st.write(
                            f"**Scadenza**  \n{invoice['scadenza'] or '-'}"
                        )
                        st.metric("Importo", format_euro(invoice["importo"]))

                    with col_c:
                        confidence = invoice.get("confidence", 0)
                        st.metric("Riconoscimento", f"{confidence}%")

                        status = invoice.get("status", "DA CONTROLLARE")

                        if status == "OK":
                            st.success("OK")
                        elif status == "PARZIALE":
                            st.warning("PARZIALE")
                        else:
                            st.error(status)

                    missing = invoice.get("campi_mancanti", [])

                    if missing:
                        st.warning(
                            "Campi da controllare: " + ", ".join(missing)
                        )

            st.markdown(
                '<div class="section-title">Tabella riepilogativa</div>',
                unsafe_allow_html=True,
            )

            table_data = []

            for invoice in invoices:
                table_data.append({
                    "Fornitore": invoice.get("fornitore"),
                    "Numero fattura": invoice.get("numero_fattura"),
                    "Data emissione": invoice.get("data_emissione"),
                    "Scadenza": invoice.get("scadenza"),
                    "Importo": format_euro(invoice.get("importo")),
                    "Riconoscimento": f"{invoice.get('confidence', 0)}%",
                    "Stato": invoice.get("status"),
                })

            dataframe = pd.DataFrame(table_data)

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )

            excel_path = temp_folder / "invoices.xlsx"
            export_to_excel(invoices, excel_path)

            with open(excel_path, "rb") as file:
                excel_data = file.read()

            st.markdown(
                '<div class="section-title">Esportazione</div>',
                unsafe_allow_html=True,
            )

            col_download, _ = st.columns([1, 3])

            with col_download:
                st.download_button(
                    label="Scarica Excel",
                    data=excel_data,
                    file_name="InvoicePy_export.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                )

else:
    st.info("Carica almeno una fattura PDF per iniziare.")
