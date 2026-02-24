"""
Tax calculation and amount-to-words (Indian numbering: Lakhs, Crores).
"""
from decimal import Decimal, ROUND_HALF_UP

# SAI PAINTS: Same state → CGST 9% + SGST 9%; Inter-state → IGST 18%
CGST_RATE = Decimal('9')
SGST_RATE = Decimal('9')
IGST_RATE = Decimal('18')

# Shop state code (A.P. = 37) — same state means CGST+SGST
SHOP_STATE_CODE = '37'


def get_tax_breakdown(total_before_tax: Decimal, customer_state_code: str) -> dict:
    """
    Returns dict with keys: total_before_tax, cgst_rate, sgst_rate, igst_rate,
    cgst_amount, sgst_amount, igst_amount, total_amount, is_inter_state.
    """
    total_before_tax = Decimal(total_before_tax).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    customer_state_code = (customer_state_code or '').strip() or None
    is_inter_state = customer_state_code != SHOP_STATE_CODE

    if is_inter_state:
        igst_amount = (total_before_tax * IGST_RATE / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {
            'total_before_tax': total_before_tax,
            'cgst_rate': Decimal('0'),
            'sgst_rate': Decimal('0'),
            'igst_rate': IGST_RATE,
            'cgst_amount': Decimal('0'),
            'sgst_amount': Decimal('0'),
            'igst_amount': igst_amount,
            'total_amount': total_before_tax + igst_amount,
            'is_inter_state': True,
        }
    else:
        cgst_amount = (total_before_tax * CGST_RATE / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        sgst_amount = (total_before_tax * SGST_RATE / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {
            'total_before_tax': total_before_tax,
            'cgst_rate': CGST_RATE,
            'sgst_rate': SGST_RATE,
            'igst_rate': Decimal('0'),
            'cgst_amount': cgst_amount,
            'sgst_amount': sgst_amount,
            'igst_amount': Decimal('0'),
            'total_amount': total_before_tax + cgst_amount + sgst_amount,
            'is_inter_state': False,
        }


# Indian number names for amount in words
_ONES = (
    '', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen'
)
_TENS = ('', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')


def _group_to_words(n: int) -> str:
    """Convert 0-999 to words."""
    if n == 0:
        return ''
    if n < 20:
        return _ONES[n].strip()
    if n < 100:
        return f"{_TENS[n // 10]} {_ONES[n % 10]}".strip()
    return f"{_ONES[n // 100]} Hundred {_group_to_words(n % 100)}".strip()


def amount_to_words_indian(amount: Decimal) -> str:
    """
    Convert amount to words in Indian numbering (Lakhs, Crores).
    Example: 1234567.89 → "Twelve Lakh Thirty Four Thousand Five Hundred Sixty Seven and Eighty Nine Paise Only"
    """
    try:
        amount = Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except Exception:
        return "Zero Only"

    if amount < 0:
        return "Minus " + amount_to_words_indian(-amount)
    if amount == 0:
        return "Zero Only"

    whole = int(amount)
    paise = int((amount - whole) * 100)

    if whole == 0:
        if paise == 0:
            return "Zero Only"
        return f"{_group_to_words(paise)} Paise Only"

    parts = []
    # Crores (10^7)
    if whole >= 10_00_00_000:
        parts.append(_group_to_words(whole // 10_00_00_000) + " Crore")
        whole %= 10_00_00_000
    if whole >= 1_00_000:
        parts.append(_group_to_words(whole // 1_00_000) + " Lakh")
        whole %= 1_00_000
    if whole >= 1000:
        parts.append(_group_to_words(whole // 1000) + " Thousand")
        whole %= 1000
    if whole > 0:
        parts.append(_group_to_words(whole))

    result = " ".join(parts).strip()
    if result:
        result += " Rupees"
    if paise > 0:
        result += f" and {_group_to_words(paise)} Paise"
    result += " Only"
    return result
