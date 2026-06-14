import { AuthGuard } from '@/components/auth-guard';
import { Providers } from '@/components/providers';
import { Sidebar } from '@/components/sidebar';
import { Topbar } from '@/components/topbar';
import type { ReactNode } from 'react';

/**
 * Authenticated app shell.
 *
 * Flex layout: full-height sidebar on the left (236px), topbar + main on
 * the right. Matches the layout from the high-fidelity mock
 * (`docs/smartinv-ui.html`).
 */
export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <Providers>
        <div className="h-screen flex bg-surface">
          <div className="w-[236px] flex-none">
            <Sidebar />
          </div>
          <div className="flex-1 flex flex-col min-w-0">
            <Topbar />
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
        </div>
      </Providers>
    </AuthGuard>
  );
}
