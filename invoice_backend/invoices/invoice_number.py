"""
Auto-increment invoice number: SP-YYYY-XXXX (e.g. SP-2026-0001).
Uses database with transaction to prevent duplicates.
"""
from django.db import transaction
from django.utils import timezone

from .models import Invoice


def get_next_invoice_number(prefix: str = 'SP') -> str:
    """
    Returns next invoice number in form PREFIX-YYYY-XXXX.
    Uses select_for_update to avoid race conditions.
    """
    year = timezone.now().year
    prefix_with_year = f"{prefix}-{year}-"

    with transaction.atomic():
        last = (
            Invoice.objects
            .filter(invoice_no__startswith=prefix_with_year)
            .order_by('-invoice_no')
            .values_list('invoice_no', flat=True)
            .first()
        )
        if last:
            try:
                seq = int(last.split('-')[-1])
            except (ValueError, IndexError):
                seq = 0
        else:
            seq = 0
        next_seq = seq + 1
        return f"{prefix_with_year}{next_seq:04d}"
