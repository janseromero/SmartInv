'use client';

import { type Me, fetchMe } from '@/lib/api';
import { clearToken } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

/**
 * Topbar identity chip + logout (CV1.E6). Reads /me to show the active tenant
 * and role, and clears the token on logout.
 */
export function SessionChip() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    fetchMe()
      .then(setMe)
      .catch(() => setMe(null));
  }, []);

  function logout(): void {
    clearToken();
    router.replace('/login');
  }

  const label = me ? `TENANT · ${me.tenant_id.slice(0, 8)}` : 'TENANT · …';
  const role = me?.roles[0]?.toUpperCase() ?? '';

  return (
    <div className="flex items-center gap-1.5">
      <span className="font-mono text-[10px] text-teal-bright border border-teal/[0.4] rounded px-2 py-0.5 tracking-wide">
        {label}
        {role ? ` · ${role}` : ''}
      </span>
      <button
        type="button"
        onClick={logout}
        className="font-mono text-[10px] text-chrome-ink border border-chrome-line rounded px-2 py-0.5 tracking-wide hover:bg-chrome-2 hover:text-chrome-strong"
      >
        LOGOUT
      </button>
    </div>
  );
}
