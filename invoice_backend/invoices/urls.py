from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.create_order),
    path('generate-invoice/<int:order_id>/', views.generate_invoice),
    path('invoice/<int:order_id>/pdf/', views.download_invoice_pdf),
]
