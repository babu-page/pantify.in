"""
Invoice generation service: fetch order, compute tax, generate PDF, store record.
Uses transaction atomicity and prevents duplicate invoice generation.
"""
import os
from decimal import Decimal

from django.db import transaction
from django.core.files.base import ContentFile

from .models import Shop, Order, Invoice
from .utils import get_tax_breakdown, amount_to_words_indian
from .invoice_number import get_next_invoice_number
from .pdf_generator import build_invoice_pdf


class InvoiceGenerationError(Exception):
    """Raised when invoice cannot be generated (e.g. order not found, no items)."""
    pass


class InvoiceGenerationService:
    """Service layer for generating and storing GST invoices."""

    @staticmethod
    def get_shop():
        """Return default shop (SAI PAINTS)."""
        shop = Shop.objects.filter(is_default=True).first()
        if not shop:
            shop = Shop.objects.first()
        if not shop:
            raise InvoiceGenerationError("No shop configured. Add a Shop in admin.")
        return shop

    @staticmethod
    def compute_order_totals(order: Order) -> None:
        """Recalculate order subtotal and tax from items; save to order."""
        items = order.items.all().order_by('sno')
        if not items.exists():
            raise InvoiceGenerationError("Order has no items.")
        total_before_tax = sum((item.amount for item in items), Decimal('0'))
        breakdown = get_tax_breakdown(total_before_tax, order.customer.state_code or '')
        order.total_before_tax = breakdown['total_before_tax']
        order.cgst_amount = breakdown['cgst_amount']
        order.sgst_amount = breakdown['sgst_amount']
        order.igst_amount = breakdown['igst_amount']
        order.total_amount = breakdown['total_amount']
        order.is_inter_state = breakdown['is_inter_state']
        order.save(update_fields=[
            'total_before_tax', 'cgst_amount', 'sgst_amount', 'igst_amount',
            'total_amount', 'is_inter_state',
        ])

    @classmethod
    def generate_for_order(cls, order_id: int, email_invoice: bool = False) -> Invoice:
        """
        Generate invoice for order_id. Idempotent: if invoice already exists, returns it.
        Uses transaction to prevent duplicate invoice numbers.
        """
        with transaction.atomic():
            order = Order.objects.select_related('customer').filter(pk=order_id).first()
            if not order:
                raise InvoiceGenerationError("Order not found.")
            existing = getattr(order, 'invoice', None)
            if existing:
                return existing

            shop = cls.get_shop()
            cls.compute_order_totals(order)

            invoice_no = get_next_invoice_number(prefix=shop.invoice_prefix)
            from django.utils import timezone
            invoice_date = timezone.now().date()

            pdf_buffer = build_invoice_pdf(
                shop=shop,
                order=order,
                invoice_no=invoice_no,
                invoice_date=str(invoice_date),
                amount_in_words=amount_to_words_indian(order.total_amount),
            )

            invoice = Invoice.objects.create(
                order=order,
                invoice_no=invoice_no,
                invoice_date=invoice_date,
            )
            filename = f"invoice_{invoice_no.replace('-', '_')}.pdf"
            invoice.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)

        if email_invoice:
            cls._send_invoice_email(invoice)
        return invoice

    @staticmethod
    def _send_invoice_email(invoice: Invoice) -> None:
        """Send invoice PDF by email if Django email is configured and customer has email."""
        from django.core.mail import EmailMessage
        from django.conf import settings
        to_email = (getattr(invoice.order.customer, 'email', None) or '').strip()
        if not to_email:
            return
        if not invoice.pdf_file:
            return
        try:
            path = invoice.pdf_file.path
        except Exception:
            return
        if not os.path.isfile(path):
            return
        subject = f"Tax Invoice {invoice.invoice_no} - SAI PAINTS"
        body = f"Please find attached your tax invoice {invoice.invoice_no}."
        with open(path, 'rb') as f:
            pdf_data = f.read()
        email_msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            attachments=[(os.path.basename(path), pdf_data, 'application/pdf')],
        )
        try:
            email_msg.send(fail_silently=True)
        except Exception:
            pass
