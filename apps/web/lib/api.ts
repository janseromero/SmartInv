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
