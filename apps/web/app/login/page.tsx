'use client';

import { devLogin } from '@/lib/api';
import { setToken } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { type FormEvent, useState } from 'react';

/**
 * Dev sign-in (CV1.E6 / ADR-021).
 *
 * Mints a token from the API's dev-login endpoint for a chosen tenant + roles.
 * This page is replaced by a real OIDC login when the IdP is wired.
 */
export default function LoginPage() {
  const router = useRouter();
  const [tenant, setTenant] = useState('smartinv-dev');
  const [roles, setRoles] = useState('admin,planner');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const parsed = roles
        .split(',')
        .map((role) => role.trim())
        .filter(Boolean);
      const token = await devLogin(tenant.trim(), parsed);
      setToken(token);
      router.replace('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen grid place-items-center bg-surface text-ink p-lg">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm bg-chrome border border-chrome-line rounded-lg p-lg flex flex-col gap-md"
      >
        <div>
          <h1 className="font-display text-lg text-chrome-strong">SmartInv</h1>
          <p className="text-sm text-chrome-cmd">Developer sign-in</p>
        </div>

        <label className="flex flex-col gap-1 text-sm text-chrome-ink">
          Tenant slug
          <input
            value={tenant}
            onChange={(event) => setTenant(event.target.value)}
            className="bg-chrome-2 border border-chrome-line rounded-md px-md py-1.5 text-chrome-strong"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm text-chrome-ink">
          Roles (comma-separated)
          <input
            value={roles}
            onChange={(event) => setRoles(event.target.value)}
            className="bg-chrome-2 border border-chrome-line rounded-md px-md py-1.5 text-chrome-strong"
          />
        </label>

        {error ? <p className="text-sm text-crit">{error}</p> : null}

        <button
          type="submit"
          disabled={busy}
          className="bg-teal text-surface rounded-md px-md py-2 text-sm font-medium hover:bg-teal-bright disabled:opacity-60"
        >
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </main>
  );
}
