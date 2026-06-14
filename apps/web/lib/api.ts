/**
 * Minimal API client (CV1.E6).
 *
 * Attaches the bearer token to requests. The full typed SDK (generated from
 * OpenAPI) arrives with the data screens; this is the smallest thing that
 * proves the authenticated path end-to-end.
 */

import { getToken } from '@/lib/auth';

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export interface Me {
  sub: string;
  tenant_id: string;
  email: string | null;
  roles: string[];
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function devLogin(tenantSlug: string, roles: string[]): Promise<string> {
  const response = await fetch(`${API_URL}/auth/dev-login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tenant_slug: tenantSlug, roles }),
  });
  if (!response.ok) {
    throw new Error(`Dev login failed: ${response.status}`);
  }
  const data = (await response.json()) as { access_token: string };
  return data.access_token;
}

export function fetchMe(): Promise<Me> {
  return apiFetch<Me>('/me');
}

// --- Connectors (CV2.E1) -------------------------------------------------

export interface SyncRun {
  object_type: string;
  status: string;
  records_read: number;
  records_upserted: number;
  records_failed: number;
  finished_at: string | null;
}

export interface Connector {
  id: string;
  source_system: string;
  name: string;
  status: string;
  runs: SyncRun[];
}

export function fetchConnectors(): Promise<Connector[]> {
  return apiFetch<Connector[]>('/admin/connectors');
}

export function triggerFixtureSync(): Promise<Record<string, Record<string, number>>> {
  return apiFetch<Record<string, Record<string, number>>>('/admin/connectors/sync', {
    method: 'POST',
  });
}

// --- Inventory catalog (CV2.E2) ------------------------------------------

export interface ItemRow {
  id: string;
  item_number: string;
  description: string | null;
  uom: string | null;
  item_type: string | null;
  status: string | null;
  unit_cost: number | null;
  on_hand: number;
  inventory_value: number;
  locations: number;
}

export interface ItemsPage {
  items: ItemRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface InventorySummary {
  total_items: number;
  inventory_value: number;
  excess_value: number;
  dead_stock_value: number;
  completeness_pct: number;
}

export interface LocationRow {
  id: string;
  location_code: string;
  name: string | null;
}

export interface BalanceRow {
  location_code: string;
  on_hand: number;
  min_level: number | null;
  max_level: number | null;
  as_of: string | null;
}

export interface TransactionRow {
  type: string;
  quantity: number;
  txn_date: string | null;
  location_code: string | null;
}

export interface ItemDetail {
  id: string;
  item_number: string;
  description: string | null;
  uom: string | null;
  item_type: string | null;
  status: string | null;
  unit_cost: number | null;
  balances: BalanceRow[];
  recent_transactions: TransactionRow[];
}

export interface ItemQuery {
  page?: number;
  page_size?: number;
  search?: string;
  item_type?: string;
  location_id?: string;
  missing_data?: boolean;
  sort?: 'item_number' | 'value' | 'on_hand';
}

function queryString(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}

export function fetchInventorySummary(locationId?: string): Promise<InventorySummary> {
  return apiFetch<InventorySummary>(
    `/inventory/summary${queryString({ location_id: locationId })}`,
  );
}

export function fetchItems(query: ItemQuery): Promise<ItemsPage> {
  return apiFetch<ItemsPage>(`/inventory/items${queryString({ ...query })}`);
}

export function fetchLocations(): Promise<LocationRow[]> {
  return apiFetch<LocationRow[]>('/inventory/locations');
}

export function fetchItemDetail(id: string): Promise<ItemDetail> {
  return apiFetch<ItemDetail>(`/inventory/items/${id}`);
}
