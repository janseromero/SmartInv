/**
 * Dev token storage (CV1.E6).
 *
 * MVP keeps the bearer token in localStorage. When a real IdP lands, this is
 * replaced by the Auth.js session — call sites only use these helpers.
 */

const TOKEN_KEY = 'smartinv.token';

export function getToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}
