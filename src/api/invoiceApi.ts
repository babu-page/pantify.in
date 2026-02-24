/**
 * Invoice backend API client.
 * Base URL: VITE_INVOICE_API_URL or http://127.0.0.1:8000
 */

const API_BASE = import.meta.env.VITE_INVOICE_API_URL || 'http://127.0.0.1:8000';

export interface CustomerPayload {
  name: string;
  address?: string;
  gstin?: string;
  phone?: string;
  email?: string;
  state_code?: string;
}

export interface OrderItemPayload {
  sno: number;
  description: string;
  hsn_sac?: string;
  quantity: number;
  rate: number;
  amount: number;
}

export interface OrderPayload {
  customer: CustomerPayload;
  items: OrderItemPayload[];
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE.replace(/\/$/, '')}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({})) as Record<string, unknown>;
    const msg =
      (typeof errBody?.error === 'string' && errBody.error) ||
      (Array.isArray(errBody?.detail) && errBody.detail.join(' ')) ||
      (typeof errBody?.detail === 'string' && errBody.detail) ||
      (typeof errBody === 'object' &&
        Object.entries(errBody)
          .filter(([, v]) => Array.isArray(v) || typeof v === 'string')
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('; ')) ||
      `API error: ${res.status}`;
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export async function createOrder(payload: OrderPayload): Promise<{ order_id: number }> {
  return request<{ order_id: number }>('/api/orders/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function generateInvoice(orderId: number): Promise<{
  invoice_no: string;
  invoice_date: string;
  order_id: number;
  pdf_url: string;
}> {
  return request(`/api/generate-invoice/${orderId}/`, { method: 'POST' });
}

export function getInvoicePdfUrl(orderId: number): string {
  return `${API_BASE.replace(/\/$/, '')}/api/invoice/${orderId}/pdf/`;
}

/** Download invoice PDF to user's device. */
export async function downloadInvoicePdf(orderId: number, invoiceNo: string): Promise<void> {
  const url = getInvoicePdfUrl(orderId);
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch PDF');
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = `invoice_${invoiceNo.replace(/-/g, '_')}.pdf`;
  a.click();
  URL.revokeObjectURL(blobUrl);
}
