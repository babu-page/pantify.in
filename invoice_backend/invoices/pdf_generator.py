"""
Generate GST Tax Invoice PDF matching SAI PAINTS printed layout (reportlab).
"""
import os
from io import BytesIO
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

# A4 in points (reportlab default); Helvetica/Helvetica-Bold are built-in
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 15 * mm
TABLE_HEADER_FONT_SIZE = 8
BODY_FONT_SIZE = 9
TITLE_FONT_SIZE = 14


def build_invoice_pdf(shop, order, invoice_no, invoice_date, amount_in_words: str) -> BytesIO:
    """
    Build PDF buffer for the given order and invoice meta.
    Layout matches: Header (SAI PAINTS, GSTIN, Address, Cell, State, TAX INVOICE, No, Date),
    Customer section, Items table, Totals/tax, Bank details, Footer (Receiver, Authorised Signatory).
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        'InvoiceNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=BODY_FONT_SIZE,
    )
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=TITLE_FONT_SIZE,
        alignment=1,
    )
    small = ParagraphStyle(
        'InvoiceSmall',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
    )

    story = []

    # ----- Header -----
    header_data = [
        [f"GSTIN: {shop.gstin}", "TAX INVOICE", f"Cell: {shop.cell}"],
        ["", "", f"State : {shop.state}"],
        ["", "", f"Code : {shop.state_code}"],
    ]
    header_table = Table(header_data, colWidths=[PAGE_WIDTH / 3 - MARGIN * 2] * 3)
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(shop.name, ParagraphStyle(
        'ShopName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, alignment=1
    )))
    story.append(Paragraph(shop.address, ParagraphStyle(
        'ShopAddress', parent=styles['Normal'], fontName='Helvetica', fontSize=BODY_FONT_SIZE, alignment=1
    )))
    story.append(Spacer(1, 2 * mm))

    # Invoice No & Date row
    inv_row = Table([
        [f"No: {invoice_no}", f"Date: {invoice_date}"],
    ], colWidths=[PAGE_WIDTH / 2 - MARGIN, PAGE_WIDTH / 2 - MARGIN])
    inv_row.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), BODY_FONT_SIZE),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(inv_row)
    story.append(Spacer(1, 6 * mm))

    # ----- Details of Receive (Billed) - Customer -----
    cust = order.customer
    story.append(Paragraph(
        "<b>Details of Receive (Billed)</b>",
        ParagraphStyle('Section', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10),
    ))
    story.append(Spacer(1, 2 * mm))
    customer_data = [
        [f"Sri.: {cust.name}"],
        [f"Address: {cust.address or '............'}"],
        [f"Cell: {cust.phone or '........................'}"],
        [f"GSTIN: {cust.gstin or '........................'}"],
    ]
    cust_table = Table(customer_data, colWidths=[PAGE_WIDTH - 2 * MARGIN])
    cust_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), BODY_FONT_SIZE),
    ]))
    story.append(cust_table)
    story.append(Spacer(1, 6 * mm))

    # ----- Table: S.No, Description, HSN/SAC, Qty, Rate, Amount -----
    table_headers = ['S. No', 'Description of Goods', 'HSN/SAC', 'Qty.', 'Rate', 'Amount']
    row_data = [table_headers]
    for item in order.items.all().order_by('sno'):
        row_data.append([
            str(item.sno),
            item.description,
            item.hsn_sac,
            str(item.quantity),
            str(item.rate),
            str(item.amount),
        ])

    col_widths = [
        10 * mm,
        (PAGE_WIDTH - 2 * MARGIN - 10 * mm - 18 * mm - 18 * mm - 22 * mm - 22 * mm),
        18 * mm,
        18 * mm,
        22 * mm,
        22 * mm,
    ]
    # Recompute if sum doesn't match
    total_w = sum(col_widths)
    if abs(total_w - (PAGE_WIDTH - 2 * MARGIN)) > 2:
        col_widths[1] = (PAGE_WIDTH - 2 * MARGIN) - (total_w - col_widths[1])

    items_table = Table(row_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), TABLE_HEADER_FONT_SIZE),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (5, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (2, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 4 * mm))

    # ----- Below table: Total before tax, CGST, SGST, IGST, Total, Amount in words -----
    total_before = order.total_before_tax
    cgst = order.cgst_amount
    sgst = order.sgst_amount
    igst = order.igst_amount
    total_amt = order.total_amount

    totals_data = [
        ['TOTAL  Total Amount before Tax', str(total_before)],
        ['Add. CGST:', str(cgst)],
        ['Add. SGST:', str(sgst)],
        ['Add. IGST:', str(igst)],
        ['Total Amount', str(total_amt)],
    ]
    tot_col_w = (PAGE_WIDTH - 2 * MARGIN) * 0.75, (PAGE_WIDTH - 2 * MARGIN) * 0.25
    tot_table = Table(totals_data, colWidths=tot_col_w)
    tot_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), BODY_FONT_SIZE),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(tot_table)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        f"<b>Total Invoice Amount in Words:</b> {amount_in_words}",
        ParagraphStyle('Words', parent=styles['Normal'], fontName='Helvetica', fontSize=BODY_FONT_SIZE),
    ))
    story.append(Spacer(1, 8 * mm))

    # ----- Bank Details -----
    story.append(Paragraph(
        f"<b>{shop.bank_name}</b><br/>Bank Account No.: {shop.bank_account_no}<br/>Bank Branch IFSC: {shop.bank_ifsc}<br/>Cell: {shop.cell}",
        ParagraphStyle('Bank', parent=styles['Normal'], fontName='Helvetica', fontSize=BODY_FONT_SIZE),
    ))
    story.append(Spacer(1, 10 * mm))

    # ----- Footer: Receiver Details, Authorised Signatory -----
    footer_data = [
        ['Receivers Details', ''],
        ['Bank Name:', ''],
        ['Cheque No.', ''],
        ['Date', ''],
        ['', ''],
        ['', 'For ' + shop.name],
        ['', 'Authorised Signatory'],
    ]
    footer_table = Table(footer_data, colWidths=[(PAGE_WIDTH - 2 * MARGIN) / 2] * 2)
    footer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), BODY_FONT_SIZE),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(footer_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
