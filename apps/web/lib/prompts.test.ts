import { SUGGESTED_PROMPTS } from '@/lib/prompts';
import { describe, expect, it } from 'vitest';

describe('SUGGESTED_PROMPTS', () => {
  it('offers five starter prompts (CV5.E2.S6)', () => {
    expect(SUGGESTED_PROMPTS).toHaveLength(5);
  });

  it('each prompt has a label and a non-empty question', () => {
    for (const p of SUGGESTED_PROMPTS) {
      expect(p.label.length).toBeGreaterThan(0);
      expect(p.question.trim().length).toBeGreaterThan(0);
    }
  });
});
