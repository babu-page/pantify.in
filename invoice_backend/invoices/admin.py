from django.contrib import admin
from .models import Shop, Customer, Order, OrderItem, Invoice


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'gstin', 'state_code', 'is_default')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'state_code', 'email')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'total_amount', 'is_inter_state')
    inlines = [OrderItemInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_no', 'order', 'invoice_date', 'created_at')
