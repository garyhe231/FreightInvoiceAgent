import os
from typing import Optional

from fpdf import FPDF

from app.models.invoice import Invoice
from app.models.invoice_line import InvoiceLine
from app.models.client import Client
from app.models.shipment import Shipment
from app.models.port import Port
from app.config import settings


# Directory where generated PDFs are stored
PDF_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
    "pdfs",
)


class FreightInvoicePDF(FPDF):
    """Custom FPDF subclass for freight invoice rendering."""

    def header(self):
        # Company name
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, settings.COMPANY_NAME, ln=True, align="L")

        # Company address / contact
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, settings.COMPANY_ADDRESS, ln=True, align="L")
        self.cell(
            0, 5,
            f"Phone: {settings.COMPANY_PHONE}  |  Email: {settings.COMPANY_EMAIL}",
            ln=True, align="L",
        )
        self.ln(4)
        # Separator line
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-30)
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 4, "Payment Instructions:", ln=True, align="L")
        self.cell(
            0, 4,
            (
                f"Wire Transfer to: {settings.COMPANY_NAME}, "
                "Bank of America, Account: XXXX-XXXX-1234, Routing: 026009593"
            ),
            ln=True, align="L",
        )
        self.cell(
            0, 4,
            f"Page {self.page_no()}/{{nb}}",
            align="C",
        )


def generate_pdf(
    invoice: Invoice,
    lines: list[InvoiceLine],
    client: Client,
    shipment: Shipment,
    origin_port: Port,
    dest_port: Port,
) -> str:
    """Generate a professional invoice PDF and save it to the static/pdfs directory.

    Returns the file path of the generated PDF.
    """
    # Ensure output directory exists
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

    pdf = FreightInvoicePDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ---- INVOICE title and meta ----
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, "INVOICE", ln=True, align="R")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Invoice Number: {invoice.invoice_number}", ln=True, align="R")
    pdf.cell(0, 6, f"Issue Date: {invoice.issue_date}", ln=True, align="R")
    pdf.cell(0, 6, f"Due Date: {invoice.due_date}", ln=True, align="R")
    pdf.ln(6)

    # ---- Bill To ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Bill To:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, client.company_name, ln=True)
    if client.contact_name:
        pdf.cell(0, 6, f"Attn: {client.contact_name}", ln=True)
    if client.address:
        pdf.cell(0, 6, client.address, ln=True)
    city_country = ", ".join(
        part for part in [client.city, client.country] if part
    )
    if city_country:
        pdf.cell(0, 6, city_country, ln=True)
    pdf.cell(0, 6, f"Email: {client.email}", ln=True)
    pdf.ln(6)

    # ---- Shipment Reference ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Shipment Reference:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Booking Number: {shipment.booking_number}", ln=True)
    if shipment.bl_number:
        pdf.cell(0, 6, f"BL Number: {shipment.bl_number}", ln=True)

    route_str = (
        f"{origin_port.port_name} ({origin_port.port_code}) "
        f"-> {dest_port.port_name} ({dest_port.port_code})"
    )
    pdf.cell(0, 6, f"Route: {route_str}", ln=True)

    vessel_info = shipment.vessel_name or "N/A"
    if shipment.voyage_number:
        vessel_info += f" / {shipment.voyage_number}"
    pdf.cell(0, 6, f"Vessel / Voyage: {vessel_info}", ln=True)
    pdf.cell(0, 6, f"Container Type: {shipment.container_type}", ln=True)
    pdf.ln(8)

    # ---- Line Items Table ----
    pdf.set_font("Helvetica", "B", 10)
    # Column widths
    col_desc = 90
    col_qty = 25
    col_unit = 35
    col_total = 40

    # Table header
    pdf.set_fill_color(45, 65, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_desc, 8, "Description", border=1, fill=True, align="L")
    pdf.cell(col_qty, 8, "Qty", border=1, fill=True, align="C")
    pdf.cell(col_unit, 8, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(col_total, 8, "Total", border=1, fill=True, align="R")
    pdf.ln()

    # Table rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)

    for line in lines:
        desc = line.description if hasattr(line, "description") else str(line)
        qty = line.quantity if hasattr(line, "quantity") else 1
        unit_price = line.unit_price if hasattr(line, "unit_price") else 0
        line_total = line.line_total if hasattr(line, "line_total") else 0

        pdf.cell(col_desc, 7, desc, border=1, align="L")
        pdf.cell(col_qty, 7, f"{qty:g}", border=1, align="C")
        pdf.cell(col_unit, 7, f"${unit_price:,.2f}", border=1, align="R")
        pdf.cell(col_total, 7, f"${line_total:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(4)

    # ---- Totals ----
    totals_x = col_desc + col_qty + 10  # Starting x for labels
    label_w = 35
    value_w = 40

    def _total_row(label: str, value: float, bold: bool = False) -> None:
        pdf.set_x(totals_x)
        if bold:
            pdf.set_font("Helvetica", "B", 10)
        else:
            pdf.set_font("Helvetica", "", 10)
        pdf.cell(label_w, 7, label, align="R")
        pdf.cell(value_w, 7, f"${value:,.2f}", align="R")
        pdf.ln()

    _total_row("Subtotal:", invoice.subtotal)
    _total_row("Tax:", invoice.tax_amount or 0)
    _total_row("Total:", invoice.total_amount, bold=True)
    _total_row("Amount Paid:", invoice.amount_paid or 0)
    _total_row("Balance Due:", invoice.balance_due, bold=True)

    # ---- Save PDF ----
    filename = f"{invoice.invoice_number}.pdf"
    file_path = os.path.join(PDF_OUTPUT_DIR, filename)
    pdf.output(file_path)

    return file_path
