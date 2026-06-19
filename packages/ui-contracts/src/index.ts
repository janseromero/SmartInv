/**
 * SmartInv UI component contracts (CV1.E8 / ADR-023).
 *
 * TypeScript interfaces only — no rendering. These contracts decouple screens
 * from the concrete implementation, so the web components in @smartinv/ui-web
 * can be re-skinned (or ported to native) without touching consumers.
 */

// --- Button --------------------------------------------------------------

/** `primary` is teal (default action color); `ai` is violet (AI-triggered only). */
export type ButtonVariant = 'default' | 'primary' | 'ai' | 'ghost';
export type ButtonSize = 'md' | 'sm';

/** Presentational props; the component intersects these with native button attrs. */
export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

// --- Badge ---------------------------------------------------------------

export type BadgeVariant = 'neutral' | 'status' | 'ai';
export type BadgeTone = 'ok' | 'warn' | 'crit';

export interface BadgeProps {
  label: string;
  /** `ai` renders violet (reserved for AI content); `status` uses `tone`. */
  variant?: BadgeVariant;
  tone?: BadgeTone;
}

// --- KpiCard -------------------------------------------------------------

export type KpiStatus = 'ok' | 'warn' | 'crit';
export type KpiTrend = 'up' | 'down' | 'flat';

export interface KpiCardProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: string;
  trend?: KpiTrend;
  status?: KpiStatus;
  loading?: boolean;
  dense?: boolean;
}

// --- ConfidenceMeter -----------------------------------------------------

export interface ConfidenceMeterProps {
  /** Confidence in the range 0..1 (clamped). */
  value: number;
  label?: string;
  showBands?: boolean;
}

// --- ApprovalStep --------------------------------------------------------

export type ApprovalState = 'pending' | 'active' | 'approved' | 'rejected';

export interface ApprovalStepProps {
  label: string;
  state: ApprovalState;
  actor?: string;
}

// --- EvidenceStrip -------------------------------------------------------

export interface EvidenceItem {
  metric: string;
  value: string;
  sourceHref?: string;
}

export interface EvidenceStripProps {
  items: EvidenceItem[];
  /** Optional confidence (0..1) rendered as a meter. */
  confidence?: number;
  modelVersion?: string;
  loading?: boolean;
}
