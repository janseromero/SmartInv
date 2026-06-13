import type { ReactNode } from 'react';

interface PageHeadProps {
  crumb: string;
  title: string;
  sub: string;
  actions?: ReactNode;
}

/**
 * Standard page header used by every screen in the app: small uppercase
 * crumb, large display title, body sub-line, optional right-aligned actions.
 */
export function PageHead({ crumb, title, sub, actions }: PageHeadProps) {
  return (
    <div className="flex items-end gap-lg mb-xl flex-wrap">
      <div className="min-w-0">
        <div className="text-xs uppercase tracking-widest font-semibold text-ink-3 mb-1">
          {crumb}
        </div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        <p className="text-ink-2 text-sm mt-1 max-w-[640px]">{sub}</p>
      </div>
      {actions ? <div className="ml-auto flex gap-sm items-center">{actions}</div> : null}
    </div>
  );
}
