/**
 * Semantic token aliases.
 *
 * These bind raw color tokens to product meaning. They are the named
 * vocabulary the rest of the app should reach for first — never the raw hex,
 * rarely even the raw color name.
 *
 * AGENTS.md non-negotiable #8: violet means AI. The `aiContent` semantic
 * makes that contract explicit; any component rendering AI-produced content
 * pulls from this token.
 */

import { ai, crit, ok, warn } from './colors.js';

export const semantic = {
  /** AI-produced content (recommendations, narratives, generated charts). */
  aiContent: ai.DEFAULT,
  aiContentSoft: ai.soft,

  /** Operational status. Reserved; never used for AI. */
  statusOk: ok.DEFAULT,
  statusOkSoft: ok.soft,
  statusWarn: warn.DEFAULT,
  statusWarnSoft: warn.soft,
  statusCrit: crit.DEFAULT,
  statusCritSoft: crit.soft,
} as const;

export type Semantic = typeof semantic;
