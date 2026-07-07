/**
 * Pure helpers for the Ask SmartInv chat (CV5.E2.S4).
 *
 * Kept free of React so the answer→UI mapping is unit-testable in node. The
 * evidence chips reuse the built `EvidenceStrip` contract (metric/value/href).
 */

import type { AgentAnswer, AgentEvidence } from '@/lib/api';

export interface EvidenceItem {
  metric: string;
  value: string;
  sourceHref?: string;
}

/** Format a governed numeric fact for display (thousands sep; ≤2 decimals). */
export function formatEvidenceValue(value: number): string {
  if (Number.isInteger(value)) {
    return new Intl.NumberFormat('en-US').format(value);
  }
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
}

/** Map an answer's evidence facts to EvidenceStrip items. */
export function toEvidenceItems(evidence: AgentEvidence[]): EvidenceItem[] {
  return evidence.map((e) => ({
    metric: e.label,
    value: formatEvidenceValue(e.value),
    sourceHref: e.source,
  }));
}

/** Short status line shown under an assistant answer. */
export function groundingLabel(answer: AgentAnswer): { text: string; ok: boolean } {
  return answer.grounded
    ? { text: 'Grounded — every figure traces to a governed source', ok: true }
    : { text: 'Withheld — the draft referenced figures that could not be verified', ok: false };
}

/** Turn a non-2xx analyst error status into a user-facing message. */
export function analystErrorMessage(status: number): string {
  if (status === 503) {
    return 'Ask SmartInv is not configured yet (no model API key on the server).';
  }
  if (status === 403) {
    return "You don't have access to the data needed to answer that.";
  }
  return 'Something went wrong answering that. Please try again.';
}
