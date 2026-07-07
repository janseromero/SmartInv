import { AskSmartInvLauncher } from './ask-smartinv-launcher';
import { BellIcon, HelpIcon } from './icons';
import { SessionChip } from './session-chip';

/**
 * Persistent topbar. The command bar is the global "Ask SmartInv" launcher
 * (CV5.E2.S4); notifications become real in CV6.E3 / CV13.E4.
 */
export function Topbar() {
  return (
    <header className="flex items-center gap-lg px-lg bg-chrome border-b border-chrome-line text-chrome-topbar h-[54px]">
      <AskSmartInvLauncher />

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
