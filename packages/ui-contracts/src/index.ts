/**
 * SmartInv UI component contracts.
 *
 * TypeScript interfaces only — no rendering. These contracts decouple
 * screens from the concrete UI implementation, so we can swap web for
 * native (or evolve the design system) without touching consumers.
 *
 * Real contracts (KpiCard, EvidenceStrip, Badge, ApprovalStep,
 * ConfidenceMeter, ...) are added in task E1.12.
 */

export const UI_CONTRACTS_READY = false as const;
