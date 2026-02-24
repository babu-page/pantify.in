"""
API endpoints for invoice generation and download.
"""
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Invoice
from .serializers import OrderCreateSerializer
from .services import InvoiceGenerationService, InvoiceGenerationError


@api_view(['POST', 'GET'])
def generate_invoice(request, order_id):
    """
    Generate invoice for order_id.
    POST: Generate (optionally ?email=1 to email invoice).
    GET: If invoice exists, return metadata and download link; else 404.
    Prevents duplicate: returns existing invoice if already generated.
    """
    if request.method == 'GET':
        invoice = Invoice.objects.filter(order_id=order_id).select_related('order').first()
        if not invoice:
            raise Http404("Invoice not found for this order.")
        return Response({
            'invoice_no': invoice.invoice_no,
            'invoice_date': str(invoice.invoice_date),
            'order_id': order_id,
            'pdf_url': request.build_absolute_uri(invoice.pdf_file.url) if invoice.pdf_file else None,
        })

    # POST
    email_invoice = request.query_params.get('email', '').lower() in ('1', 'true', 'yes')
    try:
        invoice = InvoiceGenerationService.generate_for_order(
            order_id=int(order_id),
            email_invoice=email_invoice,
        )
    except InvoiceGenerationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({'error': 'Invalid order_id'}, status=status.HTTP_400_BAD_REQUEST)

    pdf_url = request.build_absolute_uri(invoice.pdf_file.url) if invoice.pdf_file else None
    return Response({
        'invoice_no': invoice.invoice_no,
        'invoice_date': str(invoice.invoice_date),
        'order_id': order_id,
        'pdf_url': pdf_url,
        'message': 'Invoice generated successfully.',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def create_order(request):
    """
    Create order with customer and line items.
    Returns order_id for use with generate-invoice and download endpoints.
    """
    serializer = OrderCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    order = serializer.save()
    return Response({'order_id': order.id}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def download_invoice_pdf(request, order_id):
    """Download PDF for order. Admin or anyone with link; protect in production with auth."""
    invoice = Invoice.objects.filter(order_id=order_id).first()
    if not invoice or not invoice.pdf_file:
        raise Http404("Invoice or PDF not found.")
    try:
        f = invoice.pdf_file.open('rb')
        return FileResponse(
            f,
            as_attachment=True,
            filename=f"invoice_{invoice.invoice_no}.pdf",
        )
    except (OSError, ValueError):
        raise Http404("File not found.")
