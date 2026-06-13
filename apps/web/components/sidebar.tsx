'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ICONS, LogoMarkIcon } from './icons';
import { ROUTE_GROUPS } from './nav-config';

/**
 * Persistent left sidebar. Lifted from the high-fidelity mock and re-rendered
 * with token-backed Tailwind classes.
 */
export function Sidebar() {
  const pathname = usePathname() ?? '/';

  return (
    <aside className="flex flex-col overflow-y-auto bg-chrome border-r border-chrome-line text-chrome-ink">
      {/* Logo mark */}
      <div className="flex items-center gap-md px-lg py-md border-b border-chrome-line">
        <div className="w-[30px] h-[30px] rounded-md bg-teal grid place-items-center flex-none text-white">
          <LogoMarkIcon className="w-4 h-4" />
        </div>
        <div className="font-display font-bold text-base text-white tracking-wide">
          Smart<span className="text-teal-bright">Inv</span>
        </div>
      </div>

      {ROUTE_GROUPS.map((group) => (
        <nav key={group.label} className="px-sm pt-md pb-1">
          <div className="text-xs font-semibold tracking-widest uppercase text-chrome-muted px-md pb-sm">
            {group.label}
          </div>
          {group.routes.map((route) => {
            const Icon = ICONS[route.icon];
            const isActive = pathname === route.href;
            return (
              <Link
                key={route.href}
                href={route.href}
                aria-current={isActive ? 'page' : undefined}
                className={[
                  'flex items-center gap-md w-full px-md py-1.5 rounded-md text-sm font-medium mb-px',
                  isActive
                    ? 'bg-teal/[0.16] text-teal-bright'
                    : 'text-chrome-ink hover:bg-chrome-2 hover:text-chrome-hover',
                ].join(' ')}
              >
                <Icon
                  className={['w-4 h-4 flex-none', isActive ? 'opacity-100' : 'opacity-80'].join(
                    ' ',
                  )}
                />
                <span className="truncate">{route.label}</span>
                {route.pill ? (
                  <span
                    className={[
                      'ml-auto text-[10px] font-semibold rounded-full px-1.5 leading-4 text-white',
                      route.pill.tone === 'ai' ? 'bg-ai' : 'bg-crit',
                    ].join(' ')}
                  >
                    {route.pill.value}
                  </span>
                ) : null}
              </Link>
            );
          })}
        </nav>
      ))}

      {/* User footer */}
      <div className="mt-auto px-lg py-md border-t border-chrome-line flex items-center gap-md">
        <div className="w-[30px] h-[30px] rounded-pill bg-chrome-2 grid place-items-center text-xs font-semibold text-chrome-strong flex-none">
          RM
        </div>
        <div className="text-xs leading-tight">
          <span className="block font-semibold text-chrome-strong">R. Marques</span>
          <span className="text-chrome-ink">Inventory Planner · BR-South</span>
        </div>
      </div>
    </aside>
  );
}
