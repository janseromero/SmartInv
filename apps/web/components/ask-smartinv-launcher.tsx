'use client';

/**
 * Global "Ask SmartInv" launcher in the topbar (CV5.E2.S4).
 *
 * Turns the reserved command-bar slot into an entry point usable from any
 * screen: click (or ⌘K / Ctrl-K) opens a right-side slide-over that hosts the
 * same governed `AnalystChat`. Keeps the analyst one keystroke away without
 * leaving the current page.
 */

import { AnalystChat } from '@/components/analyst-chat';
import { SearchIcon } from '@/components/icons';
import { useEffect, useState } from 'react';

export function AskSmartInvLauncher() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Ask SmartInv"
        className="flex-1 max-w-[620px] flex items-center gap-sm bg-chrome-2 border border-chrome-line rounded-md px-md py-1.5 text-sm text-chrome-cmd hover:border-ai text-left"
      >
        <SearchIcon className="w-3.5 h-3.5 flex-none" />
        <span className="truncate">Ask SmartInv about inventory, health, risk…</span>
        <kbd className="ml-auto font-mono text-[10px] bg-chrome-kbd border border-chrome-line rounded px-1.5 py-px text-chrome-cmd">
          ⌘K
        </kbd>
      </button>

      {open ? (
        <div className="fixed inset-0 z-50 flex justify-end">
          <button
            type="button"
            aria-label="Close Ask SmartInv"
            onClick={() => setOpen(false)}
            className="flex-1 bg-ink/[0.25]"
          />
          <aside className="w-[460px] max-w-full h-full bg-surface border-l border-line flex flex-col">
            <header className="flex items-center gap-2 px-lg h-[54px] border-b border-line flex-none">
              <span className="rounded-pill bg-ai text-white text-[10px] font-bold px-1.5 py-px">
                AI
              </span>
              <h2 className="font-display text-sm text-ink">Ask SmartInv</h2>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="ml-auto text-ink-3 hover:text-ink text-sm"
              >
                Esc
              </button>
            </header>
            <div className="flex-1 min-h-0 p-lg">
              <AnalystChat variant="panel" />
            </div>
          </aside>
        </div>
      ) : null}
    </>
  );
}
