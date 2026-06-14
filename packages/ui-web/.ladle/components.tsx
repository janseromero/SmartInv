import type { GlobalProvider } from '@ladle/react';
import './styles.css';

/** Wraps every story in the app surface + spacing so tokens render correctly. */
export const Provider: GlobalProvider = ({ children }) => (
  <div className="bg-surface text-ink font-body p-lg min-h-screen">{children}</div>
);
