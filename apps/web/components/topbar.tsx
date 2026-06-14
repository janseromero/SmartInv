import { BellIcon, HelpIcon, SearchIcon } from './icons';
import { SessionChip } from './session-chip';

/**
 * Persistent topbar with command bar, tenant chip, notification dot, and
 * help button. Command palette becomes interactive in CV8.E2 (UX Polish);
 * notifications become real in CV6.E3 (Audit Trail) / CV13.E4 (Alert Center).
 */
export function Topbar() {
  return (
    <header className="flex items-center gap-lg px-lg bg-chrome border-b border-chrome-line text-chrome-topbar h-[54px]">
      <div className="flex-1 max-w-[620px] flex items-center gap-sm bg-chrome-2 border border-chrome-line rounded-md px-md py-1.5 text-sm text-chrome-cmd">
        <SearchIcon className="w-3.5 h-3.5 flex-none" />
        <span className="truncate">Search items, suppliers, assets — or ask anything…</span>
        <kbd className="ml-auto font-mono text-[10px] bg-chrome-kbd border border-chrome-line rounded px-1.5 py-px text-chrome-cmd">
          ⌘K
        </kbd>
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        <SessionChip />

        <button
          type="button"
          aria-label="Notifications"
          className="w-[34px] h-[34px] rounded-md grid place-items-center text-chrome-ink hover:bg-chrome-2 hover:text-chrome-strong relative"
        >
          <BellIcon className="w-[17px] h-[17px]" />
          <span className="absolute top-[7px] right-[7px] w-[7px] h-[7px] rounded-pill bg-crit border-2 border-chrome" />
        </button>

        <button
          type="button"
          aria-label="Help"
          className="w-[34px] h-[34px] rounded-md grid place-items-center text-chrome-ink hover:bg-chrome-2 hover:text-chrome-strong"
        >
          <HelpIcon className="w-[17px] h-[17px]" />
        </button>
      </div>
    </header>
  );
}
