/**
 * Curated starter prompts for Ask SmartInv (CV5.E2.S6).
 *
 * Five prompts spanning the tools the governed analyst can answer today
 * (inventory health + operational risk). Kept as data so the empty-state panel
 * and any future prompt surfaces share one source.
 */

export interface SuggestedPrompt {
  label: string;
  question: string;
}

export const SUGGESTED_PROMPTS: SuggestedPrompt[] = [
  {
    label: 'Portfolio snapshot',
    question: 'Give me an inventory health overview.',
  },
  {
    label: 'Critical spares & downtime',
    question: 'How many critical spares are there and what is the total downtime exposure?',
  },
  {
    label: 'Obsolescence exposure',
    question: 'How many items are at obsolescence risk?',
  },
  {
    label: 'High-risk items',
    question: 'How many items are high or critical risk right now?',
  },
  {
    label: 'Data-quality gaps',
    question: 'How many items have data-quality risks?',
  },
];
