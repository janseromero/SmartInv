/**
 * Pure aggregation helpers for the Executive Overview (CV2 + CV4 + CV6).
 *
 * Kept free of React/Next imports so the roll-up logic is unit-testable in a
 * plain node environment.
 */

import type { ExposureCell } from '@/lib/api';

export interface PlantExposure {
  plant: string;
  exposure: number;
  count: number;
}

/** Roll up per-(plant, risk-class) cells into a per-plant ranking, worst first. */
export function rollUpPlantExposure(cells: ExposureCell[]): PlantExposure[] {
  const byPlant = new Map<string, { exposure: number; count: number }>();
  for (const c of cells) {
    const cur = byPlant.get(c.location_code) ?? { exposure: 0, count: 0 };
    cur.exposure += c.exposure;
    cur.count += c.count;
    byPlant.set(c.location_code, cur);
  }
  return Array.from(byPlant.entries())
    .map(([plant, v]) => ({ plant, ...v }))
    .sort((a, b) => b.exposure - a.exposure);
}

/** Working capital exposed = slow/excess value + dead-stock value. */
export function capitalAtRisk(excessValue: number, deadStockValue: number): number {
  return excessValue + deadStockValue;
}

/** Recommendation capital delta is signed (savings are negative); show magnitude. */
export function opportunityValue(capitalDelta: number): number {
  return Math.abs(capitalDelta);
}
