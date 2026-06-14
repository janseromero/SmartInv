'use client';

import { getToken } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';

/**
 * Client-side route guard (CV1.E6).
 *
 * Redirects to /login when no token is present. This is the dev-grade gate;
 * the real IdP swap replaces it with an Auth.js session check (ADR-021).
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (getToken()) {
      setAuthorized(true);
    } else {
      router.replace('/login');
    }
  }, [router]);

  if (!authorized) {
    return null;
  }
  return <>{children}</>;
}
