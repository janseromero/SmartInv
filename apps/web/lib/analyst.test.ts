import {
  analystErrorMessage,
  formatEvidenceValue,
  groundingLabel,
  toEvidenceItems,
} from '@/lib/analyst';
import type { AgentAnswer } from '@/lib/api';
import { describe, expect, it } from 'vitest';

describe('formatEvidenceValue', () => {
  it('formats integers with thousands separators', () => {
    expect(formatEvidenceValue(1050)).toBe('1,050');
  });
  it('keeps up to two decimals for non-integers', () => {
    expect(formatEvidenceValue(28103013.75)).toBe('28,103,013.75');
  });
});

describe('toEvidenceItems', () => {
  it('maps label/value/source to the EvidenceStrip contract', () => {
    const items = toEvidenceItems([
      { metric: 'critical_spares', label: 'Critical spares', value: 260, source: '/risk' },
    ]);
    expect(items).toEqual([{ metric: 'Critical spares', value: '260', sourceHref: '/risk' }]);
  });
});

describe('groundingLabel', () => {
  const base: AgentAnswer = {
    answer: '',
    grounded: true,
    confidence: 0.9,
    model: 'gpt-4o-mini',
    tool_calls: [],
    evidence: [],
  };
  it('is ok when grounded', () => {
    expect(groundingLabel({ ...base, grounded: true }).ok).toBe(true);
  });
  it('flags withheld when not grounded', () => {
    const label = groundingLabel({ ...base, grounded: false });
    expect(label.ok).toBe(false);
    expect(label.text.toLowerCase()).toContain('withheld');
  });
});

describe('analystErrorMessage', () => {
  it('explains the 503 unconfigured case', () => {
    expect(analystErrorMessage(503).toLowerCase()).toContain('not configured');
  });
  it('has a generic fallback', () => {
    expect(analystErrorMessage(500)).toMatch(/went wrong/i);
  });
});
