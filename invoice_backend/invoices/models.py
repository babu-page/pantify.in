"""
Models for GST Invoice system.
MVC: Models hold business entities; services perform operations.
"""
from decimal import Decimal
from django.db import models


class Shop(models.Model):
    """Business/shop details for invoice header and footer (SAI PAINTS)."""
    name = models.CharField(max_length=128)
    gstin = models.CharField(max_length=20)
    address = models.TextField()
    cell = models.CharField(max_length=20)
    state = models.CharField(max_length=64)
    state_code = models.CharField(max_length=4)  # e.g. 37 for A.P.
    invoice_prefix = models.CharField(max_length=10, default='SP')  # SP for SAI PAINTS
    bank_name = models.CharField(max_length=128)
    bank_account_no = models.CharField(max_length=32)
    bank_ifsc = models.CharField(max_length=20)
    is_default = models.BooleanField(default=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name


class Customer(models.Model):
    """Customer/buyer details for billing."""
    name = models.CharField(max_length=256)
    address = models.TextField(blank=True)
    gstin = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)  # For sending invoice by email
    state_code = models.CharField(max_length=4, blank=True)  # 37 = A.P. → CGST+SGST; else IGST

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Order(models.Model):
    """Order placed by customer; one order can have one invoice."""
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    total_before_tax = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    cgst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    sgst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    igst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    is_inter_state = models.BooleanField(default=False)  # True → IGST applied

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name}"


class OrderItem(models.Model):
    """Line item in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    sno = models.PositiveSmallIntegerField()
    description = models.CharField(max_length=256)
    hsn_sac = models.CharField(max_length=20, default='998313')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # quantity * rate

    class Meta:
        ordering = ['order', 'sno']
        unique_together = [('order', 'sno')]

    def __str__(self):
        return f"{self.order_id} - {self.description}"


class Invoice(models.Model):
    """Generated invoice; one per order. Prevents duplicate generation."""
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='invoice')
    invoice_no = models.CharField(max_length=32, unique=True)  # SP-YYYY-XXXX
    invoice_date = models.DateField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='invoices/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_no
