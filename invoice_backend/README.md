# GST Tax Invoice Backend (SAI PAINTS)

Django backend for automatic GST tax invoice generation: PDF generation (reportlab), tax calculation (CGST+SGST or IGST), Indian amount-in-words, and optional email.

## Features

- **Invoice layout** matching SAI PAINTS: header (GSTIN, address, cell, state), customer details, items table (S.No, Description, HSN/SAC, Qty, Rate, Amount), totals, CGST/SGST/IGST, amount in words, bank details, footer (Receiver details, Authorised Signatory).
- **Tax rules**: Customer state code = 37 (A.P.) → CGST 9% + SGST 9%; else → IGST 18%.
- **Invoice number**: Auto-increment format `SP-YYYY-XXXX` (e.g. SP-2026-0001).
- **PDF**: Generated with reportlab, stored in `media/invoices/`.
- **Duplicate prevention**: One invoice per order; idempotent generate endpoint.
- **Email**: Optional send after generation when `?email=1` and customer has email.

## Setup

### 1. Install dependencies

```bash
cd invoice_backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
# For MySQL (production):
pip install -r requirements.txt
# For SQLite only (no MySQL client needed):
pip install -r requirements-sqlite.txt
```

### 2. Database (MySQL or SQLite)

**MySQL (production):**

Create database and set env:

```bash
export MYSQL_DB=paintify_invoice
export MYSQL_USER=root
export MYSQL_PASSWORD=yourpassword
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
```

**SQLite (quick local test):**

```bash
export USE_SQLITE=1
```

### 3. Migrate and run

```bash
python manage.py migrate
python manage.py runserver
```

Default **SAI PAINTS** shop is created automatically if none exists (migration `0002_default_shop`).

### 4. Create test data (optional)

- Open **http://127.0.0.1:8000/admin/** → create superuser: `python manage.py createsuperuser`
- Add a **Customer** (name, address, state_code e.g. `37` for A.P.).
- Add an **Order** linked to that customer, then add **Order Items** (description, HSN/SAC, quantity, rate; amount can be computed or set).

## API

- **Generate invoice (POST)**  
  `POST /api/generate-invoice/<order_id>/`  
  Optional query: `?email=1` to email invoice to customer email if set.  
  Returns: `invoice_no`, `invoice_date`, `order_id`, `pdf_url`.  
  If invoice already exists, returns existing (no duplicate).

- **Get invoice info (GET)**  
  `GET /api/generate-invoice/<order_id>/`  
  Returns metadata and `pdf_url` if invoice exists; else 404.

- **Download PDF**  
  `GET /api/invoice/<order_id>/pdf/`  
  Returns PDF file attachment.

## Email (optional)

To send invoice by email after generation:

1. Set in env: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
2. Set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`.
3. Call generate with `?email=1` and ensure **Customer** has `email` set.

## Project structure (MVC-style)

- **Models** (`invoices/models.py`): Shop, Customer, Order, OrderItem, Invoice.
- **Utils** (`invoices/utils.py`): Tax calculation, amount to words (Indian).
- **Invoice number** (`invoices/invoice_number.py`): SP-YYYY-XXXX with transaction-safe increment.
- **PDF** (`invoices/pdf_generator.py`): reportlab layout matching printed invoice.
- **Service** (`invoices/services.py`): `InvoiceGenerationService.generate_for_order()` — atomic, no duplicate.
- **Views** (`invoices/views.py`): REST endpoints for generate and download.

## Integrate with your frontend

From your React app (e.g. after “place order”):

1. Create order via your API (or Django admin).
2. Call `POST /api/generate-invoice/<order_id>/` to generate and get `pdf_url`.
3. Use `GET /api/invoice/<order_id>/pdf/` to download PDF or open in new tab.
